# P4-02 — Phân quyền và quyền sở hữu

Backend dùng JWT để nhận user ID; role/status luôn lấy lại từ PostgreSQL ở mỗi request. Không lưu quyền trong process hoặc tin role do client/JWT gửi. `Principal` chỉ chứa thông tin tài khoản theo contract, không password_hash. Một USER có thể đồng thời là Buyer và owner shop; không thêm role SELLER vào schema.

## Các lớp code

- `backend/app/api/dependencies.py`: xác thực subject, CSRF, transaction và dependency cho route.
- `backend/app/repositories/access.py`: SELECT có điều kiện owner ngay trong SQL, không commit.
- `backend/app/services/access.py`: quy tắc role/status/shop/ownership, trả ID được phép hoặc lỗi.
- `AuthService.me`: dùng cùng AccessPolicy để kiểm tra tài khoản hiện tại và tạo response profile. API catalog vẫn public.

## Ma trận thực thi

| Policy | Điều kiện |
| --- | --- |
| `buyer()` | Chỉ USER ACTIVE; ADMIN trả403 COMMERCE_FORBIDDEN, kể cả phiên cũ hoặc tài nguyên đã có |
| `admin()` | ADMIN ACTIVE theo database hiện tại |
| `owned_shop()` / `shop(id)` | Owner ACTIVE, hồ sơ shop mình ở mọi trạng thái; ID khác trả404 |
| `selling_shop()` | Owner ACTIVE và shop APPROVED |
| `seller_product(id)` | Product thuộc shop mình, shop APPROVED; dùng cả trước thao tác ảnh/tồn theo product |
| `seller_shop_order(id)` | Đơn shop thuộc shop mình; APPROVED hoặc LOCKED để xử lý đơn cũ |
| `address/cart/order(id)` | SQL đối chiếu user_id/buyer_user_id hiện tại |
| `buyer_shop_order(id)` | Join orders và kiểm buyer_user_id; không dựa vào shop ID client |

Thiếu/sai/hết hạn JWT:401. Token hợp lệ nhưng user không tồn tại:401. User LOCKED:403 USER_LOCKED trên mọi protected action. Thiếu quyền chức năng/không sở hữu shop:403 FORBIDDEN. Shop chưa được bán:403 SHOP_NOT_APPROVED. Resource không tồn tại hoặc của người khác:404 NOT_FOUND cùng nội dung, không tiết lộ owner. Admin không được bypass ownership Buyer/Seller; quản trị dùng API riêng trong P7.

## Cách gắn vào API sau này

GET dùng `ReadAccess` hoặc `Depends(require_admin)` / `Depends(require_buyer)`. Ví dụ phần thân service đọc đơn:

```python
authorized_id = access.order(order_id)
# Repository đọc đơn bằng authorized_id và buyer_user_id của access.principal.
```

`ReadAccess` mở PostgreSQL READ ONLY transaction. Mutation dùng `WriteAccess`, sau đó gọi policy cụ thể ngay trong transaction đã mở:

```python
def update_shop_product(product_id: int, access: WriteAccess):
    authorized_id = access.seller_product(product_id)
    # Service validate và update theo authorized_id + shop_id trong cùng session.
```

Đây là mẫu tích hợp, không phải endpoint đã mở. `WriteAccess` yêu cầu JWT + CSRF/Origin, khóa row user rồi shop khi policy cần shop; transaction được giữ xuyên suốt kiểm quyền và thao tác. Các alias dùng `Depends(..., scope="function")` để commit/rollback hoàn tất trước khi trả response. Service được tích hợp phải dùng cùng `access.repository.session`, không `session.begin()` lồng hoặc commit sớm; repository không commit. Gặp lỗi commit trả503 sanitized, không trả200 trước commit. READ dependency không mutation; không dùng require_admin/read dependency làm guard duy nhất cho POST.

Các task checkout/catalog mutation sau này vẫn phải khóa danh mục/shop/product/inventory theo docs/architecture.md và kiểm tồn/giá/state machine. Nếu cần khóa danh mục thì lấy sau user và trước khi gọi shop policy. Ownership guard không thay thế kiểm transition đơn, tồn kho, idempotency hoặc liên kết child ID. Khi API nhận cả parent/child ID phải query child theo đúng parent đã được kiểm quyền; không dùng ID child toàn cục. Không suy ra quyền nhận đơn mới cho shop LOCKED từ quyền xử lý đơn cũ.

## Kiểm thử và chạy

```powershell
cd backend
uv lock --check
uv run --locked ruff check app tests
uv run --locked ruff format --check app tests
uv run --locked pytest -q
```

Không có MARKETPLACE_TEST_DB_* thì integration tests SKIPPED. Để chạy đầy đủ phải dùng PostgreSQL16 riêng tên marketplace_test, không gắn named volume/dữ liệu hiện hữu. Task này đã chạy full111 PASS với tmpfs riêng và kiểm schema thực READ ONLY; container test được xóa sau mỗi lần chạy. Test-only `/probe/*` chỉ khai báo trong test app, không đăng ký router production.

Coverage gồm role401/403, buyer/seller truy cập chéo user/shop trả404, Admin không bypass, đơn nhiều shop chung một order, status shop APPROVED/PENDING/REJECTED/LOCKED, user bị khóa và role bị đổi sau JWT, user không tồn tại, CSRF, rollback và lỗi commit trả503 trước response. Các task dashboard/CRUD/state transition/checkout chưa được triển khai ở đây.

Từ root để cập nhật ứng dụng:

```powershell
docker compose build backend
docker compose up -d --no-deps --wait backend
```

Swagger http://localhost:8000/docs hiện vẫn có catalog và Authentication, chưa có dashboard endpoints. `/auth/me` dùng policy chung; khi có cookie hợp lệ sẽ đọc role/status/owned_shop mới nhất. Nếu chưa có MARKETPLACE_JWT_SECRET thì auth503 như P4-01; xem auth-development.md để cấu hình tại máy bạn. Không tạo account/Admin hoặc đổi role trên database thật để thử. Frontend http://localhost:3001 giữ nguyên, UI auth thuộc P4-03.
