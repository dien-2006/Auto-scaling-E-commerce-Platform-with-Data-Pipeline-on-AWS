> Cập nhật P4-03: frontend auth và same-origin proxy đã được triển khai. Xem auth-ui.md cho luồng trình duyệt và cấu hình hai service. Các mô tả “chưa có frontend” bên dưới là trạng thái P4-01.

**Cấu hình hiện tại:** chỉ dùng `.env` ở thư mục gốc; xem [hướng dẫn gộp env và Docker release](docker-release.md). Các tên env theo service trong phần lịch sử không còn được Compose đọc.

# P4-01 — Authentication backend

Đã có API backend; frontend đăng ký/login sẽ nối ở P4-03 sau policy P4-02. Chưa có giỏ/checkout nghiệp vụ. Không tạo Admin qua public endpoint. Database dùng users/shop hiện hữu, không thay SQL hoặc seed.

## Chạy và cấu hình

Docker Compose đọc khóa riêng từ `.env`. File này bị Git và Docker build context bỏ qua, chỉ service backend nhận khóa. Không đặt khóa trong root `.env` vì service PostgreSQL cũng nạp toàn bộ file đó. Backend chạy trực tiếp ngoài Docker vẫn nhận `MARKETPLACE_JWT_SECRET` qua environment như trước.

Máy local hiện tại đã được cấu hình khóa trong task FIX-AUTH-01; không cần tạo lại. Khi thiết lập máy mới, từ root trong VS Code Terminal:

```powershell
python -c "import pathlib,secrets; pathlib.Path('.env').open('x').write('MARKETPLACE_JWT_SECRET='+secrets.token_urlsafe(48)+'\n')"
```

Lệnh dùng chế độ `x` nên từ chối ghi đè nếu file đã tồn tại; không in khóa ra terminal. Không commit/gửi khóa qua chat. `MARKETPLACE_PUBLIC_ORIGIN` mặc định `http://localhost:3001`; mở đúng URL này, không dùng `127.0.0.1` hoặc cổng khác nếu chưa đồng bộ cấu hình. Không thay POSTGRES_* đã có, không chép đè root .env bằng .env.example. Khóa tối thiểu32 ký tự random; issuer mặc định marketplace, audience marketplace-web, TTL cố định15 phút. Mọi replica phải dùng cùng khóa/issuer/audience. Thay khóa làm token cũ mất hiệu lực.

```powershell
docker compose build backend
docker compose up -d --no-deps --wait backend
```

Không cần restart postgres hoặc frontend. Thiếu khóa: GET auth/csrf503 AUTH_NOT_CONFIGURED, catalog/health vẫn dùng được. Không hiển thị khóa trong lệnh Compose config/log. Chạy trực tiếp backend: export biến env từ backend/.env.example rồi `uv sync --locked`, `uv run --locked uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log`. Settings không tự đọc root .env khi chạy uv.

## API và cách thử

Swagger http://localhost:8000/docs có Authentication. Không thử tạo user trên DB hiện hữu nếu chỉ muốn kiểm tra UI; suite tự dùng DB riêng. Để tự tạo tài khoản thật, dùng client cookie và gửi JSON register email,password,full_name,phone tùy chọn. Password đăng ký9–128 ký tự, có A–Z/0–9/ký tự đặc biệt (punctuation/symbol), không trim; login kiểm hash cũ không ép complexity mới. Role/status/owner gửi từ client bị422.

Lấy CSRF bằng PowerShell (sau khi tự cấu hình khóa):

```powershell
$csrfResult = Invoke-RestMethod http://localhost:8000/api/v1/auth/csrf -SessionVariable authSession
$authHeaders = @{ Origin='http://localhost:3001'; 'X-CSRF-Token'=$csrfResult.data.csrf_token }
```

POST register:201 {data:UserPrivate}, chưa login; POST login email/password:200 {data:UserPrivate}, set HttpOnly access-cookie và readable CSRF-cookie, không trả JWT JSON. Giữ `$authSession` qua `-WebSession $authSession`, gửi `$authHeaders` và `-ContentType application/json`. Sau login gọi GET auth/csrf lại để cập nhật token rồi POST logout. GET auth/me gửi cookie trả thông tin tài khoản + owned_shop ID/status, không password_hash. Logout204 không body, clear cookies, kể cả khi JWT hết hạn. Token bị sao chép vẫn có hiệu lực tới exp nếu user ACTIVE; chưa refresh/revocation store.

Frontend origin3001 và backend8000 khác origin: Swagger Try it out dùng Origin8000 nên unsafe request sẽ bị CSRF403 nếu không phù hợp PUBLIC_ORIGIN. Đây là hành vi đúng. P4-03 sẽ có proxy same-origin và auth UI; không thêm wildcard CORS/bypass để thử. GET csrf200 không chứng minh DB/auth login thành công. Kiểm thử thực tế trong task dùng TestClient và PostgreSQL16 riêng.

## Source và kiểm thử

`core/security.py` hash/JWT/CSRF/cookie; `schemas/auth.py` input/output validation; `repositories/users.py` SQLAlchemy query; `services/auth.py` explicit transaction/rollback/registration/login/me; `api/v1/routers/auth.py` HTTP. Ví dụ cookie:

```python
response.set_cookie(self.access_cookie, access, max_age=ACCESS_SECONDS, path="/",
                    secure=self.secure, httponly=True, samesite="lax")
```

Frontend hiện chỉ có panel login/register và preview giỏ; backend trong Docker kết nối postgres:5432, server giữ secrets. Auth endpoints không tạo schema. Unit tests không cần DB; integration chỉ chạy khi MARKETPLACE_TEST_DB_NAME=marketplace_test và DB host/port/user/password chỉ tới PostgreSQL riêng không dùng volume thật. Schema test tạo trong DB riêng, container phải được dọn sau test. Không export credentials DB thật thành TEST_DB_*.

```powershell
cd backend
uv lock --check
uv run --locked ruff check app tests
uv run --locked ruff format --check app tests
uv run --locked pytest -q
```

Không cấu hình test/audit env thì integration SKIPPED; không gọi skipped là PASS. Full task run95 PASS gồm DB test riêng và audit READ ONLY. Production public rollout cần rate limit tại shared gateway/store và HTTPS; chưa có rate limiter trong process.

## FIX-AUTH-02 — localhost và LAN

Khi public origin là IP LAN, Compose bổ sung đúng http://localhost:3001 vào MARKETPLACE_ADDITIONAL_ORIGINS của cả hai app. Backend/proxy đều kiểm exact allowlist và token/cookie binding; không wildcard hoặc trust Host request. Production phải dùng [] hoặc origin HTTPS. Cookie host-only nên mỗi địa chỉ đăng nhập riêng. Xem [mobile-local.md](mobile-local.md).
