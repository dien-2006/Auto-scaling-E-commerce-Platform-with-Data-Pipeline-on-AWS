# P5-04 — Lịch sử và chi tiết đơn Buyer

**ADMIN-COMMERCE-01:** ADMIN bị chặn bằng403 COMMERCE_FORBIDDEN ở API giỏ/địa chỉ/đơn Buyer/checkout và hồ sơ đăng ký shop. Chỉ USER ACTIVE dùng các luồng này. Giữ nguyên dữ liệu cũ; quy tắc mới thay thế các ví dụ lịch sử cho Admin mua hàng hoặc tạo shop bên dưới.


Đã có API thật và giao diện `/tai-khoan/don-hang`, `/tai-khoan/don-hang/{order_id}`. Vào từ Tài khoản → Lịch sử đơn hàng hoặc liên kết Theo dõi đơn hàng sau checkout. Không cần tạo lại database/schema; không seed dữ liệu để làm đầy giao diện.

Cập nhật P6-05 (11/11/2026): chi tiết đơn mua đã có **Hủy đơn shop** cho PENDING, kèm xác nhận và hoàn tồn một lần. Sau lỗi/mất phản hồi cần tải lại đơn để xác minh; không tự gửi lặp. Không hủy shop khác hoặc đơn đã CONFIRMED/SHIPPING/COMPLETED. Chi tiết API/transaction và kiểm chứng mới nhất tại [seller-orders.md](seller-orders.md); phần dưới ghi nền tảng P5-04.

## Kết nối và quyền

Browser gọi Next same-origin `/api/v1/orders` hoặc `/api/v1/orders/{id}`. Proxy giới hạn GET, ID BIGINT dương và query page/page_size; chuyển cookie xác thực được cho phép, không Authorization tùy ý. Next gọi FastAPI qua INTERNAL_API_URL; backend trong Docker truy cập PostgreSQL `postgres:5432`. JWT HttpOnly không được đưa vào JSON hoặc browser storage.

FastAPI dùng ReadAccess, transaction READ ONLY và AccessPolicy kiểm user ACTIVE/role hiện tại trong database. OrderRepository luôn giới hạn `buyer_user_id` theo principal, kể cả ADMIN. Đơn người khác và ID không tồn tại cùng trả404 NOT_FOUND. Không có quyền xem đơn người khác qua query hoặc sửa ID trên giao diện.

Code trọng tâm trong `backend/app/repositories/orders.py`:

```python
return self.session.scalar(
    select(Order).where(Order.order_id == order_id, Order.buyer_user_id == self.buyer_id)
)
```

Service/router: `backend/app/services/orders.py`, `backend/app/api/v1/routers/orders.py`. Schemas: `backend/app/schemas/orders.py`; chi tiết dùng chung OrderDetailData hiện có. CheckoutRepository kế thừa phần dựng detail từ OrderRepository để checkout và xem đơn có cùng projection/snapshot.

## API và dữ liệu

- GET `/api/v1/orders?page=1&page_size=24`: `{items:OrderSummary[],page,page_size,total}`. Mặc định24, size1..100, page1..2147483647; unknown query422. Thứ tự created_at DESC, order_id DESC. Trang quá cuối trả rỗng với total đúng; không coi lỗi503 là danh sách rỗng. Frontend dùng12 đơn/trang.
- GET `/api/v1/orders/{id}`: `{data:OrderDetail}`. ID dương đến9223372036854775807. Có snapshot người nhận, điện thoại, shipping_address và các sản phẩm theo từng shop. Backend trả tiền Decimal string, ID string, thời gian UTC. Frontend kiểm projection, enum, ID, arithmetic bằng BigInt trước hiển thị.
- Không có trạng thái tổng giả: mỗi shop_order có PENDING/CONFIRMED/SHIPPING/COMPLETED/CANCELLED riêng. Tổng tiền/subtotal là giá trị đơn đã ghi nhận, không tự tính lại từ catalog hoặc loại đơn shop đã hủy. Chỉ COD mô phỏng, không khẳng định đã thanh toán.
- Snapshot tên/giá sản phẩm và địa chỉ đến từ orders/order_items, không join Product/Address hiện tại. Shop name là tên hiện tại vì schema chưa có snapshot shop_name. Shop bị khóa, sản phẩm ẩn hoặc địa chỉ bị xóa không làm mất lịch sử.
- List không trả người nhận/điện thoại/địa chỉ/line items. Không endpoint nào trả buyer ID, idempotency_key, owner/email riêng, hash hoặc storage key. Cache-Control:no-store; proxy thêm Vary:Cookie. Không lưu lịch sử hoặc detail vào sessionStorage/localStorage, không cache riêng tư ở SSR.
- Query số lượng cố định: list có3 SELECT sau principal (count/page/all shop summaries), detail có3 SELECT sau principal (owned order/all shops/all items), không N+1. Offset pagination không cam kết snapshot cố định giữa nhiều request khi có đơn mới.

Frontend: `components/orders/buyer-orders.tsx`, `lib/orders-client.ts`, Next route handlers `app/api/v1/orders/*`, pages `app/tai-khoan/don-hang/*`. Loading/empty/error/retry, cập nhật trạng thái bằng GET, login returnTo và giao diện responsive. Request cũ bị abort khi unmount/thay account/page, kết quả riêng tư không chuyển sang account khác.

P5-04 chỉ đọc/theo dõi đơn. Endpoint hủy Buyer và state machine/hoàn tồn tiếp tục được theo dõi ở P6-05 để kiểm thử cùng xử lý đơn Seller; chưa có nút hủy giả. Không tích hợp đơn vị vận chuyển, tracking number, thời gian giao dự kiến hoặc dữ liệu trạng thái giả.

## Kiểm chứng

PASS221 backend tests toàn bộ, gồm16 trường hợp mới trên PostgreSQL16 tmpfs riêng: IDOR USER/ADMIN, own ADMIN, guest/locked JWT, nhiều shop/mixed statuses, snapshots khi đổi product/giá/xóa address/khóa shop, pagination tie-break, trang rỗng/validation/READ ONLY/query count/no secrets. Các fixtures chỉ chạy khi database tên marketplace_test, không ghi DB thật. Full suite cũng kiểm lại transaction/replay/concurrency checkout sau khi dùng chung detail repository. Ruff check/format PASS; dependencies/lock không đổi.

PASS40 frontend tests, lint/typecheck/production build; projection Decimal/BIGINT/enum/private extras, fixed proxy route/method/query/cookies, lỗi không thành empty, invalid/mismatched payload.

PASS Chrome E2E Next production → FastAPI → PostgreSQL16 riêng: guest/empty, checkout thật hai shop → detail, cập nhật SHIPPING/CANCELLED bằng test fixture và refetch, snapshot cũ,14 đơn/2 trang không trùng, API503→error→retry, IDOR404 không lộ người nhận, expiry xóa màn hình đơn riêng. Responsive320/390/768/1440 không tràn ngang/JS errors; đã xem ảnh desktop/mobile. Fixtures trạng thái và đơn phân trang chỉ trong test database, không production. Test resources đã dọn. Chưa kiểm HTTPS/gateway/load hoặc Seller chuyển trạng thái qua API (P6-05 chưa làm).

## Chạy và kiểm tra trong VS Code

Từ thư mục repository:

```powershell
docker compose build backend frontend
docker compose up -d --no-deps --wait backend frontend
```

1. Mở http://localhost:3001/tai-khoan/don-hang. Guest thấy yêu cầu đăng nhập; đăng nhập bằng tài khoản của bạn. Chưa có đơn thì empty state thật.
2. Đơn mua thành công xuất hiện theo ngày mới nhất. Bấm Xem chi tiết để xem mã đơn, người nhận, các dòng và trạng thái riêng của từng shop. Cập nhật trạng thái chỉ tải lại dữ liệu server.
3. Swagger http://localhost:8000/docs: đăng nhập qua auth API để cookie cùng origin, rồi GET /api/v1/orders và GET /api/v1/orders/{id}. Thay ID bằng đơn của user khác phải404; guest401. Không cần CSRF cho hai GET.
4. Kiểm tra mobile bằng DevTools. Khi API không sẵn sàng phải báo lỗi và có Thử lại; không hiển thị đơn demo.

Chạy checks frontend từ frontend: `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build` với Node24. Backend từ backend: `uv run --locked ruff check .`, `uv run --locked ruff format --check .`, `uv run --locked pytest -q`; các PostgreSQL integration tests cần cấu hình MARKETPLACE_TEST_DB_* trỏ DB test riêng, audit hiện hữu chỉ READ ONLY theo backend/README.md. Không trỏ test fixtures vào DB ứng dụng.
