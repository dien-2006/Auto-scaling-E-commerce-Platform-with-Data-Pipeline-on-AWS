# P4-03 — Đăng ký, đăng nhập, đăng xuất và tài khoản

**Cấu hình hiện tại:** chỉ dùng `.env` ở thư mục gốc; xem [hướng dẫn gộp env và Docker release](docker-release.md). Các tên env theo service trong phần lịch sử không còn được Compose đọc.

## Trang và hành vi

- `/dang-ky`: họ tên, email, phone tùy chọn, password9–128 ký tự có A–Z/0–9/ký tự đặc biệt và xác nhận. Khoảng trắng password được giữ nguyên, email/họ tên/phone trim. Email/password/required fields có browser validation và backend validation. Không nhận role/status/owner từ form. Thành công chuyển tới login, không tự đăng nhập.
- `/dang-nhap`: email/password, hiện/ẩn mật khẩu, loading, lỗi API tiếng Việt. Login thành công gọi me rồi chuyển đến `returnTo` đã kiểm tra (mặc định `/tai-khoan`). Không tự retry mutation khi timeout.
- `/tai-khoan`: thông tin riêng từ API me, role và trạng thái owned_shop; loading/error/guest/retry. Không có dữ liệu cá nhân trong SSR props/static cache. Đây là trang đọc profile, chưa có sửa profile/địa chỉ/dashboard.
- Header có Đăng ký/Đăng nhập khi guest; khi authenticated có tên user (link tài khoản) và Đăng xuất. Logout gọi API có CSRF, clear cookie tại backend rồi xóa state và về trang chủ. Lỗi logout giữ thông báo và không giả thành công. Session kiểm lại khi tab visible và mỗi60s khi tab mở; backend vẫn kiểm quyền/status mỗi protected request.

`returnTo` chỉ chấp nhận các route nội bộ có sẵn, không protocol-relative URL, backslash/control character, /api, auth loops hoặc URL ngoài. Không chứa JWT trong URL, localStorage/sessionStorage hay JSON response. Profile phía client chỉ giữ state trong bộ nhớ và projection đúng contract, không hash/token/owner fields.

## Kết nối

Browser → `/api/v1/auth/{csrf,register,login,logout,me}` trên Next → `INTERNAL_API_URL` cố định → FastAPI → PostgreSQL qua hostname postgres khi Docker. Backend là nguồn xác thực và phân quyền P4-01/02.

Proxy route chỉ cho phép đúng5 endpoints/method, không query tùy ý, không arbitrary upstream URL/redirect; giới hạn body8KiB, timeout15s, no-store. Chỉ forward auth cookies, Origin/Referer, CSRF và request ID hợp lệ; không forward Authorization/analytics cookies. Set-Cookie auth giữ nguyên HttpOnly/Secure/SameSite/Path và header nhiều cookie riêng. Origin unsafe phải khớp MARKETPLACE_PUBLIC_ORIGIN; backend kiểm CSRF signature/session-binding lần nữa. Client lấy csrf mới trước mỗi POST; không đọc JWT.

Source chính:

- `frontend/src/lib/auth-proxy.ts` và `app/api/v1/auth/[endpoint]/route.ts`.
- `lib/auth-contract.ts` (account projection/return URL), `lib/auth-client.ts`.
- `components/auth/{auth-form,session-provider,header-auth,account-panel}.tsx`.
- Routes dang-nhap/dang-ky/tai-khoan; root layout bọc SessionProvider.

## Chạy local

Compose đã bổ sung duy nhất MARKETPLACE_PUBLIC_ORIGIN vào frontend; INTERNAL_API_URL vẫn http://backend:8000. Không thêm JWT secret vào frontend. Root .env/database config giữ nguyên.

Nếu chưa cấu hình khóa JWT, các trang vẫn mở nhưng submit báo “Đăng nhập chưa sẵn sàng”. FIX-AUTH-01 đã bật auth trên máy hiện tại bằng file riêng `.env`; máy mới tạo file theo [auth-development.md](auth-development.md), không gửi khóa qua chat/commit. Không đặt khóa trong root .env vì PostgreSQL cũng nạp file đó. Hai service dùng cùng MARKETPLACE_PUBLIC_ORIGIN, mặc định http://localhost:3001; chỉ backend nhận JWT secret. Khi đổi public origin/port phải đồng bộ hai service.

Từ root:

```powershell
docker compose build frontend
docker compose up -d --no-deps --wait frontend
# Khi bạn vừa cấu hình khóa/origin cho backend:
docker compose up -d --no-deps --wait backend
```

Direct npm dev: dùng Node24, copy frontend/.env.example sang .env.local trên máy; INTERNAL_API_URL=http://localhost:8000, MARKETPLACE_PUBLIC_ORIGIN trùng URL frontend. Ví dụ `npm run dev -- --port 3001`. Không chép đè root .env hoặc đổi POSTGRES_*.

## Kiểm tra

Mở http://localhost:3001/dang-ky, tạo tài khoản bạn muốn sử dụng, kiểm tra chuyển sang login; đăng nhập, xem tài khoản/tên header, reload rồi đăng xuất. Khi tự submit register với cấu hình thật, API tạo tài khoản thật; không tạo account test trong DB hiện hữu chỉ để xem UI. Swagger http://localhost:8000/docs có Authentication; cookie qua proxy cùng host và CSRF/Origin vẫn bắt buộc khi gọi unsafe API trực tiếp.

DevTools Application: access cookie HttpOnly, không xuất hiện trong document.cookie/localStorage/sessionStorage. Cookie csrf readable dùng cho double submit. Login/register không nhận Admin từ client; role chỉ do DB quản lý. Production dùng HTTPS và __Host cookies theo backend, proxy giữ attrs; chỉ local HTTP flow được browser-E2E kiểm chứng trong task này.

```powershell
cd frontend
npm run test
npm run lint
npm run typecheck
npm run build
```

Task validation:24 frontend unit/contract tests PASS; lint/typecheck/build PASS. Real browser E2E chạy Next production + FastAPI + PostgreSQL16 tmpfs riêng: register/login/logout/me, confirm mismatch/email duplicate/wrong password, cookie reload/HttpOnly, CSRF hostile origin, expired session, safe return URL, no browser token storage; responsive320/390/768/1440 không overflow/JS errors. Screenshot desktop/mobile đã xem. Test container/process được dọn, không ghi DB thật. Docker live kiểm3 pages200, missing-secret error và proxy403; không gửi mutation tới backend do csrf503. Frontend healthy, PostgreSQL ID/start/mount/config/env/network/volume giữ nguyên.

Không tự triển khai P4-04 địa chỉ, P5 giỏ/checkout hoặc dashboard P6/P7. Các preview giỏ/checkout vẫn là preview. Khóa JWT và rate limit shared gateway trước public rollout vẫn theo P4-01; logout chưa có revocation/refresh token.


## UI-10 — Cập nhật thiết kế

Auth pages dùng SiteFrame với header riêng, không storefront header/footer; form giữa nền xanh và SVG túi/quà/coupon hai bên. Mobile bỏ artwork hai bên, giữ input/label/focus/loading/error đầy đủ. /tai-khoan và các trang mua sắm giữ chrome cũ. API/CSRF/JWT/validation/returnTo P4-03 không đổi. Giữ đăng nhập email; chưa OTP/phone-login/OAuth/reset-password. Lint/typecheck/build,24 tests và E2E PostgreSQL16 riêng PASS. Ctrl+F5 ở /dang-nhap hoặc /dang-ky để xem.
