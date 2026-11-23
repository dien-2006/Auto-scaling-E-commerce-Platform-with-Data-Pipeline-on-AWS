"""Exact mapping of the existing marketplace schema. Never execute DDL from this module."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    FetchedValue,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.compat import LEGACY_SCHEMA


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("(user_role IN ('USER', 'ADMIN'))", name="ck_users_role"),
        CheckConstraint("(user_status IN ('ACTIVE', 'LOCKED'))", name="ck_users_status"),
        CheckConstraint("(BTRIM(email) <> '')", name="ck_users_email_nonblank"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True, nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    user_role: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default=text("'USER'")
    )
    user_status: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default=text("'ACTIVE'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        server_onupdate=FetchedValue(),
    )


class Shop(Base):
    __tablename__ = "shops"
    __table_args__ = (
        ForeignKeyConstraint(
            ["owner_user_id"], ["marketplace.users.user_id"], name="fk_shops_owner"
        ),
        CheckConstraint(
            "(shop_status IN ('PENDING', 'APPROVED', 'REJECTED', 'LOCKED'))", name="ck_shops_status"
        ),
    )

    shop_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True, nullable=False
    )
    owner_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    shop_name: Mapped[str] = mapped_column(String(150), nullable=False)
    shop_slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    shop_status: Mapped[str] = mapped_column(
        String(12), nullable=False, server_default=text("'PENDING'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        server_onupdate=FetchedValue(),
    )


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        ForeignKeyConstraint(
            ["parent_category_id"],
            ["marketplace.categories.category_id"],
            name="fk_categories_parent",
        ),
        CheckConstraint(
            "(parent_category_id IS DISTINCT FROM category_id)", name="ck_categories_no_self_parent"
        ),
    )

    category_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True, nullable=False
    )
    parent_category_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    category_name: Mapped[str] = mapped_column(String(120), nullable=False)
    category_slug: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        ForeignKeyConstraint(["shop_id"], ["marketplace.shops.shop_id"], name="fk_products_shop"),
        ForeignKeyConstraint(
            ["category_id"], ["marketplace.categories.category_id"], name="fk_products_category"
        ),
        UniqueConstraint("shop_id", "sku", name="uq_products_shop_sku"),
        UniqueConstraint("shop_id", "product_id", name="uq_products_shop_product"),
        CheckConstraint("(price >= 0)", name="ck_products_price"),
    )

    product_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True, nullable=False
    )
    shop_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        server_onupdate=FetchedValue(),
    )


class ProductImage(Base):
    __tablename__ = "product_images"
    __table_args__ = (
        ForeignKeyConstraint(
            ["product_id"],
            ["marketplace.products.product_id"],
            name="fk_product_images_product",
            ondelete="CASCADE",
        ),
        CheckConstraint("(sort_order >= 0)", name="ck_product_images_sort_order"),
        CheckConstraint("(BTRIM(image_key) <> '')", name="ck_product_images_key_nonblank"),
        UniqueConstraint("product_id", "image_key", name="uq_product_images_key"),
    )

    product_image_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True, nullable=False
    )
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    image_key: Mapped[str] = mapped_column(Text, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        ForeignKeyConstraint(
            ["product_id"], ["marketplace.products.product_id"], name="fk_inventory_product"
        ),
        CheckConstraint("(quantity >= 0)", name="ck_inventory_quantity"),
    )

    product_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        server_onupdate=FetchedValue(),
    )


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = (
        ForeignKeyConstraint(["user_id"], ["marketplace.users.user_id"], name="fk_addresses_user"),
    )

    address_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    address_line: Mapped[str] = mapped_column(Text, nullable=False)
    ward: Mapped[str | None] = mapped_column(String(120), nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )


class Cart(Base):
    __tablename__ = "carts"
    __table_args__ = (
        ForeignKeyConstraint(["user_id"], ["marketplace.users.user_id"], name="fk_carts_user"),
    )

    cart_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        server_onupdate=FetchedValue(),
    )


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        ForeignKeyConstraint(
            ["cart_id"],
            ["marketplace.carts.cart_id"],
            name="fk_cart_items_cart",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["product_id"], ["marketplace.products.product_id"], name="fk_cart_items_product"
        ),
        UniqueConstraint("cart_id", "product_id", name="uq_cart_items_cart_product"),
        CheckConstraint("(quantity > 0)", name="ck_cart_items_quantity"),
    )

    cart_item_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True, nullable=False
    )
    cart_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        ForeignKeyConstraint(
            ["buyer_user_id"], ["marketplace.users.user_id"], name="fk_orders_buyer"
        ),
        UniqueConstraint("buyer_user_id", "idempotency_key", name="uq_orders_buyer_idempotency"),
        CheckConstraint("(total_amount >= 0)", name="ck_orders_total"),
        CheckConstraint(
            "(payment_method IN ('COD', 'BANK_TRANSFER', 'VNPAY', 'MOMO'))",
            name="ck_orders_payment",
        ),
        CheckConstraint("(discount_amount >= 0)", name="ck_orders_discount"),
        CheckConstraint("(shipping_fee >= 0)", name="ck_orders_shipping_fee"),
        *(
            ()
            if LEGACY_SCHEMA
            else (
                CheckConstraint(
                    "(shipping_discount_amount >= 0)", name="ck_orders_shipping_discount"
                ),
            )
        ),
    )

    order_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True, nullable=False
    )
    buyer_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    idempotency_key: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    shipping_address: Mapped[str] = mapped_column(Text, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    shipping_fee: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default=text("0")
    )
    payment_method: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'COD'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    if not LEGACY_SCHEMA:
        shipping_discount_amount: Mapped[Decimal] = mapped_column(
            Numeric(14, 2), nullable=False, server_default=text("0")
        )


class ShopOrder(Base):
    __tablename__ = "shop_orders"
    __table_args__ = (
        ForeignKeyConstraint(
            ["order_id"], ["marketplace.orders.order_id"], name="fk_shop_orders_order"
        ),
        ForeignKeyConstraint(
            ["shop_id"], ["marketplace.shops.shop_id"], name="fk_shop_orders_shop"
        ),
        UniqueConstraint("order_id", "shop_id", name="uq_shop_orders_order_shop"),
        UniqueConstraint("shop_order_id", "shop_id", name="uq_shop_orders_id_shop"),
        CheckConstraint(
            "(order_status IN ('PENDING', 'CONFIRMED', 'SHIPPING', 'COMPLETED', 'CANCELLED'))",
            name="ck_shop_orders_status",
        ),
        CheckConstraint("(subtotal >= 0)", name="ck_shop_orders_subtotal"),
    )

    shop_order_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True, nullable=False
    )
    order_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    shop_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    order_status: Mapped[str] = mapped_column(
        String(12), nullable=False, server_default=text("'PENDING'")
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        server_onupdate=FetchedValue(),
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        ForeignKeyConstraint(
            ["shop_order_id", "shop_id"],
            ["marketplace.shop_orders.shop_order_id", "marketplace.shop_orders.shop_id"],
            name="fk_order_items_shop_order",
        ),
        ForeignKeyConstraint(
            ["shop_id", "product_id"],
            ["marketplace.products.shop_id", "marketplace.products.product_id"],
            name="fk_order_items_shop_product",
        ),
        CheckConstraint("(unit_price >= 0)", name="ck_order_items_price"),
        CheckConstraint("(quantity > 0)", name="ck_order_items_quantity"),
        UniqueConstraint("shop_order_id", "product_id", name="uq_order_items_shop_order_product"),
    )

    order_item_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True, nullable=False
    )
    shop_order_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    shop_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)


User.__table__.append_constraint(Index("uq_users_email_lower", text("LOWER(email)"), unique=True))

ProductImage.__table__.append_constraint(
    Index(
        "uq_product_images_primary",
        ProductImage.product_id,
        unique=True,
        postgresql_where=text("is_primary = TRUE"),
    )
)

Address.__table__.append_constraint(
    Index(
        "uq_addresses_default_per_user",
        Address.user_id,
        unique=True,
        postgresql_where=text("is_default = TRUE"),
    )
)

Category.__table__.append_constraint(
    Index("idx_categories_parent", Category.parent_category_id, unique=False)
)

Product.__table__.append_constraint(
    Index("idx_products_category", Product.category_id, unique=False)
)

Product.__table__.append_constraint(
    Index("idx_products_shop_active", Product.shop_id, Product.is_active, unique=False)
)

ProductImage.__table__.append_constraint(
    Index(
        "idx_product_images_sort",
        ProductImage.product_id,
        ProductImage.sort_order,
        ProductImage.product_image_id,
        unique=False,
    )
)

Address.__table__.append_constraint(Index("idx_addresses_user", Address.user_id, unique=False))

CartItem.__table__.append_constraint(
    Index("idx_cart_items_product", CartItem.product_id, unique=False)
)

Order.__table__.append_constraint(
    Index("idx_orders_buyer_created", Order.buyer_user_id, text("created_at DESC"), unique=False)
)

ShopOrder.__table__.append_constraint(
    Index("idx_shop_orders_shop_status", ShopOrder.shop_id, ShopOrder.order_status, unique=False)
)

OrderItem.__table__.append_constraint(
    Index("idx_order_items_shop_product", OrderItem.shop_id, OrderItem.product_id, unique=False)
)
