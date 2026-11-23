-- Review and explicit approval required before running against the business database.
-- No DROP TABLE, data rewrite, identity reset, or provider configuration.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
ALTER TABLE marketplace.coupons ADD COLUMN coupon_type VARCHAR(20) NOT NULL DEFAULT 'GOODS';
ALTER TABLE marketplace.coupons ADD CONSTRAINT ck_coupons_type
    CHECK (coupon_type IN ('GOODS','SHIPPING'));
ALTER TABLE marketplace.coupons ADD CONSTRAINT ck_coupons_shop_type
    CHECK (shop_id IS NULL OR coupon_type = 'GOODS');
ALTER TABLE marketplace.orders ADD COLUMN shipping_discount_amount NUMERIC(14,2) NOT NULL DEFAULT 0;
ALTER TABLE marketplace.orders ADD CONSTRAINT ck_orders_shipping_discount CHECK (shipping_discount_amount >= 0);
ALTER TABLE marketplace.coupon_usages DROP CONSTRAINT coupon_usages_order_id_key;
ALTER TABLE marketplace.coupon_usages ADD CONSTRAINT uq_coupon_usages_coupon_order
    UNIQUE (coupon_id, order_id);
CREATE INDEX idx_coupon_usages_order ON marketplace.coupon_usages (order_id);
ALTER TABLE marketplace.orders DROP CONSTRAINT ck_orders_payment;
ALTER TABLE marketplace.orders ADD CONSTRAINT ck_orders_payment
    CHECK (payment_method IN ('COD','BANK_TRANSFER','VNPAY','MOMO'));
ALTER TABLE marketplace.payments DROP CONSTRAINT payments_payment_method_check;
ALTER TABLE marketplace.payments ADD CONSTRAINT payments_payment_method_check
    CHECK (payment_method IN ('COD','BANK_TRANSFER','VNPAY','MOMO'));
COMMIT;
