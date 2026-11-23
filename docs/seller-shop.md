# P6-01 — Đăng ký và quản lý hồ sơ gian hàng

**ADMIN-COMMERCE-01:** ADMIN bị chặn bằng403 COMMERCE_FORBIDDEN ở API giỏ/địa chỉ/đơn Buyer/checkout và hồ sơ đăng ký shop. Chỉ USER ACTIVE dùng các luồng này. Giữ nguyên dữ liệu cũ; quy tắc mới thay thế các ví dụ lịch sử cho Admin mua hàng hoặc tạo shop bên dưới.


Trang `/kenh-nguoi-ban` có đăng ký shop mới, xem hồ sơ và cập nhật tên/mô tả/email liên hệ. UI-15 đã đổi header **Kênh người bán** thành link mở form trực tiếp hoặc vào từ trang Tài khoản; guest thấy form trước, Tiếp tục chuyển đăng nhập rồi quay lại đúng trang. User có shop tiếp tục dashboard hiện tại. Thiết kế mới/slug gợi ý/SĐT account readonly xem [seller-registration-ui.md](seller-registration-ui.md). Đây là API/UI thật; chưa có quản lý sản phẩm, tồn kho, đơn bán hoặc màn hình duyệt Admin trong task này.

## Kết nối và quyền sở hữu

Browser → Next same-origin `/api/v1/seller/shop` → FastAPI qua INTERNAL_API_URL → PostgreSQL `marketplace`. Trong Docker backend dùng `postgres:5432`. Proxy chỉ cho GET/POST/PATCH tới endpoint cố định, cấm query, lọc cookies, no-store, timeout; POST/PATCH cần Origin/Referer và CSRF hợp lệ. Body seller tối đa32KiB để chứa mô tả5.000 ký tự UTF-8; giới hạn auth/cart/address vẫn8KiB. Không JWT trong JSON/browser storage hoặc secrets trong bundle.

AccessPolicy kiểm JWT và đọc user role/status hiện tại. Seller là chủ shop, không thêm role SELLER: USER/ADMIN ACTIVE đều có thể sở hữu một shop của chính mình và vẫn mua hàng. ADMIN không có quyền impersonate shop người khác qua các API này. Không nhận owner/shop ID qua route hoặc mutation payload.

Repository `backend/app/repositories/seller_shop.py` giới hạn chủ sở hữu ở SQL:

```python
query = select(Shop).where(Shop.owner_user_id == self.owner_id)
if write:
    query = query.with_for_update()
```

GET chạy ReadAccess transaction READ ONLY. POST/PATCH chạy WriteAccess khóa user trước, sau đó khóa shop theo ownership; transaction commit trước khi gửi response. POST tạo shop với owner từ principal và trạng thái PENDING do server đặt. Unique owner và unique slug có sẵn trong SQL là hàng rào cuối, không thay schema/index. Đăng ký đồng thời cùng owner chỉ một request201, request còn lại409 SHOP_EXISTS; khác owner trùng slug409 SLUG_EXISTS. Không lock/idempotency nghiệp vụ trong bộ nhớ process. PATCH giữ owner/slug/status/logo, cập nhật updated_at từ giờ database và refresh response.

## Contract đã triển khai

| API | Input | Kết quả |
| --- | --- | --- |
| GET /api/v1/seller/shop | Không | 200 ShopPrivate của mình ở mọi trạng thái; chưa có shop404 NOT_FOUND |
| POST /api/v1/seller/shop | shop_name,shop_slug,description?,contact_email? | 201 ShopPrivate PENDING; đã có shop409 SHOP_EXISTS; slug trùng409 SLUG_EXISTS |
| PATCH /api/v1/seller/shop | shop_name?,description?,contact_email? | 200 ShopPrivate; chưa có shop404; ít nhất một field chỉnh sửa |

Response `{data:{shop_id,owner_user_id,shop_name,shop_slug,description,contact_email,logo_url,shop_status,created_at,updated_at}}`. IDs là string BIGINT; timestamps UTC. Không raw logo_key/password/email tài khoản khác. Contact email và owner chỉ xuất hiện trong private contract; public shop vẫn giữ projection cũ. logo_url hiện null, không giả ảnh hoặc mở upload logo ngoài contract.

- shop_name trim, nonblank1..150 ký tự.
- shop_slug trim,1..160 ký tự ASCII chữ thường/số, phân cách bằng một dấu gạch nối; ví dụ `an-nhien-beauty`. Không cho slash/uppercase/khoảng trắng/double dash. Slug cố định sau đăng ký; không đổi slug shop hiện có.
- description nullable, tối đa5.000 ký tự, trim và hiển thị plain text; contact_email nullable, EmailStr hợp lệ tối đa255. UI gửi null khi xóa hai trường tùy chọn. PATCH shop_name=null hoặc body rỗng422.
- Mutation unknown fields đều422: owner_user_id/shop_id/shop_status/user_role/logo_key/logo_url/slug trong PATCH không được mass assign. User LOCKED403; guest401; CSRF sai403; lỗi DB/commit503 đã làm sạch, rollback toàn bộ.
- Chủ shop ACTIVE được xem/sửa hồ sơ PENDING/APPROVED/REJECTED/LOCKED. Sửa hồ sơ không tự approve/resubmit/unlock; chỉ APPROVED hiện link shop công khai và được bán theo nghiệp vụ. Trang public của trạng thái khác vẫn404.

Schemas/service/router: `backend/app/schemas/seller_shop.py`, `services/seller_shop.py`, `api/v1/routers/seller_shop.py`. Frontend `components/seller/shop-dashboard.tsx`, `lib/seller-shop-client.ts`, page `app/kenh-nguoi-ban/page.tsx`, Next `app/api/v1/seller/shop/route.ts`; proxy trong auth-proxy.ts, login return allowlist trong auth-contract.ts.

## Giao diện và phục hồi lỗi

Workspace xanh nhạt đồng bộ coco, sidebar các link đã có, form có labels/validation/disabled, thông tin riêng cho bốn trạng thái, loading/empty/error/retry, responsive. Chưa có shop chỉ kết luận sau GET404 thực; lỗi503 không biến thành form shop mới. Frontend kiểm owner ID/enum/BIGINT/timestamps và project field an toàn trước hiển thị; state không chuyển sang account khác sau unmount/expiry.

Submit có ref guard và disabled để chặn gửi đôi. Sau response201/200 hợp lệ mới cập nhật hồ sơ, báo thành công và refresh session để owned_shop hiện trên tài khoản. Mất response/503 hoặc SHOP_EXISTS yêu cầu tải lại hồ sơ trước khi ghi tiếp; GET đối chiếu được shop đã commit. Không tự retry POST/PATCH hoặc khẳng định request thất bại đồng nghĩa DB chưa lưu. Một shop/owner tại database vẫn bảo vệ nếu reload hoặc gửi lại. PATCH chưa có optimistic version/ETag: hai chỉnh sửa hợp lệ serialize theo khóa; cùng field sẽ giữ giá trị request được xử lý sau. Không hứa phát hiện mọi thay đổi stale giữa nhiều tab.

## Kiểm thử

PASS250 backend tests toàn bộ với PostgreSQL16 tmpfs marketplace_test riêng, audit metadata hiện hữu READ ONLY;29 trường hợp mới: GET READ ONLY/private projection, tạo PENDING/unique owner, cả4 status/nullable patch, cross-owner/ADMIN không bypass, guest/locked/CSRF/hostile origin, mass assignment/validation, hai app đăng ký đồng thời cùng owner hoặc cùng slug, rollback create/patch khi commit lỗi. Public không lộ private email/owner/logo key. Ruff check/format PASS; không dependency/lock changes.

PASS44 frontend tests, lint/typecheck/build: projection theo owner/enum/ID/private key; input bounds/slug/login return URL; proxy fixed route/method/query/Origin/CSRF/cookie/body limit; GET404 khác503; mutation allowlist, không đổi slug ở PATCH, không tự retry khi mất response.

PASS Chrome E2E Next production→FastAPI→PostgreSQL16 riêng: guest→login UI→return đúng seller, đăng ký chỉ1POST khi submit đôi, chỉnh/xóa nullable/reload giữ dữ liệu, bốn trạng thái/link shop APPROVED, slug trùng và tạo shop khác độc lập, owner/status injection422, mất response sau real commit→đọc lại shop, API503/error/retry, khóa user/expiry không lộ hồ sơ. Responsive320/390/768/1440 không overflow/JS errors; đã xem ảnh desktop/mobile. Chỉ test fixture đổi status trong test DB; không thay thế hoặc khẳng định Admin API đã làm. Test processes/container đã dọn. HTTPS/gateway/load chưa kiểm chứng.

## Chạy và kiểm tra

Từ root repository trong VS Code Terminal:

```powershell
docker compose build backend frontend
docker compose up -d --no-deps --wait backend frontend
```

1. Mở http://localhost:3001/kenh-nguoi-ban, đăng nhập bằng tài khoản của bạn.
2. Nếu chưa có shop, nhập tên và đường dẫn như `ten-shop-cua-ban`, mô tả/email tùy chọn, bấm Đăng ký gian hàng. **Thao tác này tạo shop thật** cho tài khoản; không cần seed hoặc chạy SQL.
3. Sau đăng ký hiển thị Chờ phê duyệt. Sửa hồ sơ rồi reload để đối chiếu. Slug chỉ đọc; không có nút tự phê duyệt. Việc duyệt sẽ có ở P7-02, không tự sửa SQL trạng thái để demo trên DB thật.
4. Swagger http://localhost:8000/docs có nhóm Seller shop. Đăng nhập auth API cùng origin để dùng cookie; POST/PATCH cần CSRF lấy từ auth/csrf và Origin hợp lệ. Thử payload thêm shop_status/owner_user_id phải422; cùng tài khoản đăng ký lại409.
5. Không tạo shop thử trên DB thật chỉ để kiểm tra nếu bạn chưa định đăng ký. Empty/loading/error và protected responses vẫn kiểm tra được bằng GET.

Frontend checks từ frontend với Node24: `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build`. Backend từ backend: `uv run --locked ruff check .`, `uv run --locked ruff format --check .`, `uv run --locked pytest -q`; PostgreSQL fixtures cần MARKETPLACE_TEST_DB_* trỏ DB test riêng marketplace_test theo backend/README.md, không trỏ DB ứng dụng.

P6-02 quản lý sản phẩm Seller là task tiếp theo; ảnh/tồn/đơn bán và Admin vẫn theo checklist, chưa tự triển khai trong P6-01.
