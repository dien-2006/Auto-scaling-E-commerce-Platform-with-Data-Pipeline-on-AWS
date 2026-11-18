# P5-01 — Giỏ hàng nhiều shop

**Cấu hình hiện tại:** chỉ dùng `.env` ở thư mục gốc; xem [hướng dẫn gộp env và Docker release](docker-release.md). Các tên env theo service trong phần lịch sử không còn được Compose đọc.

`/gio-hang` đã dùng API thật. Trang chi tiết `/san-pham/{product_id}` có chọn số lượng và Thêm vào giỏ; guest đăng nhập rồi quay lại sản phẩm. Header dẫn trực tiếp đến giỏ và đọc số dòng sản phẩm từ API; cập nhật sau thao tác trong cùng tab. Mỗi dòng tương ứng một sản phẩm, số trên header không phải tổng số lượng các đơn vị hàng.

## Kết nối và code chính

Browser → Next same-origin `/api/v1/cart*` proxy → FastAPI → SQLAlchemy → PostgreSQL `marketplace.carts` và `marketplace.cart_items`. Backend trong Docker dùng `postgres:5432` với cấu hình hiện hữu. Không lưu cart, JWT hay địa chỉ vào localStorage/sessionStorage; không cache PII hoặc cart trong static HTML.

- `backend/app/schemas/cart.py`: quantity là integer thật 1..2147483647, không nhận bool/float/string; product ID nhận BIGINT chính xác hoặc chuỗi số, không nhận float/bool; extra fields bị cấm.
- `backend/app/repositories/cart.py`: truy vấn giỏ luôn có owner predicate, một query join cho toàn bộ các dòng/shop/giá/tồn/visibility; không N+1. Dùng cây danh mục public chung với catalog, giữ dòng unavailable để người mua xóa. Không chọn password/email/storage key.
- `backend/app/services/cart.py`: `WriteAccess` khóa user trước, sau đó khóa cart/dòng giỏ; cộng thêm số lượng cho cùng sản phẩm trong một transaction. Unique cart/user và item/cart/product hiện có bảo đảm tính duy nhất; không cần thêm bảng hoặc index. Các request cùng user ở replica khác cùng serialize trên PostgreSQL, không dùng mutex in-memory. Commit xảy ra trước response; exception rollback cả cart mới và item.

```python
target = (item.quantity if item else 0) + quantity
self._validate(product_id, target)
```

- `frontend/src/lib/cart-{contract,client}.ts`: validate response, BIGINT string, tiền kiểm tra bằng BigInt cents; chỉ nhận tổng khớp từng dòng và từng shop. Lấy CSRF trước mutation, không tự retry; event `coco:cart-changed` chỉ là tín hiệu các component tải lại API.
- `frontend/src/components/cart/`: add-to-cart, header-cart, cart-panel, use-cart. Loading/error/empty riêng biệt; cập nhật số lượng có submit rõ ràng; xóa có xác nhận; retry dùng GET. Sau timeout chưa rõ kết quả, tải lại giỏ trước khi thêm lại để tránh cộng trùng. Schema không có idempotency cho cart add; không tuyên bố exactly-once sau mất response.

## API và quy tắc

| API | Ý nghĩa |
| --- | --- |
| GET /api/v1/cart | `{data:{shops:[],total_amount:"0.00"}}` khi rỗng; không tạo cart bằng GET |
| POST /api/v1/cart/items | `{product_id,quantity}` cộng thêm; 200 Cart |
| PATCH /api/v1/cart/items/{id} | `{quantity}` số lượng mục tiêu; 200 Cart |
| DELETE /api/v1/cart/items/{id} | 204; chỉ xóa dòng của mình |

Mọi API yêu cầu user ACTIVE; ghi còn cần CSRF/Origin. Admin chỉ thao tác giỏ chính mình. Thiếu/foreign item đều404. Giỏ một user, nhóm theo shop, mỗi sản phẩm một dòng. Giá/tồn được lấy lại từ DB ở mỗi lần đọc/ghi; không giữ hàng hoặc giảm inventory. Tổng tiền là tạm tính theo giá hiện tại của tất cả dòng, kể cả dòng unavailable; không phải báo giá checkout, không phí/discount giả.

Thêm và đổi số lượng kiểm shop APPROVED, product active, toàn bộ tổ tiên danh mục active, inventory tồn tại/đủ lượng và không self-purchase. Request cộng thêm kiểm **lượng đang có + lượng thêm**, không chỉ lượng thêm. Product hidden/shop không bán/category không public trả404 khi thêm/sửa; self-purchase403; thiếu tồn409 OUT_OF_STOCK. Overflow cộng quantity trả409 CART_CHANGED. Những thay đổi catalog/tồn sau thời điểm kiểm tra có thể làm giỏ unavailable; checkout P5-02 phải kiểm tra và khóa lại, giỏ không thay thế cơ chế chống overselling của checkout.

GET vẫn trả sản phẩm đã có trong giỏ với `is_available:false`, reason rõ: HIDDEN_PRODUCT, SHOP_UNAVAILABLE, CATEGORY_UNAVAILABLE, SELF_PURCHASE, MISSING_INVENTORY, OUT_OF_STOCK, INSUFFICIENT_STOCK. Có thể giảm lượng không đủ tồn xuống lượng hợp lệ, hoặc xóa dòng kể cả khi bị ẩn. Không trả storage key; ảnh đang null có chủ ý như catalog đến khi có delivery S3, dùng placeholder thật.

**Làm rõ giới hạn tiền:** giá mỗi sản phẩm và các cột tiền lưu DB tuân NUMERIC(14,2). Tạm tính giỏ không lưu vào cột NUMERIC nên là tổng Decimal có thể vượt giới hạn đó nếu lượng rất lớn. API không cắt/làm tròn hoặc ghi số này vào orders; frontend dùng BigInt để hiển thị chính xác. Guard tổng đơn trong giới hạn NUMERIC thuộc P5-02. Đây là làm rõ quy ước response dẫn xuất, không đổi schema/SQL.

## Chạy và kiểm tra

Từ root VS Code Terminal, khi PostgreSQL hiện hữu đang chạy:

```powershell
docker compose build backend frontend
docker compose up -d --no-deps --wait backend frontend
```

Mở http://localhost:3001 và http://localhost:8000/docs (nhóm Buyer cart). Auth local dùng khóa riêng `.env`; không đưa khóa vào root .env/frontend. Có thể đăng nhập rồi dùng sản phẩm thật đã có để thêm vào giỏ. Nếu catalog rỗng, giao diện vẫn hoạt động và không tự tạo hàng mẫu; cần tạo sản phẩm hợp lệ ở task Seller/dữ liệu riêng trước khi thử thao tác mua trên DB thật.

1. Guest mở `/gio-hang` có lời mời đăng nhập, không báo nhầm giỏ rỗng do API lỗi.
2. Chi tiết sản phẩm: chọn số lượng, thêm vào giỏ; lặp thêm cùng sản phẩm sẽ cộng lượng vào một dòng. Xem header và mở giỏ.
3. Thêm sản phẩm hai shop, kiểm tra nhóm/subtotal/tạm tính. Thử sửa quantity vượt tồn để nhận thông báo; tải lại trước khi thử lại nếu mất mạng.
4. Xóa có thể giữ lại hoặc xác nhận. Reload trang vẫn lấy giỏ đã lưu DB, không browser storage.
5. P5-03 đã nối nút Tiến hành thanh toán đến `/thanh-toan`: chọn địa chỉ và đặt COD mô phỏng qua API thật. Xem checkout-ui.md; lịch sử đơn thuộc P5-04.

Kiểm thử với Node24/Python3.13/uv:

```powershell
cd backend
uv run --locked ruff check app tests
uv run --locked ruff format --check app tests
uv run --locked pytest -q
cd ../frontend
npm run lint
npm run typecheck
npm test
npm run build
```

Integration cần PostgreSQL16 **riêng** tên `marketplace_test` qua `MARKETPLACE_TEST_DB_*`; không dùng volume/credential DB hiện hữu. Thiếu env sẽ SKIP, không được gọi là PASS. Fixture/concurrency/rollback chỉ ghi DB test; audit metadata DB thật dùng READ ONLY. E2E dùng Next production, backend thật và DB test riêng; sản phẩm test không vào DB đang dùng. Không dùng SQLite để chứng minh concurrency PostgreSQL.
