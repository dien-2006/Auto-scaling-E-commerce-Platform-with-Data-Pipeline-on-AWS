"""S3 staging uploads and immutable verified images. Never creates buckets or deletes objects."""

import hashlib
import hmac
import io
import re
import warnings
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

import boto3
import jwt
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import Depends, Request
from PIL import Image, UnidentifiedImageError

from app.core.config import Settings
from app.core.errors import APIError
from app.core.image_limits import MAX_IMAGE_BYTES

TYPES = {"image/jpeg": ("jpg", "JPEG"), "image/png": ("png", "PNG"), "image/webp": ("webp", "WEBP")}
FINAL_KEY = re.compile(
    r"^product-images/([1-9]\d{0,18})/([1-9]\d{0,18})/([0-9a-f]{32})\.(jpg|png|webp)$"
)
# Read-only compatibility for the existing imported catalog; never accepted by finalize().
CATALOG_SHOPS = r"(?:1-Lumi Beauty|2-Miora Lifestyle|3-Nuvia Care Store)"
LEGACY_KEY = re.compile(
    rf"(?:{CATALOG_SHOPS}/product_image|ProductImages/{CATALOG_SHOPS})/"
    r"([1-9][0-9]{0,18})/\1_[1-9][0-9]{0,5}\.jpg"
)
LEGACY_LOGO_KEY = re.compile(r"^logo/[1-9][0-9]{0,18}\.png$")
SHOP_LOGO_KEY = re.compile(r"^shop-logos/[1-9][0-9]{0,18}/[0-9a-f]{32}\.(jpg|png|webp)$")


def invalid_image():
    return APIError(
        422, "INVALID_IMAGE", "Ảnh không hợp lệ, đã hết hạn hoặc không đúng nội dung đã khai báo"
    )


class ObjectStorage:
    def __init__(self, settings: Settings, client=None):
        self.settings = settings
        self._client = client

    @property
    def client(self):
        if not self.settings.s3_bucket:
            raise APIError(503, "STORAGE_NOT_CONFIGURED", "Chưa cấu hình kho ảnh S3")
        if self._client is None:
            try:
                self._client = boto3.client(
                    "s3",
                    region_name=self.settings.s3_region,
                    endpoint_url=str(self.settings.s3_endpoint_url)
                    if self.settings.s3_endpoint_url
                    else None,
                    config=Config(
                        signature_version="s3v4",
                        connect_timeout=3,
                        read_timeout=5,
                        retries={"max_attempts": 1},
                        s3={
                            "addressing_style": "path" if self.settings.s3_path_style else "virtual"
                        },
                    ),
                )
            except (BotoCoreError, ValueError) as exc:
                raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Kho ảnh chưa sẵn sàng") from exc
        return self._client

    def call(self, operation, **kwargs):
        try:
            return getattr(self.client, operation)(**kwargs)
        except (BotoCoreError, ClientError) as exc:
            raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Kho ảnh chưa sẵn sàng") from exc

    def signing_key(self):
        if not self.settings.jwt_secret:
            raise APIError(503, "STORAGE_NOT_CONFIGURED", "Chưa cấu hình xác thực kho ảnh")
        return hmac.new(
            self.settings.jwt_secret.get_secret_value().encode(),
            b"marketplace-upload-v1",
            hashlib.sha256,
        ).digest()

    def issue(self, shop_id: int, product_id: int, content_type: str, size: int):
        if content_type not in TYPES or type(size) is not int or not 1 <= size <= MAX_IMAGE_BYTES:
            raise invalid_image()
        key = f"uploads/{shop_id}/{product_id}/{uuid4().hex}.{TYPES[content_type][0]}"
        now = int(datetime.now(UTC).timestamp())
        grant = jwt.encode(
            {
                "iss": "marketplace-upload",
                "aud": "image-finalize",
                "iat": now,
                "exp": now + 300,
                "key": key,
                "size": size,
                "type": content_type,
            },
            self.signing_key(),
            algorithm="HS256",
        )
        fields = {"Content-Type": content_type, "x-amz-meta-grant": grant}
        result = self.call(
            "generate_presigned_post",
            Bucket=self.settings.s3_bucket,
            Key=key,
            Fields=fields,
            Conditions=[
                {"Content-Type": content_type},
                {"x-amz-meta-grant": grant},
                ["content-length-range", size, size],
            ],
            ExpiresIn=300,
        )
        return {
            "upload_url": result["url"],
            "fields": result["fields"],
            "image_key": key,
            "expires_at": datetime.fromtimestamp(now + 300, UTC),
        }

    @staticmethod
    def final_key(key: str, shop_id: int, product_id: int):
        prefix = f"uploads/{shop_id}/{product_id}/"
        if not key.startswith(prefix) or not re.fullmatch(
            r"[0-9a-f]{32}\.(jpg|png|webp)", key[len(prefix) :]
        ):
            raise invalid_image()
        return "product-images/" + key[len("uploads/") :]

    def finalize(self, key: str, shop_id: int, product_id: int) -> str:
        final = self.final_key(key, shop_id, product_id)
        head = self.call("head_object", Bucket=self.settings.s3_bucket, Key=key)
        try:
            grant = jwt.decode(
                head.get("Metadata", {}).get("grant", ""),
                self.signing_key(),
                algorithms=["HS256"],
                issuer="marketplace-upload",
                audience="image-finalize",
                options={"require": ["exp", "iat", "key", "size", "type"]},
            )
        except jwt.InvalidTokenError as exc:
            raise invalid_image() from exc
        kind, size = grant["type"], grant["size"]
        if (
            grant["key"] != key
            or kind not in TYPES
            or type(size) is not int
            or not 1 <= size <= MAX_IMAGE_BYTES
            or head.get("ContentLength") != size
            or head.get("ContentType") != kind
        ):
            raise invalid_image()
        source = self.call(
            "get_object", Bucket=self.settings.s3_bucket, Key=key, IfMatch=head["ETag"]
        )
        try:
            data = source["Body"].read(MAX_IMAGE_BYTES + 1)
        except (BotoCoreError, OSError) as exc:
            raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Chưa đọc được ảnh") from exc
        finally:
            source["Body"].close()
        if len(data) != size:
            raise invalid_image()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(data), formats=[TYPES[kind][1]]) as image:
                    if (
                        image.format != TYPES[kind][1]
                        or max(image.size) > 4096
                        or image.width * image.height > 16000000
                        or getattr(image, "is_animated", False)
                    ):
                        raise invalid_image()
                    image.verify()
                with Image.open(io.BytesIO(data), formats=[TYPES[kind][1]]) as image:
                    image.load()
        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ) as exc:
            raise invalid_image() from exc
        digest = hashlib.sha256(data).hexdigest()
        try:
            self.client.put_object(
                Bucket=self.settings.s3_bucket,
                Key=final,
                Body=data,
                ContentType=kind,
                ContentDisposition="inline",
                Metadata={"sha256": digest},
                IfNoneMatch="*",
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") not in {"PreconditionFailed", "412"}:
                raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Chưa lưu được ảnh") from exc
            existing = self.call("head_object", Bucket=self.settings.s3_bucket, Key=final)
            if existing.get("Metadata", {}).get("sha256") != digest:
                raise APIError(
                    409, "IMAGE_CONFLICT", "Ảnh đã thay đổi, hãy tải lại ảnh mới"
                ) from exc
        except BotoCoreError as exc:
            raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Chưa lưu được ảnh") from exc
        return final

    def url(self, key: str | None) -> str | None:
        if not key or not self.settings.s3_bucket:
            return None
        verified = FINAL_KEY.fullmatch(key)
        if not verified and not LEGACY_KEY.fullmatch(key):
            return None
        if verified and self.settings.s3_public_base_url:
            return str(self.settings.s3_public_base_url).rstrip("/") + "/" + key
        return self.call(
            "generate_presigned_url",
            ClientMethod="get_object",
            Params={"Bucket": self.settings.s3_bucket, "Key": key},
            ExpiresIn=900,
        )

    def logo_url(self, key: str | None) -> str | None:
        """Read existing logo references without rewriting keys or database rows."""
        if not key or not self.settings.s3_bucket:
            return None
        modern = SHOP_LOGO_KEY.fullmatch(key)
        if not modern and not LEGACY_LOGO_KEY.fullmatch(key):
            return None
        if modern and self.settings.s3_public_base_url:
            return str(self.settings.s3_public_base_url).rstrip("/") + "/" + key
        return self.call(
            "generate_presigned_url",
            ClientMethod="get_object",
            Params={"Bucket": self.settings.s3_bucket, "Key": key},
            ExpiresIn=900,
        )


def get_storage(request: Request) -> ObjectStorage:
    return ObjectStorage(request.app.state.settings)


Storage = Annotated[ObjectStorage, Depends(get_storage)]
