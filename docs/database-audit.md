# Database audit — kết quả mới nhất và lịch sử

## Kiểm tra lại P1-02 ngày 09/11/2026 — kết quả hiện hành

Schema marketplace hiện tồn tại trong database marketplace_db, PostgreSQL 16.15. Có đủ 12 bảng và 86 cột. So sánh offline toàn bộ tên/thứ tự/kiểu/độ dài/precision/nullability/identity/default với SQL gốc: không có chênh lệch. Không thấy bảng nghiệp vụ trong public ở lần kiểm tra này; không suy diễn cách dữ liệu đã được thay đổi giữa hai lần audit.

Có 55 constraints (12 PK, 15 FK, 12 UNIQUE, 16 CHECK), tất cả validated; 36 indexes đều valid/ready; 6 triggers enabled và function marketplace.set_updated_at có định nghĩa phù hợp. Đã review các định nghĩa constraint/index/trigger/function. users hiện có user_role và updated_at đúng tên, NOT NULL/default đúng SQL, đủ ck_users_role/ck_users_status/ck_users_email_nonblank và uq_users_email_lower. Trigger users hiện tham chiếu cột updated_at tồn tại.

Kiểm chứng PASS: psql ON_ERROR_STOP, transaction REPEATABLE READ READ ONLY, timeout 15 giây và ROLLBACK; SELECT xác nhận read_only=on. Đối chiếu catalog và so sánh tự động 86 cột thành công. Không đọc hàng dữ liệu nghiệp vụ hoặc thử mutation; kết quả không xác nhận hành vi checkout/auth và không chứng minh bảo toàn dữ liệu giữa hai lần audit.

Q08 RESOLVED: các chênh lệch D01–D10 trước đây không còn quan sát được. P1-02 vẫn DONE; P1-03 chưa thực hiện, còn chờ các quyết định nghiệp vụ Q03–Q06. Không thay database/schema/dữ liệu, Compose, volume, network, SQL hoặc code trong lần kiểm tra lại này.

---

## Bản ghi audit trước khi kiểm tra lại — chỉ dùng làm lịch sử

# Báo cáo kiểm tra database P1-02

Ngày: 09/11/2026 (Asia/Bangkok).

## Kết luận

Đã hoàn thành audit nhưng database không khớp SQL/DOCX. Database marketplace_db trên container marketplace_postgres đang chạy PostgreSQL 16.15 (Debian 16.15-1.pgdg13+2). Schema marketplace không tồn tại. Có đúng 12 bảng cùng tên trong public; bảng users có nhiều chênh lệch. Không sửa database hoặc tự chuyển mapping sang public.

## Phương pháp và giới hạn

Ba phiên psql đọc metadata, ON_ERROR_STOP, BEGIN READ ONLY, statement timeout 15 giây, kết thúc ROLLBACK; SELECT xác nhận transaction_read_only=on. Hai phiên catalog chính và public dùng REPEATABLE READ. Đối chiếu pg_namespace/pg_class độc lập với information_schema; đọc pg_constraint, pg_index, pg_trigger, pg_proc và default/identity của cột.

Không chạy SQL nguồn, DDL/DML, nextval hoặc SELECT hàng dữ liệu nghiệp vụ. Không đếm dữ liệu hoặc khẳng định các bảng rỗng. Không chạy UPDATE thử trigger. Không khởi động/dừng/recreate database/container, không thay volume/network. Chỉ đọc marketplace_db; tên database không template quan sát được là marketplace_db và postgres, không khảo sát database postgres.

So sánh cột tự động offline theo tên/thứ tự/kiểu/độ dài/precision/NOT NULL/identity/default; review định nghĩa constraints/indexes/triggers/function, tính đến cách PostgreSQL deparse IN thành ANY/ARRAY và các cast ngầm. Không tạo database tham chiếu. Mỗi phiên có snapshot riêng, không khẳng định cả ba cùng một snapshot nếu có tác nhân khác sửa DDL đồng thời.

## So sánh tổng thể

| Hạng mục | SQL gốc | Database quan sát |
| --- | --- | --- |
| Schema | marketplace | public; marketplace không tồn tại |
| Bảng | 12 | 12 cùng tên trong public |
| Cột | 86 | 86; hai tên cột khác ở users |
| Primary key | 12 | 12 |
| Foreign key | 15 | 15 |
| UNIQUE constraints | 12 | 12 |
| CHECK constraints | 16 | 13 |
| Index tổng gồm PK/UNIQUE | 36 | 35 |
| Trigger nghiệp vụ | 6 | 6 enabled; trigger users tham chiếu cột thiếu |
| Function trigger | 1 | public.set_updated_at |

Toàn bộ 52 constraints hiện có được validated; 35 indexes valid/ready. Metadata này không thay thế kiểm thử ứng dụng hoặc kiểm tra dữ liệu.

## Chênh lệch D01–D10

| ID | Yêu cầu SQL/DOCX | Quan sát thực tế và ảnh hưởng |
| --- | --- | --- |
| D01 | Bảng/function thuộc marketplace | Tất cả nằm ở public; mapping marketplace sẽ không tìm thấy bảng |
| D02 | user_role VARCHAR(10) NOT NULL DEFAULT 'USER' | Không có user_role; có role VARCHAR(10) nullable, không default |
| D03 | updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW() | Không có updated_at; có update_at TIMESTAMPTZ nullable, không default |
| D04 | email/password_hash/full_name NOT NULL | Cả ba nullable, không bảo đảm dữ liệu tài khoản bắt buộc |
| D05 | user_status NOT NULL DEFAULT 'ACTIVE' | Nullable, không default |
| D06 | created_at NOT NULL DEFAULT NOW() | Nullable, không default |
| D07 | CHECK ck_users_role giới hạn USER/ADMIN | Không có |
| D08 | CHECK ck_users_status giới hạn ACTIVE/LOCKED | Không có |
| D09 | CHECK ck_users_email_nonblank | Không có |
| D10 | Unique index uq_users_email_lower trên LOWER(email) | Không có; DB không bảo đảm email duy nhất không phân biệt hoa/thường |

Không kết luận role/update_at từng được rename từ cột nào; chỉ ghi nhận khác tên yêu cầu. users_pkey còn tồn tại; mọi khác biệt cột/default/NOT NULL đều tập trung ở users.

Trigger public.trg_users_updated_at đang enabled, BEFORE UPDATE, gọi public.set_updated_at(); function gán NEW.updated_at nhưng users chỉ có update_at. Theo định nghĩa, UPDATE một dòng users sẽ lỗi thiếu trường updated_at. Đây là kết luận phân tích cấu trúc; không chạy mutation để tái hiện.

## Kết quả từng bảng

Mọi kết quả khớp dưới đây đều xét độc lập với D01; không bảng nào đã đúng vị trí schema marketplace.

| Bảng trong public | Cột | Kết quả |
| --- | ---: | --- |
| addresses | 10 | Cột và ràng buộc/index tương ứng khớp |
| cart_items | 5 | Khớp |
| carts | 4 | Khớp |
| categories | 6 | Khớp |
| inventory | 3 | Khớp |
| order_items | 7 | Khớp |
| orders | 9 | Khớp |
| product_images | 6 | Khớp |
| products | 10 | Khớp |
| shop_orders | 7 | Khớp |
| shops | 10 | Khớp |
| users | 9 | Lệch như D02–D10; trigger không phù hợp cột |

11 identity là GENERATED ALWAYS. inventory.product_id là PK/FK không identity đúng SQL. Hai composite FK order_items, unique buyer/idempotency, SKU theo shop, một shop/chủ, một giỏ/user, partial unique ảnh chính và địa chỉ mặc định còn tồn tại. FK cascade product_images/cart_items đúng SQL. Năm trigger ngoài users có cột updated_at phù hợp function; chưa thử ghi dữ liệu.

## Kiểm thử và kết quả

- PASS: kết nối database hiện hữu, PostgreSQL major 16, xác nhận READ ONLY và ROLLBACK.
- PASS: kiểm tra schema bằng pg_namespace, đủ 12 bảng/86 cột trong public và báo toàn bộ chênh lệch cột tự động.
- PASS: tất cả constraints validated, indexes valid/ready; review constraint/index/trigger/function.
- FAIL: database tuân thủ SQL gốc, vì D01–D10.
- NOT RUN: tests INSERT/UPDATE/checkout/auth hoặc kiểm tra dữ liệu; ngoài phạm vi audit chỉ đọc.

## Quyết định còn chờ và điểm dừng

P1-02 DONE vì audit hoàn tất và báo chênh lệch. Q02 đã giải quyết. Q08 OPEN: người dùng cần quyết định hướng xử lý schema public và users trước P1-03/P2-03. Không tự sửa SQL/DOCX, mapping, schema hoặc dữ liệu. Nếu cần migration không mất dữ liệu, phải có task riêng được yêu cầu, khảo sát dữ liệu và kế hoạch backup trước; hiện chưa thực hiện. Không chạy lại SQL init trên DB hiện hữu.

Named volume marketplace_postgres_data và network marketplace_network được giữ nguyên. Dừng sau P1-02, chưa thực hiện task tiếp theo.

## Metadata evidence

Source SQL SHA-256: `2c7a7991ce2e8b98fdc15b3fbf7308a9e5488f35dd808fc9b5c7153424a43be2`.

### Constraints (public)

```text
addresses | addresses_pkey | PRIMARY KEY (address_id)
addresses | fk_addresses_user | FOREIGN KEY (user_id) REFERENCES users(user_id)
cart_items | cart_items_pkey | PRIMARY KEY (cart_item_id)
cart_items | ck_cart_items_quantity | CHECK (quantity > 0)
cart_items | fk_cart_items_cart | FOREIGN KEY (cart_id) REFERENCES carts(cart_id) ON DELETE CASCADE
cart_items | fk_cart_items_product | FOREIGN KEY (product_id) REFERENCES products(product_id)
cart_items | uq_cart_items_cart_product | UNIQUE (cart_id, product_id)
carts | carts_pkey | PRIMARY KEY (cart_id)
carts | carts_user_id_key | UNIQUE (user_id)
carts | fk_carts_user | FOREIGN KEY (user_id) REFERENCES users(user_id)
categories | categories_category_slug_key | UNIQUE (category_slug)
categories | categories_pkey | PRIMARY KEY (category_id)
categories | ck_categories_no_self_parent | CHECK (parent_category_id IS DISTINCT FROM category_id)
categories | fk_categories_parent | FOREIGN KEY (parent_category_id) REFERENCES categories(category_id)
inventory | ck_inventory_quantity | CHECK (quantity >= 0)
inventory | fk_inventory_product | FOREIGN KEY (product_id) REFERENCES products(product_id)
inventory | inventory_pkey | PRIMARY KEY (product_id)
order_items | ck_order_items_price | CHECK (unit_price >= 0::numeric)
order_items | ck_order_items_quantity | CHECK (quantity > 0)
order_items | fk_order_items_shop_order | FOREIGN KEY (shop_order_id, shop_id) REFERENCES shop_orders(shop_order_id, shop_id)
order_items | fk_order_items_shop_product | FOREIGN KEY (shop_id, product_id) REFERENCES products(shop_id, product_id)
order_items | order_items_pkey | PRIMARY KEY (order_item_id)
order_items | uq_order_items_shop_order_product | UNIQUE (shop_order_id, product_id)
orders | ck_orders_payment | CHECK (payment_method::text = 'COD'::text)
orders | ck_orders_total | CHECK (total_amount >= 0::numeric)
orders | fk_orders_buyer | FOREIGN KEY (buyer_user_id) REFERENCES users(user_id)
orders | orders_pkey | PRIMARY KEY (order_id)
orders | uq_orders_buyer_idempotency | UNIQUE (buyer_user_id, idempotency_key)
product_images | ck_product_images_key_nonblank | CHECK (btrim(image_key) <> ''::text)
product_images | ck_product_images_sort_order | CHECK (sort_order >= 0)
product_images | fk_product_images_product | FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
product_images | product_images_pkey | PRIMARY KEY (product_image_id)
product_images | uq_product_images_key | UNIQUE (product_id, image_key)
products | ck_products_price | CHECK (price >= 0::numeric)
products | fk_products_category | FOREIGN KEY (category_id) REFERENCES categories(category_id)
products | fk_products_shop | FOREIGN KEY (shop_id) REFERENCES shops(shop_id)
products | products_pkey | PRIMARY KEY (product_id)
products | uq_products_shop_product | UNIQUE (shop_id, product_id)
products | uq_products_shop_sku | UNIQUE (shop_id, sku)
shop_orders | ck_shop_orders_status | CHECK (order_status::text = ANY (ARRAY['PENDING'::character varying, 'CONFIRMED'::character varying, 'SHIPPING'::character varying, 'COMPLETED'::character varying, 'CANCELLED'::character varying]::text[]))
shop_orders | ck_shop_orders_subtotal | CHECK (subtotal >= 0::numeric)
shop_orders | fk_shop_orders_order | FOREIGN KEY (order_id) REFERENCES orders(order_id)
shop_orders | fk_shop_orders_shop | FOREIGN KEY (shop_id) REFERENCES shops(shop_id)
shop_orders | shop_orders_pkey | PRIMARY KEY (shop_order_id)
shop_orders | uq_shop_orders_id_shop | UNIQUE (shop_order_id, shop_id)
shop_orders | uq_shop_orders_order_shop | UNIQUE (order_id, shop_id)
shops | ck_shops_status | CHECK (shop_status::text = ANY (ARRAY['PENDING'::character varying, 'APPROVED'::character varying, 'REJECTED'::character varying, 'LOCKED'::character varying]::text[]))
shops | fk_shops_owner | FOREIGN KEY (owner_user_id) REFERENCES users(user_id)
shops | shops_owner_user_id_key | UNIQUE (owner_user_id)
shops | shops_pkey | PRIMARY KEY (shop_id)
shops | shops_shop_slug_key | UNIQUE (shop_slug)
users | users_pkey | PRIMARY KEY (user_id)
```

### Indexes

```sql
CREATE UNIQUE INDEX addresses_pkey ON public.addresses USING btree (address_id);
CREATE INDEX idx_addresses_user ON public.addresses USING btree (user_id);
CREATE UNIQUE INDEX uq_addresses_default_per_user ON public.addresses USING btree (user_id) WHERE (is_default = true);
CREATE UNIQUE INDEX cart_items_pkey ON public.cart_items USING btree (cart_item_id);
CREATE INDEX idx_cart_items_product ON public.cart_items USING btree (product_id);
CREATE UNIQUE INDEX uq_cart_items_cart_product ON public.cart_items USING btree (cart_id, product_id);
CREATE UNIQUE INDEX carts_pkey ON public.carts USING btree (cart_id);
CREATE UNIQUE INDEX carts_user_id_key ON public.carts USING btree (user_id);
CREATE UNIQUE INDEX categories_category_slug_key ON public.categories USING btree (category_slug);
CREATE UNIQUE INDEX categories_pkey ON public.categories USING btree (category_id);
CREATE INDEX idx_categories_parent ON public.categories USING btree (parent_category_id);
CREATE UNIQUE INDEX inventory_pkey ON public.inventory USING btree (product_id);
CREATE INDEX idx_order_items_shop_product ON public.order_items USING btree (shop_id, product_id);
CREATE UNIQUE INDEX order_items_pkey ON public.order_items USING btree (order_item_id);
CREATE UNIQUE INDEX uq_order_items_shop_order_product ON public.order_items USING btree (shop_order_id, product_id);
CREATE INDEX idx_orders_buyer_created ON public.orders USING btree (buyer_user_id, created_at DESC);
CREATE UNIQUE INDEX orders_pkey ON public.orders USING btree (order_id);
CREATE UNIQUE INDEX uq_orders_buyer_idempotency ON public.orders USING btree (buyer_user_id, idempotency_key);
CREATE INDEX idx_product_images_sort ON public.product_images USING btree (product_id, sort_order, product_image_id);
CREATE UNIQUE INDEX product_images_pkey ON public.product_images USING btree (product_image_id);
CREATE UNIQUE INDEX uq_product_images_key ON public.product_images USING btree (product_id, image_key);
CREATE UNIQUE INDEX uq_product_images_primary ON public.product_images USING btree (product_id) WHERE (is_primary = true);
CREATE INDEX idx_products_category ON public.products USING btree (category_id);
CREATE INDEX idx_products_shop_active ON public.products USING btree (shop_id, is_active);
CREATE UNIQUE INDEX products_pkey ON public.products USING btree (product_id);
CREATE UNIQUE INDEX uq_products_shop_product ON public.products USING btree (shop_id, product_id);
CREATE UNIQUE INDEX uq_products_shop_sku ON public.products USING btree (shop_id, sku);
CREATE INDEX idx_shop_orders_shop_status ON public.shop_orders USING btree (shop_id, order_status);
CREATE UNIQUE INDEX shop_orders_pkey ON public.shop_orders USING btree (shop_order_id);
CREATE UNIQUE INDEX uq_shop_orders_id_shop ON public.shop_orders USING btree (shop_order_id, shop_id);
CREATE UNIQUE INDEX uq_shop_orders_order_shop ON public.shop_orders USING btree (order_id, shop_id);
CREATE UNIQUE INDEX shops_owner_user_id_key ON public.shops USING btree (owner_user_id);
CREATE UNIQUE INDEX shops_pkey ON public.shops USING btree (shop_id);
CREATE UNIQUE INDEX shops_shop_slug_key ON public.shops USING btree (shop_slug);
CREATE UNIQUE INDEX users_pkey ON public.users USING btree (user_id);
```

### Triggers and function (public)

```sql
CREATE TRIGGER trg_carts_updated_at BEFORE UPDATE ON carts FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_inventory_updated_at BEFORE UPDATE ON inventory FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_shop_orders_updated_at BEFORE UPDATE ON shop_orders FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_shops_updated_at BEFORE UPDATE ON shops FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE OR REPLACE FUNCTION public.set_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$function$

```
