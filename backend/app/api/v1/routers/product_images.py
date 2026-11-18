from fastapi import APIRouter, Response

from app.api.dependencies import WriteAccess
from app.schemas.product_images import (
    ImageCreate,
    ImagePatch,
    ImageResponse,
    ImageUpload,
    UploadResponse,
)
from app.schemas.products import PositiveID
from app.services.product_images import ProductImageService
from app.services.storage import Storage

router = APIRouter(prefix="/seller/products/{product_id}/images", tags=["Seller images"])


@router.post("/upload-url", response_model=UploadResponse)
def upload_url(
    product_id: PositiveID,
    payload: ImageUpload,
    access: WriteAccess,
    storage: Storage,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return ProductImageService(access, storage, product_id).upload(payload)


@router.post("", response_model=ImageResponse, status_code=201)
def create_image(
    product_id: PositiveID,
    payload: ImageCreate,
    access: WriteAccess,
    storage: Storage,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return ImageResponse(data=ProductImageService(access, storage, product_id).create(payload))


@router.patch("/{image_id}", response_model=ImageResponse)
def patch_image(
    product_id: PositiveID,
    image_id: PositiveID,
    payload: ImagePatch,
    access: WriteAccess,
    storage: Storage,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return ImageResponse(
        data=ProductImageService(access, storage, product_id).patch(image_id, payload)
    )


@router.delete("/{image_id}", status_code=204)
def delete_image(
    product_id: PositiveID, image_id: PositiveID, access: WriteAccess, storage: Storage
):
    ProductImageService(access, storage, product_id).delete(image_id)
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
