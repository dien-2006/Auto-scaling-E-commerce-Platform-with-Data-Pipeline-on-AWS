from fastapi import APIRouter

from app.api.v1.routers.addresses import router as addresses_router
from app.api.v1.routers.admin_categories import router as admin_categories_router
from app.api.v1.routers.admin_products import router as admin_products_router
from app.api.v1.routers.admin_shops import router as admin_shops_router
from app.api.v1.routers.admin_users import router as admin_users_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.cart import router as cart_router
from app.api.v1.routers.catalog import router as catalog_router
from app.api.v1.routers.checkout import router as checkout_router
from app.api.v1.routers.inventory import router as inventory_router
from app.api.v1.routers.orders import router as orders_router
from app.api.v1.routers.otp import router as otp_router
from app.api.v1.routers.product_images import router as product_images_router
from app.api.v1.routers.products import router as products_router
from app.api.v1.routers.seller_orders import router as seller_orders_router
from app.api.v1.routers.seller_products import router as seller_products_router
from app.api.v1.routers.seller_shop import router as seller_shop_router
from app.api.v1.routers.shopping import router as shopping_router

router = APIRouter(prefix="/api/v1")
router.include_router(admin_categories_router)
router.include_router(admin_products_router)
router.include_router(admin_users_router)
router.include_router(admin_shops_router)
router.include_router(auth_router)
router.include_router(seller_shop_router)
router.include_router(seller_products_router)
router.include_router(inventory_router)
router.include_router(seller_orders_router)
router.include_router(product_images_router)
router.include_router(cart_router)
router.include_router(checkout_router)
router.include_router(orders_router)
router.include_router(addresses_router)
router.include_router(catalog_router)
router.include_router(products_router)
router.include_router(shopping_router)


router.include_router(otp_router)
