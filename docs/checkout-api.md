# P5-02 — Checkout COD bằng transaction

Backend đã có `POST /api/v1/orders/checkout`. API/transaction thuộc P5-02; giao diện `/thanh-toan` đã tích hợp ở [P5-03](checkout-ui.md), lịch sử đơn thuộc P5-04. Không tạo đơn test trong DB hiện hữu.

## Request và response

Cần access cookie, user ACTIVE, CSRF cookie + `X-CSRF-Token`, Origin đúng PUBLIC_ORIGIN và header `Idempotency-Key` UUID. Body minh họa (thay bằng ID và giỏ thật nếu thao tác thực tế):

```json
{
  "address_id": "1",
  "payment_method": "COD",
  "items": [
    { "product_id": "2", "quantity": 1, "expected_unit_price": "120000.00" }
  ]
}
```

Phải khớp toàn bộ giỏ theo product ID/quantity. Có từ1..1000 dòng, không product ID trùng; quantity integer thật1..2147483647; expected price là decimal string (không float/exponent), tối đa12 chữ số nguyên/2 thập phân. Chỉ COD. Unknown fields, UUID thiếu/sai, shape sai trả422. Không nhận buyer/shop/tổng tiền từ client.

Lần đầu201 `{data:OrderDetail}`; cùng buyer/key replay200. Response có BIGINT strings, Decimal strings, created_at UTC, total/COD, snapshots người nhận/phone/địa chỉ và từng shop_orders/subtotal/items. Mỗi đơn shop mới PENDING, không tự tạo trạng thái đơn tổng. Cache-Control:no-store.

## Transaction, khóa và retry

Router dùng `current_subject`, `csrf_guard` và session chung. `services/checkout.py` sở hữu transaction qua COMMIT để có thể retry; mỗi attempt tạo `AccessPolicy(AccessRepository(write=True))`, kiểm lại principal ACTIVE/role. Không bọc thêm WriteAccess/begin lồng nhau; không trả success trước commit. Các policy và CSRF/JWT dùng chung với mutation khác.

Khóa theo thứ tự: user buyer → cart → shared advisory lock cây danh mục → shop theo ID → product theo ID → inventory theo product ID. Địa chỉ cũng được bảo vệ bởi user lock của CRUD địa chỉ. Đọc lại catalog sau khóa, không tin giá/tồn từ frontend. Cart lock phối hợp với cart mutations.

`db/locks.py` đặt namespace/key `(731921,1)`. Checkout dùng `pg_advisory_xact_lock_shared`; category tree/status mutations phase sau phải dùng `pg_advisory_xact_lock` exclusive cùng hai key trước shop/product. Shop/product/inventory mutations tương lai phải theo lock order chung. Shared lock cho phép các checkout không tranh hàng chạy đồng thời, không dùng mutex in-process hoặc bảng mới.

Tìm order theo buyer/key trước kiểm cart/address/catalog. Replay trả đơn đã commit, không áp payload mới, không giảm tồn hoặc xóa giỏ mới. Shape vẫn phải hợp lệ và user phải ACTIVE. Schema không có request hash nên không phát hiện mọi payload retry khác nhau; client phải giữ cùng key cho cùng ý định, không tái dùng key cũ cho đơn mới.

Lần đầu kiểm ownership địa chỉ, shop APPROVED, product active, category/ancestors public, không self-purchase, expected price đúng Decimal, inventory đủ. Giá đổi409 PRICE_CHANGED; thiếu tồn409 OUT_OF_STOCK; cart/catalog đổi409 CART_CHANGED; địa chỉ foreign/missing404; self-purchase403. Tổng phải <=999999999999.99 để vừa NUMERIC14,2, không clamp/làm tròn. Tổng chỉ là giá×lượng, không phí/discount giả.

Validate mọi dòng trước ghi; insert orders → một shop_orders mỗi shop → order_items đúng composite FK/snapshots → giảm kho có điều kiện → xóa cart_items buyer, tất cả trong một transaction. Không gọi S3/dịch vụ mạng trong transaction.

```python
session.execute(
    update(Inventory)
    .where(Inventory.product_id == product_id, Inventory.quantity >= quantity)
    .values(quantity=Inventory.quantity - quantity)
    .returning(Inventory.product_id)
)
```

Row lock và conditional UPDATE chống overselling. Giữ unique `(buyer_user_id,idempotency_key)` làm hàng rào chống trùng. Retry tối đa3 attempt chỉ cho SQLSTATE40001/40P01 hoặc unique conflict đúng constraint idempotency, cùng key/payload và kiểm lại toàn bộ. DB lỗi khác/timeout trả503 đã làm sạch, không tự retry lỗi kết nối có kết quả commit chưa rõ. Caller dùng lại key cũ để xác minh/replay.

Replay đọc tên/giá/lượng sản phẩm và recipient/phone/shipping_address từ order tables; sửa/xóa địa chỉ hoặc đổi/ẩn product sau mua không đổi snapshots. `shop_name` response lấy tên shop hiện tại vì schema không có cột snapshot tên shop; không thêm cột hoặc tuyên bố có snapshot đó.

## Chạy và kiểm tra

Root VS Code Terminal, PostgreSQL hiện hữu đang chạy:

```powershell
docker compose build backend frontend
docker compose up -d --no-deps --wait backend frontend
```

Swagger http://localhost:8000/docs có Buyer checkout. Cookie/CSRF/Origin vẫn bắt buộc; Swagger khác origin không bypass guard. Dùng HTTP client giữ cookie theo [auth-development.md](auth-development.md), đọc giỏ/địa chỉ, rồi gọi endpoint. Một lần201 tạo đơn và giảm tồn thật; kiểm thử tự động phải dùng DB test riêng.

```powershell
cd backend
uv run --locked ruff check app tests
uv run --locked ruff format --check app tests
uv run --locked pytest -q
```

Integration `test_checkout_postgres.py` chỉ ghi PostgreSQL16 riêng tên marketplace_test qua MARKETPLACE_TEST_DB_*, không volume/credential DB thật. Thiếu env thì SKIP, không gọi PASS. Có tranh tồn cuối, cùng key nhiều app instances, key scope buyer, rollback giữa chừng/commit, serialization retry, snapshot/replay sau xóa địa chỉ/đổi product, numeric overflow và đổi shop/price/stock/category/cart khi giữ khóa. DDL/fixtures chỉ ở DB test đã guard; DB hiện hữu audit metadata READ ONLY.

UI giữ key qua timeout/reload, proxy checkout Next và nút đặt hàng đã có ở P5-03; xem checkout-ui.md. HTTPS/gateway public/load testing/AWS chưa nằm trong task này.
