import hashlib
import io
import secrets
from datetime import UTC, datetime
from urllib.parse import unquote, urlsplit

import boto3
import jwt
import pytest
from botocore.exceptions import ClientError
from PIL import Image
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import APIError
from app.schemas.product_images import ImagePatch, ImageUpload
from app.services.storage import MAX_IMAGE_BYTES, ObjectStorage


class MemoryS3:
    """Deterministic contract double; never a substitute for real bucket/CORS tests."""

    def __init__(self):
        self.objects = {}
        self.calls = []

    def generate_presigned_post(self, **kwargs):
        self.calls.append(("post", kwargs))
        return {
            "url": "https://storage.invalid/upload",
            "fields": {"key": kwargs["Key"], **kwargs["Fields"]},
        }

    def generate_presigned_url(self, **kwargs):
        return f"https://storage.invalid/{kwargs['Params']['Key']}?signed=test"

    def head_object(self, **kwargs):
        row = self.objects[kwargs["Key"]]
        return {k: v for k, v in row.items() if k != "data"}

    def get_object(self, **kwargs):
        row = self.objects[kwargs["Key"]]
        assert kwargs["IfMatch"] == row["ETag"]
        return {"Body": io.BytesIO(row["data"])}

    def put_object(self, **kwargs):
        self.calls.append(("put", kwargs))
        assert kwargs["IfNoneMatch"] == "*"
        if kwargs["Key"] in self.objects:
            raise ClientError({"Error": {"Code": "PreconditionFailed"}}, "PutObject")
        data = kwargs["Body"]
        self.objects[kwargs["Key"]] = {
            "data": data,
            "Metadata": kwargs["Metadata"],
            "ContentType": kwargs["ContentType"],
            "ContentLength": len(data),
            "ETag": hashlib.sha256(data).hexdigest(),
        }


def png(color="blue", size=(4, 4)):
    out = io.BytesIO()
    Image.new("RGB", size, color).save(out, format="PNG")
    return out.getvalue()


def configured():
    return Settings(
        environment="test",
        public_origin="http://testserver",
        jwt_secret=secrets.token_urlsafe(48),
        s3_bucket="marketplace-test-only",
    )


def test_existing_logo_is_signed_without_mutation_or_cdn_rewrite():
    settings = configured()
    settings.s3_public_base_url = "https://cdn.example"
    client = MemoryS3()
    storage = ObjectStorage(settings, client)
    assert storage.logo_url("logo/1.png") == "https://storage.invalid/logo/1.png?signed=test"
    assert storage.logo_url("shop-logos/1/" + "a" * 32 + ".png") == (
        "https://cdn.example/shop-logos/1/" + "a" * 32 + ".png"
    )
    for key in ("../logo/1.png", "logo/1.svg", "logo/1.png?x=1", "https://evil/logo/1.png"):
        assert storage.logo_url(key) is None
    assert client.objects == {}
    assert client.calls == []


def stage(storage, client, shop=1, product=2, data=None, mime="image/png"):
    data = data if data is not None else png()
    grant = storage.issue(shop, product, mime, len(data))
    client.objects[grant["image_key"]] = {
        "data": data,
        "Metadata": {"grant": grant["fields"]["x-amz-meta-grant"]},
        "ContentType": mime,
        "ContentLength": len(data),
        "ETag": hashlib.sha256(data).hexdigest(),
    }
    return grant["image_key"]


def test_presigned_policy_exact_key_type_size_and_expiry_without_network():
    settings = configured()
    client = boto3.client(
        "s3",
        region_name=settings.s3_region,
        aws_access_key_id="test-only",
        aws_secret_access_key="test-only",
    )
    storage = ObjectStorage(settings, client)
    grant = storage.issue(9007199254740993, 9007199254740994, "image/png", 1234)
    import base64
    import json

    policy = json.loads(base64.b64decode(grant["fields"]["policy"]))
    assert ["content-length-range", 1234, 1234] in policy["conditions"]
    assert {"Content-Type": "image/png"} in policy["conditions"]
    assert {"key": grant["image_key"]} in policy["conditions"]
    assert "9007199254740993/9007199254740994/" in grant["image_key"]
    assert 280 < (grant["expires_at"] - datetime.now(UTC)).total_seconds() <= 300


@pytest.mark.parametrize(
    "format,mime", [("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp")]
)
def test_supported_decoders_publish_unchanged_bytes(format, mime):
    output = io.BytesIO()
    Image.new("RGB", (8, 8), "blue").save(output, format=format)
    data = output.getvalue()
    client = MemoryS3()
    storage = ObjectStorage(configured(), client)
    key = stage(storage, client, data=data, mime=mime)
    final = storage.finalize(key, 1, 2)
    assert client.objects[final]["data"] == data


def test_unsupported_decoder_is_not_attempted_even_with_png_metadata():
    output = io.BytesIO()
    Image.new("RGB", (8, 8)).save(output, format="TIFF")
    client = MemoryS3()
    storage = ObjectStorage(configured(), client)
    key = stage(storage, client, data=output.getvalue())
    with pytest.raises(APIError) as error:
        storage.finalize(key, 1, 2)
    assert error.value.code == "INVALID_IMAGE"
    assert not any(call[0] == "put" for call in client.calls)


def test_verified_immutable_final_object_and_delivery():
    client = MemoryS3()
    storage = ObjectStorage(configured(), client)
    key = stage(storage, client)
    final = storage.finalize(key, 1, 2)
    assert final.startswith("product-images/1/2/") and final != key
    assert client.objects[final]["data"] == png()
    assert storage.finalize(key, 1, 2) == final
    assert storage.url(final).startswith("https://storage.invalid/product-images/")
    assert storage.url(key) is None and storage.url("private/credentials") is None


@pytest.mark.parametrize("change", ["mime", "size", "grant", "expired", "bytes"])
def test_rejects_invalid_object_before_publishing(change):
    client = MemoryS3()
    storage = ObjectStorage(configured(), client)
    key = stage(storage, client, data=b"not an image" if change == "bytes" else None)
    row = client.objects[key]
    if change == "mime":
        row["ContentType"] = "text/html"
    if change == "size":
        row["ContentLength"] += 1
    if change == "grant":
        row["Metadata"]["grant"] = "forged"
    if change == "expired":
        payload = jwt.decode(
            row["Metadata"]["grant"],
            storage.signing_key(),
            algorithms=["HS256"],
            audience="image-finalize",
        )
        payload["exp"] = 1
        row["Metadata"]["grant"] = jwt.encode(payload, storage.signing_key(), algorithm="HS256")
    with pytest.raises(APIError) as error:
        storage.finalize(key, 1, 2)
    assert error.value.code == "INVALID_IMAGE"
    assert not any(operation == "put" for operation, _ in client.calls)


def test_cross_shop_product_and_path_traversal_fail_before_storage():
    storage = ObjectStorage(configured(), MemoryS3())
    for key in [
        "uploads/2/2/" + "a" * 32 + ".png",
        "uploads/1/3/" + "a" * 32 + ".png",
        "uploads/1/2/../secret",
        "https://evil.invalid/p.png",
    ]:
        with pytest.raises(APIError):
            storage.finalize(key, 1, 2)


def test_not_configured_no_credential_discovery_or_network(monkeypatch):
    monkeypatch.setattr(boto3, "client", lambda *a, **k: pytest.fail("must not create SDK client"))
    storage = ObjectStorage(Settings(environment="test"))
    assert storage.url("product-images/1/2/" + "a" * 32 + ".png") is None
    with pytest.raises(APIError) as e:
        _ = storage.client
    assert e.value.code == "STORAGE_NOT_CONFIGURED"


@pytest.mark.parametrize(
    "data",
    [
        {"content_type": "image/svg+xml", "size_bytes": 10},
        {"content_type": "image/png", "size_bytes": MAX_IMAGE_BYTES + 1},
        {"content_type": "image/png", "size_bytes": True},
    ],
)
def test_upload_validation(data):
    with pytest.raises(ValidationError):
        ImageUpload(**data)


@pytest.mark.parametrize(
    "data",
    [{}, {"image_key": "other"}, {"sort_order": -1}, {"sort_order": None}, {"is_primary": "true"}],
)
def test_patch_validation(data):
    with pytest.raises(ValidationError):
        ImagePatch(**data)


@pytest.mark.parametrize(
    "changes",
    [
        {"s3_bucket": "../bad"},
        {"s3_bucket": "valid-bucket", "s3_endpoint_url": "http://storage.invalid"},
        {"s3_bucket": "valid-bucket", "s3_public_base_url": "https://x.invalid?secret=key"},
        {"s3_endpoint_url": "https://x.invalid"},
    ],
)
def test_storage_configuration_validation(changes):
    with pytest.raises(ValidationError):
        Settings(environment="test", **changes)


@pytest.mark.parametrize("prefix", ["1-Lumi Beauty", "2-Miora Lifestyle", "3-Nuvia Care Store"])
@pytest.mark.parametrize("layout", ["original", "ProductImages"])
def test_legacy_catalog_delivery_signs_exact_key_without_allowing_upload(prefix, layout):
    client = boto3.client(
        "s3",
        region_name="ap-southeast-1",
        aws_access_key_id="test-only",
        aws_secret_access_key="test-only",
    )
    settings = configured().model_copy(update={"s3_public_base_url": "https://cdn.invalid"})
    storage = ObjectStorage(settings, client)
    directory = f"{prefix}/product_image" if layout == "original" else f"ProductImages/{prefix}"
    key = f"{directory}/297/297_1.jpg"
    url = storage.url(key)
    assert unquote(urlsplit(url).path).endswith("/" + key)
    assert "X-Amz-Signature=" in url or "Signature=" in url
    assert "cdn.invalid" not in url
    with pytest.raises(APIError):
        storage.final_key(key, 1, 297)


@pytest.mark.parametrize(
    "key",
    [
        "1-Lumi+Beauty/product_image/1/1_1.jpg",
        "1-Lumi Beauty/product_image/1/2_1.jpg",
        "1-Lumi Beauty/product_image/1/../secret.jpg",
        "1-Lumi Beauty/product_image/1/1_1.svg",
        "1-Lumi Beauty/product_image/01/01_1.jpg",
        "1-Lumi Beauty/product_image/1/1_1.jpg?query=1",
        "1-Lumi Beauty/product_image/1/1_1.jpg\n",
        "4-Unknown/product_image/1/1_1.jpg",
        "uploads/1/1/" + "a" * 32 + ".jpg",
        "https://evil.invalid/image.jpg",
        "ProductImages/1-Lumi Beauty/1/2_1.jpg",
        "ProductImages/1-Lumi Beauty/1/../secret.jpg",
        "ProductImages/1-Lumi Beauty/1/1_1.svg",
        "ProductImages/1-Lumi Beauty/1/1_1.jpg?query=1",
        "ProductImages/4-Unknown/1/1_1.jpg",
        "ProductImages/1-Lumi+Beauty/1/1_1.jpg",
        "ProductImages/1-Lumi Beauty/1/1_1.jpg\n",
        "productimages/1-Lumi Beauty/1/1_1.jpg",
    ],
)
def test_legacy_delivery_rejects_other_paths_without_sdk(key):
    assert ObjectStorage(configured(), object()).url(key) is None
