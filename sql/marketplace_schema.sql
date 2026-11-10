-- MARKETPLACE DATABASE STRUCTURE - PostgreSQL 16
-- Docker .env: POSTGRES_DB=marketplace_db, POSTGRES_USER=marketplace_user
-- Connect to the EXISTING marketplace_db before running.
-- This script does NOT create/drop a database or delete existing data.
-- Creates all objects explicitly in schema marketplace (not public).
-- Note: if objects already exist inside marketplace, CREATE TABLE will stop
-- and the transaction will roll back rather than overwrite them.

BEGIN;

CREATE SCHEMA IF NOT EXISTS marketplace;


-- 01. Users
CREATE TABLE marketplace.users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30),
    user_role VARCHAR(10) NOT NULL DEFAULT 'USER',
    user_status VARCHAR(10) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_users_role CHECK (user_role IN ('USER', 'ADMIN')),
    CONSTRAINT ck_users_status CHECK (user_status IN ('ACTIVE', 'LOCKED')),
    CONSTRAINT ck_users_email_nonblank CHECK (BTRIM(email) <> '')
);
CREATE UNIQUE INDEX uq_users_email_lower ON marketplace.users (LOWER(email));

-- 02. Shops
CREATE TABLE marketplace.shops (
    shop_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_user_id BIGINT NOT NULL UNIQUE,
    shop_name VARCHAR(150) NOT NULL,
    shop_slug VARCHAR(160) NOT NULL UNIQUE,
    description TEXT,
    contact_email VARCHAR(255),
    logo_key TEXT,
    shop_status VARCHAR(12) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_shops_owner FOREIGN KEY (owner_user_id) REFERENCES marketplace.users(user_id),
    CONSTRAINT ck_shops_status CHECK (shop_status IN ('PENDING', 'APPROVED', 'REJECTED', 'LOCKED'))
);

-- 03. Categories
CREATE TABLE marketplace.categories (
    category_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    parent_category_id BIGINT,
    category_name VARCHAR(120) NOT NULL,
    category_slug VARCHAR(140) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_categories_parent FOREIGN KEY (parent_category_id) REFERENCES marketplace.categories(category_id),
    CONSTRAINT ck_categories_no_self_parent CHECK (parent_category_id IS DISTINCT FROM category_id)
);

-- 04. Products
CREATE TABLE marketplace.products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shop_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL,
    sku VARCHAR(64) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    description TEXT,
    price NUMERIC(14,2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_products_shop FOREIGN KEY (shop_id) REFERENCES marketplace.shops(shop_id),
    CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES marketplace.categories(category_id),
    CONSTRAINT uq_products_shop_sku UNIQUE (shop_id, sku),
    CONSTRAINT uq_products_shop_product UNIQUE (shop_id, product_id),
    CONSTRAINT ck_products_price CHECK (price >= 0)
);

-- 05. Product images
CREATE TABLE marketplace.product_images (
    product_image_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id BIGINT NOT NULL,
    image_key TEXT NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_product_images_product FOREIGN KEY (product_id) REFERENCES marketplace.products(product_id) ON DELETE CASCADE,
    CONSTRAINT ck_product_images_sort_order CHECK (sort_order >= 0),
    CONSTRAINT ck_product_images_key_nonblank CHECK (BTRIM(image_key) <> ''),
    CONSTRAINT uq_product_images_key UNIQUE (product_id, image_key)
);
CREATE UNIQUE INDEX uq_product_images_primary ON marketplace.product_images(product_id) WHERE is_primary = TRUE;

-- 06. Inventory
CREATE TABLE marketplace.inventory (
    product_id BIGINT PRIMARY KEY,
    quantity INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_inventory_product FOREIGN KEY (product_id) REFERENCES marketplace.products(product_id),
    CONSTRAINT ck_inventory_quantity CHECK (quantity >= 0)
);

-- 07. Addresses
CREATE TABLE marketplace.addresses (
    address_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL,
    recipient_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    address_line TEXT NOT NULL,
    ward VARCHAR(120),
    district VARCHAR(120),
    city VARCHAR(120) NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_addresses_user FOREIGN KEY (user_id) REFERENCES marketplace.users(user_id)
);
CREATE UNIQUE INDEX uq_addresses_default_per_user ON marketplace.addresses(user_id) WHERE is_default = TRUE;

-- 08. Carts
CREATE TABLE marketplace.carts (
    cart_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_carts_user FOREIGN KEY (user_id) REFERENCES marketplace.users(user_id)
);

-- 09. Cart items
CREATE TABLE marketplace.cart_items (
    cart_item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cart_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_cart_items_cart FOREIGN KEY (cart_id) REFERENCES marketplace.carts(cart_id) ON DELETE CASCADE,
    CONSTRAINT fk_cart_items_product FOREIGN KEY (product_id) REFERENCES marketplace.products(product_id),
    CONSTRAINT uq_cart_items_cart_product UNIQUE (cart_id, product_id),
    CONSTRAINT ck_cart_items_quantity CHECK (quantity > 0)
);

-- 10. Orders
CREATE TABLE marketplace.orders (
    order_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    buyer_user_id BIGINT NOT NULL,
    idempotency_key UUID NOT NULL,
    recipient_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    shipping_address TEXT NOT NULL,
    total_amount NUMERIC(14,2) NOT NULL,
    payment_method VARCHAR(10) NOT NULL DEFAULT 'COD',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_orders_buyer FOREIGN KEY (buyer_user_id) REFERENCES marketplace.users(user_id),
    CONSTRAINT uq_orders_buyer_idempotency UNIQUE (buyer_user_id, idempotency_key),
    CONSTRAINT ck_orders_total CHECK (total_amount >= 0),
    CONSTRAINT ck_orders_payment CHECK (payment_method IN ('COD'))
);

-- 11. Shop orders
CREATE TABLE marketplace.shop_orders (
    shop_order_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id BIGINT NOT NULL,
    shop_id BIGINT NOT NULL,
    order_status VARCHAR(12) NOT NULL DEFAULT 'PENDING',
    subtotal NUMERIC(14,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_shop_orders_order FOREIGN KEY (order_id) REFERENCES marketplace.orders(order_id),
    CONSTRAINT fk_shop_orders_shop FOREIGN KEY (shop_id) REFERENCES marketplace.shops(shop_id),
    CONSTRAINT uq_shop_orders_order_shop UNIQUE (order_id, shop_id),
    CONSTRAINT uq_shop_orders_id_shop UNIQUE (shop_order_id, shop_id),
    CONSTRAINT ck_shop_orders_status CHECK (order_status IN ('PENDING', 'CONFIRMED', 'SHIPPING', 'COMPLETED', 'CANCELLED')),
    CONSTRAINT ck_shop_orders_subtotal CHECK (subtotal >= 0)
);

-- 12. Order items
CREATE TABLE marketplace.order_items (
    order_item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shop_order_id BIGINT NOT NULL,
    shop_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    unit_price NUMERIC(14,2) NOT NULL,
    quantity INTEGER NOT NULL,
    CONSTRAINT fk_order_items_shop_order FOREIGN KEY (shop_order_id, shop_id)
        REFERENCES marketplace.shop_orders(shop_order_id, shop_id),
    CONSTRAINT fk_order_items_shop_product FOREIGN KEY (shop_id, product_id)
        REFERENCES marketplace.products(shop_id, product_id),
    CONSTRAINT ck_order_items_price CHECK (unit_price >= 0),
    CONSTRAINT ck_order_items_quantity CHECK (quantity > 0),
    CONSTRAINT uq_order_items_shop_order_product UNIQUE (shop_order_id, product_id)
);

-- Supporting indexes for common joins and lookups
CREATE INDEX idx_categories_parent ON marketplace.categories(parent_category_id);
CREATE INDEX idx_products_category ON marketplace.products(category_id);
CREATE INDEX idx_products_shop_active ON marketplace.products(shop_id, is_active);
CREATE INDEX idx_product_images_sort ON marketplace.product_images(product_id, sort_order, product_image_id);
CREATE INDEX idx_addresses_user ON marketplace.addresses(user_id);
CREATE INDEX idx_cart_items_product ON marketplace.cart_items(product_id);
CREATE INDEX idx_orders_buyer_created ON marketplace.orders(buyer_user_id, created_at DESC);
CREATE INDEX idx_shop_orders_shop_status ON marketplace.shop_orders(shop_id, order_status);
CREATE INDEX idx_order_items_shop_product ON marketplace.order_items(shop_id, product_id);

-- Automatic updated_at maintenance
CREATE FUNCTION marketplace.set_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON marketplace.users FOR EACH ROW EXECUTE FUNCTION marketplace.set_updated_at();
CREATE TRIGGER trg_shops_updated_at BEFORE UPDATE ON marketplace.shops FOR EACH ROW EXECUTE FUNCTION marketplace.set_updated_at();
CREATE TRIGGER trg_products_updated_at BEFORE UPDATE ON marketplace.products FOR EACH ROW EXECUTE FUNCTION marketplace.set_updated_at();
CREATE TRIGGER trg_inventory_updated_at BEFORE UPDATE ON marketplace.inventory FOR EACH ROW EXECUTE FUNCTION marketplace.set_updated_at();
CREATE TRIGGER trg_carts_updated_at BEFORE UPDATE ON marketplace.carts FOR EACH ROW EXECUTE FUNCTION marketplace.set_updated_at();
CREATE TRIGGER trg_shop_orders_updated_at BEFORE UPDATE ON marketplace.shop_orders FOR EACH ROW EXECUTE FUNCTION marketplace.set_updated_at();

COMMIT;

-- Verification
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'marketplace' AND table_type = 'BASE TABLE'
ORDER BY table_name;


-- Count expected tables (12)
SELECT COUNT(*) AS total_marketplace_tables
FROM information_schema.tables
WHERE table_schema = 'marketplace' AND table_type = 'BASE TABLE';
