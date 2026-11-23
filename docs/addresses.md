# P4-04 — Địa chỉ giao hàng

Trang `/tai-khoan/dia-chi` truy cập từ **Tài khoản → Quản lý địa chỉ giao hàng**. Cần đăng nhập bằng tài khoản ACTIVE. Người chưa đăng nhập có liên kết đăng nhập và quay lại đúng trang địa chỉ. Dữ liệu chỉ tải ở client qua API riêng, không nằm trong static HTML, localStorage hoặc sessionStorage.

## Kết nối và code chính

Browser → Next `/api/v1/addresses` → FastAPI → SQLAlchemy → PostgreSQL `marketplace.addresses`. Trong Docker backend kết nối `postgres:5432` qua cấu hình hiện có. Proxy Next chỉ cho GET/POST danh sách và PATCH/DELETE theo BIGINT hợp lệ; chuyển cookie xác thực/CSRF, kiểm tra Origin, giới hạn JSON 8 KiB, timeout và `no-store`. Không nhận target URL từ browser.

- `backend/app/schemas/addresses.py`: trim, giới hạn độ dài, phone, boolean nghiêm ngặt; cấm `user_id` và field ngoài contract. PATCH không rỗng; chỉ ward/district được null để xóa giá trị. `address_line` tối đa 2.000 ký tự là giới hạn API, không đổi kiểu TEXT trong DB.
- `backend/app/repositories/addresses.py`: mọi truy vấn có `user_id` từ principal. Không commit trong repository.
- `backend/app/services/addresses.py`: trả projection không có owner ID; ghi trong transaction của `WriteAccess`. Khóa user trước khi đọc/sửa địa chỉ; xóa cờ mặc định cũ trước khi flush địa chỉ mặc định mới. Các replica cùng PostgreSQL dùng chung khóa và partial unique index đã có; không dùng mutex trong process.

```python
if values.get("is_default") is True:
    self.repository.clear_default()
```

- `frontend/src/components/auth/address-panel.tsx`: danh sách, form thêm/sửa, đặt mặc định, xác nhận xóa, loading/error/empty/retry. Không tự retry mutation khi timeout; tải lại trước khi gửi lại để kiểm tra kết quả chưa rõ.
- `frontend/src/lib/address-client.ts`, `address-contract.ts`: CSRF mới cho mỗi lần ghi, validate response, BIGINT dạng chuỗi.
- `frontend/src/lib/auth-proxy.ts`: phần chuyển tiếp private dùng chung auth/địa chỉ; từng nhóm có allowlist riêng.

## Quy tắc

Tối đa một địa chỉ mặc định cho mỗi tài khoản. Địa chỉ đầu tiên **không tự động** thành mặc định: người dùng chọn rõ ràng. Bỏ cờ hoặc xóa địa chỉ mặc định cho phép không còn mặc định, không tự chọn thay thế. Chỉ chủ địa chỉ được sửa/xóa; Admin không bypass ownership trong API Buyer. Resource thiếu và của người khác đều 404.

Xóa địa chỉ chỉ xóa dòng trong `addresses`; không cập nhật `orders.recipient_name`, `orders.phone`, `orders.shipping_address`. Đơn hàng dùng snapshot theo contract. Task này không triển khai checkout.

## Chạy từ VS Code Terminal

Tại root dự án; PostgreSQL hiện hữu phải đang chạy:

```powershell
docker compose build backend frontend
docker compose up -d --no-deps --wait backend frontend
```

Không khởi tạo lại DB, không chạy SQL Downloads, không seed dữ liệu thật. Nếu auth báo chưa sẵn sàng, cấu hình JWT secret local theo [auth-development.md](auth-development.md); không gửi secret qua chat hoặc chép đè `.env`.

Kiểm thử trực tiếp với tooling đã cài:

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

Integration tests chỉ chạy khi `MARKETPLACE_TEST_DB_*` trỏ PostgreSQL riêng tên `marketplace_test`; không dùng credential/volume DB thật. Chạy pytest không cấu hình DB test sẽ SKIP integration, không phải bằng chứng PASS transaction/concurrency. Các biến audit chỉ phục vụ đọc metadata DB hiện hữu. Test schema chỉ được tạo trong DB test được bảo vệ bởi kiểm tra tên database.

## Kiểm tra thủ công

1. Mở http://localhost:3001/tai-khoan/dia-chi; guest thấy yêu cầu đăng nhập. Đăng nhập rồi quay lại trang địa chỉ.
2. Thêm hai địa chỉ, thử field rỗng/phone sai; chuyển mặc định giữa hai địa chỉ rồi reload. Chỉ một dòng mang nhãn Mặc định.
3. Sửa địa chỉ; xóa có bước xác nhận và có thể giữ lại. Xóa mặc định không tự đổi địa chỉ khác thành mặc định.
4. Swagger http://localhost:8000/docs có nhóm Buyer addresses. GET cần access cookie; POST/PATCH/DELETE còn cần CSRF cookie/header và Origin hợp lệ. Swagger khác origin không tự bỏ qua guard; dùng UI cùng origin hoặc client có cookie theo hướng dẫn auth.
5. PostgreSQL: khi cần đối chiếu, chỉ đọc dòng của tài khoản kiểm tra trong transaction READ ONLY. Không tạo fixture vào DB hiện hữu để chạy test tự động; thử nghiệm tự động dùng DB riêng.

Backend chưa có JWT secret local sẽ từ chối auth; việc kiểm chứng luồng thành công cần cấu hình hợp lệ hoặc môi trường test riêng. HTTPS/gateway public chưa nằm trong task này.
