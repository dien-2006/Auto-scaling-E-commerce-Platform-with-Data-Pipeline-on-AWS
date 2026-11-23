from fastapi import APIRouter, Response

from app.api.dependencies import ReadAccess, WriteAccess
from app.schemas.admin_categories import CategoryCreate, CategoryPatch, CategoryResponse
from app.schemas.catalog import CategoryList
from app.schemas.products import PositiveID
from app.services.admin_categories import AdminCategoryService

router = APIRouter(prefix="/admin/categories", tags=["Admin categories"])


@router.get("", response_model=CategoryList)
def categories(access: ReadAccess, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return AdminCategoryService(access).list()


@router.post("", response_model=CategoryResponse, status_code=201)
def create(payload: CategoryCreate, access: WriteAccess, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return CategoryResponse(data=AdminCategoryService(access).write(payload))


@router.patch("/{category_id}", response_model=CategoryResponse)
def patch(category_id: PositiveID, payload: CategoryPatch, access: WriteAccess, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return CategoryResponse(data=AdminCategoryService(access).write(payload, category_id))
