
"""Metadata for the thirteen extension tables; mapping never executes DDL.

No coupon/payment/review/ETL API is enabled by registering these tables.
"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base
from app.models.compat import LEGACY_SCHEMA


def identity(name):
    return Column(name, BigInteger, Identity(always=True), primary_key=True, nullable=False)


def reference(table, column, target, *, nullable=False, unique=False, ondelete=None):
    return Column(
        column,
        BigInteger,
        ForeignKey("marketplace." + target, name=f"{table}_{column}_fkey", ondelete=ondelete),
        nullable=nullable,
        unique=unique,
    )


def timestamp(name):
    return Column(name, DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


audit_logs = Table(
    "audit_logs",
    Base.metadata,
    identity("audit_id"),
    reference("audit_logs", "actor_user_id", "users.user_id", nullable=True, ondelete="SET NULL"),
    Column("action", String(10), nullable=False),
    Column("table_name", String(100), nullable=False),
    Column("record_id", BigInteger, nullable=False),
    timestamp("changed_at"),
    CheckConstraint("action IN ('INSERT', 'UPDATE', 'DELETE')", name="audit_logs_action_check"),
)
audit_log_changes = Table(
    "audit_log_changes",
    Base.metadata,
    identity("change_id"),
    reference("audit_log_changes", "audit_id", "audit_logs.audit_id", ondelete="CASCADE"),
    Column("column_name", String(100), nullable=False),
    Column("old_value", JSONB),
    Column("new_value", JSONB),
)
product_price_history = Table(
    "product_price_history",
    Base.metadata,
    identity("price_history_id"),
    reference("product_price_history", "product_id", "products.product_id"),
    Column("old_price", Numeric(14, 2), nullable=False),
    Column("new_price", Numeric(14, 2), nullable=False),
    reference(
        "product_price_history", "changed_by", "users.user_id", nullable=True, ondelete="SET NULL"
    ),
    timestamp("changed_at"),
    CheckConstraint("old_price >= 0", name="product_price_history_old_price_check"),
    CheckConstraint("new_price >= 0", name="product_price_history_new_price_check"),
    CheckConstraint("old_price <> new_price", name="ck_price_changed"),
)
inventory_movements = Table(
    "inventory_movements",
    Base.metadata,
    identity("movement_id"),
    reference("inventory_movements", "product_id", "products.product_id"),
    Column("movement_type", String(20), nullable=False),
    Column("quantity_change", Integer, nullable=False),
    Column("quantity_before", Integer, nullable=False),
    Column("quantity_after", Integer, nullable=False),
    reference("inventory_movements", "order_id", "orders.order_id", nullable=True),
    reference(
        "inventory_movements", "created_by", "users.user_id", nullable=True, ondelete="SET NULL"
    ),
    timestamp("created_at"),
    CheckConstraint(
        "movement_type IN ('IMPORT', 'SALE', 'RETURN', 'ADJUSTMENT')",
        name="inventory_movements_movement_type_check",
    ),
    CheckConstraint("quantity_change <> 0", name="inventory_movements_quantity_change_check"),
    CheckConstraint("quantity_before >= 0", name="inventory_movements_quantity_before_check"),
    CheckConstraint("quantity_after >= 0", name="inventory_movements_quantity_after_check"),
    CheckConstraint(
        "quantity_after = quantity_before + quantity_change", name="ck_inventory_movement_balance"
    ),
)
shop_order_status_history = Table(
    "shop_order_status_history",
    Base.metadata,
    identity("history_id"),
    reference("shop_order_status_history", "shop_order_id", "shop_orders.shop_order_id"),
    Column("old_status", String(12)),
    Column("new_status", String(12), nullable=False),
    reference(
        "shop_order_status_history",
        "changed_by",
        "users.user_id",
        nullable=True,
        ondelete="SET NULL",
    ),
    timestamp("changed_at"),
    CheckConstraint(
        "old_status IS NULL OR old_status IN "
        "('PENDING','CONFIRMED','SHIPPING','COMPLETED','CANCELLED')",
        name="ck_order_history_old",
    ),
    CheckConstraint(
        "new_status IN ('PENDING','CONFIRMED','SHIPPING','COMPLETED','CANCELLED')",
        name="ck_order_history_new",
    ),
)
shop_approval_history = Table(
    "shop_approval_history",
    Base.metadata,
    identity("approval_id"),
    reference("shop_approval_history", "shop_id", "shops.shop_id"),
    reference("shop_approval_history", "admin_user_id", "users.user_id"),
    Column("old_status", String(12)),
    Column("new_status", String(12), nullable=False),
    Column("reason", Text),
    timestamp("created_at"),
    CheckConstraint(
        "old_status IS NULL OR old_status IN ('PENDING','APPROVED','REJECTED','LOCKED')",
        name="ck_approval_old",
    ),
    CheckConstraint(
        "new_status IN ('PENDING','APPROVED','REJECTED','LOCKED')", name="ck_approval_new"
    ),
)
coupons = Table(
    "coupons",
    Base.metadata,
    identity("coupon_id"),
    reference("coupons", "shop_id", "shops.shop_id", nullable=True),
    Column("code", String(50), nullable=False, unique=True),
    Column("discount_percent", Numeric(5, 2), nullable=False),
    Column("min_order_amount", Numeric(14, 2), nullable=False, server_default=text("0")),
    Column("usage_limit", Integer, nullable=False),
    Column("used_count", Integer, nullable=False, server_default=text("0")),
    Column("starts_at", DateTime(timezone=True), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("is_active", Boolean, nullable=False, server_default=text("TRUE")),
    timestamp("created_at"),
    *(
        []
        if LEGACY_SCHEMA
        else [Column("coupon_type", String(20), nullable=False, server_default=text("'GOODS'"))]
    ),
    CheckConstraint(
        "discount_percent > 0 AND discount_percent <= 100", name="coupons_discount_percent_check"
    ),
    CheckConstraint("min_order_amount >= 0", name="coupons_min_order_amount_check"),
    CheckConstraint("usage_limit > 0", name="coupons_usage_limit_check"),
    CheckConstraint("used_count >= 0", name="coupons_used_count_check"),
    CheckConstraint("expires_at > starts_at", name="ck_coupon_dates"),
    CheckConstraint("used_count <= usage_limit", name="ck_coupon_used_count"),
    CheckConstraint("BTRIM(code) <> ''", name="ck_coupon_code_nonblank"),
    CheckConstraint("coupon_type IN ('GOODS','SHIPPING')", name="ck_coupons_type"),
    CheckConstraint("shop_id IS NULL OR coupon_type = 'GOODS'", name="ck_coupons_shop_type"),
)
coupon_usages = Table(
    "coupon_usages",
    Base.metadata,
    identity("usage_id"),
    reference("coupon_usages", "coupon_id", "coupons.coupon_id"),
    reference("coupon_usages", "user_id", "users.user_id"),
    reference("coupon_usages", "order_id", "orders.order_id"),
    Column("discount_amount", Numeric(14, 2), nullable=False),
    timestamp("used_at"),
    CheckConstraint("discount_amount >= 0", name="coupon_usages_discount_amount_check"),
    UniqueConstraint("coupon_id", "order_id", name="uq_coupon_usages_coupon_order"),
)
product_reviews = Table(
    "product_reviews",
    Base.metadata,
    identity("review_id"),
    reference("product_reviews", "product_id", "products.product_id"),
    reference("product_reviews", "user_id", "users.user_id"),
    reference("product_reviews", "order_item_id", "order_items.order_item_id", unique=True),
    Column("rating", SmallInteger, nullable=False),
    Column("comment", Text),
    timestamp("created_at"),
    timestamp("updated_at"),
    CheckConstraint("rating >= 1 AND rating <= 5", name="product_reviews_rating_check"),
)
payments = Table(
    "payments",
    Base.metadata,
    identity("payment_id"),
    reference("payments", "order_id", "orders.order_id"),
    Column("payment_method", String(20), nullable=False),
    Column("amount", Numeric(14, 2), nullable=False),
    Column("payment_status", String(20), nullable=False, server_default=text("'PENDING'")),
    Column("transaction_code", String(150)),
    Column("paid_at", DateTime(timezone=True)),
    timestamp("created_at"),
    CheckConstraint(
        "payment_method IN ('COD','BANK_TRANSFER','VNPAY','MOMO')",
        name="payments_payment_method_check",
    ),
    CheckConstraint("amount >= 0", name="payments_amount_check"),
    CheckConstraint(
        "payment_status IN ('PENDING','SUCCESS','FAILED','REFUNDED')",
        name="payments_payment_status_check",
    ),
)
shippers = Table(
    "shippers",
    Base.metadata,
    identity("shipper_id"),
    Column("full_name", String(150), nullable=False),
    Column("phone", String(30), nullable=False),
    Column("carrier", String(100)),
    Column("is_active", Boolean, nullable=False, server_default=text("TRUE")),
    timestamp("created_at"),
)
shipments = Table(
    "shipments",
    Base.metadata,
    identity("shipment_id"),
    reference("shipments", "shop_order_id", "shop_orders.shop_order_id", unique=True),
    reference("shipments", "shipper_id", "shippers.shipper_id", nullable=True),
    Column("carrier", String(100)),
    Column("tracking_number", String(100)),
    Column("shipping_method", String(20), nullable=False, server_default=text("'STANDARD'")),
    Column("shipping_fee", Numeric(14, 2), nullable=False, server_default=text("0")),
    Column("shipping_status", String(20), nullable=False, server_default=text("'PENDING'")),
    Column("shipped_at", DateTime(timezone=True)),
    Column("delivered_at", DateTime(timezone=True)),
    timestamp("created_at"),
    CheckConstraint(
        "shipping_method IN ('STANDARD','EXPRESS','INSTANT')",
        name="shipments_shipping_method_check",
    ),
    CheckConstraint("shipping_fee >= 0", name="shipments_shipping_fee_check"),
    CheckConstraint(
        "shipping_status IN ('PENDING','PICKED_UP','IN_TRANSIT','DELIVERED','FAILED')",
        name="shipments_shipping_status_check",
    ),
)
shipment_tracking = Table(
    "shipment_tracking",
    Base.metadata,
    identity("tracking_id"),
    reference("shipment_tracking", "shipment_id", "shipments.shipment_id"),
    Column("status", String(20), nullable=False),
    Column("description", Text),
    timestamp("created_at"),
    CheckConstraint(
        "status IN ('PENDING','PICKED_UP','IN_TRANSIT','DELIVERED','FAILED')",
        name="shipment_tracking_status_check",
    ),
)

for name, table, columns in [
    ("idx_audit_logs_record", audit_logs, ["table_name", "record_id", "changed_at"]),
    ("idx_audit_logs_actor", audit_logs, ["actor_user_id"]),
    ("idx_price_history_product", product_price_history, ["product_id", "changed_at"]),
    ("idx_inventory_movements_product", inventory_movements, ["product_id", "created_at"]),
    ("idx_inventory_movements_order", inventory_movements, ["order_id"]),
    ("idx_order_status_history_order", shop_order_status_history, ["shop_order_id", "changed_at"]),
    ("idx_shop_approval_history_shop", shop_approval_history, ["shop_id", "created_at"]),
    ("idx_coupons_shop", coupons, ["shop_id"]),
    ("idx_coupon_usages_coupon", coupon_usages, ["coupon_id"]),
    ("idx_coupon_usages_order", coupon_usages, ["order_id"]),
    ("idx_reviews_product", product_reviews, ["product_id"]),
    ("idx_payments_order", payments, ["order_id"]),
    ("idx_shipments_shipper", shipments, ["shipper_id"]),
    ("idx_shipment_tracking_shipment", shipment_tracking, ["shipment_id", "created_at"]),
]:
    Index(
        name,
        *(
            table.c[column].desc()
            if len(columns) > 1 and column in {"created_at", "changed_at"}
            else table.c[column]
            for column in columns
        ),
    )
Index(
    "uq_payments_transaction_code",
    payments.c.payment_method,
    payments.c.transaction_code,
    unique=True,
    postgresql_where=text("transaction_code IS NOT NULL"),
)
Index(
    "uq_payments_one_success_per_order",
    payments.c.order_id,
    unique=True,
    postgresql_where=text("payment_status = 'SUCCESS'"),
)
