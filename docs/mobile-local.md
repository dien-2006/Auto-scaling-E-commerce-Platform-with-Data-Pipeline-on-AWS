# Truy cập điện thoại qua mạng LAN

## Cấu hình hiện tại — FIX-MOBILE-AUTH-01 (11/11/2026)

Wi-Fi hiện tại có IP172.18.60.11. Hai app được người dùng mở lại với canonical localhost và additional origins chỉ localhost; điện thoại mở LAN nhận403 CSRF_FAILED ở đăng ký. Đã tái hiện trước sửa và cập nhật đồng bộ runtime backend/frontend bằng exact allowlist, không sửa root.env/Compose/source hoặc bỏ CSRF:

```powershell
$env:MARKETPLACE_PUBLIC_ORIGIN='http://localhost:3001'
$env:MARKETPLACE_ADDITIONAL_ORIGINS='["http://localhost:3001","http://172.18.60.11:3001"]'
docker compose up -d --no-deps --wait backend frontend
```

Điện thoại cùng Wi-Fi mở http://172.18.60.11:3001/dang-ky hoặc /dang-nhap. Biến PowerShell theo terminal không tự tồn tại sau khi đóng; recreate app bằng terminal khác mà quên biến sẽ quay lại chỉ localhost. Khi đổi mạng/IP, thay đúng IP LAN trong allowlist và URL, không dùng wildcard/Host tự động. Các IP/phương án canonical dưới đây là lịch sử, không còn là URL hiện tại.

PASS browser mobile390px thực qua IP LAN và localhost: GETcsrf rồi POST register/login với body rỗng trả422 VALIDATION_ERROR thay403, chứng minh qua CSRF tới validation mà không tạo account; hostileOrigin/forgedtoken vẫn403. Không overflow/page JS errors, hai app healthy. Không đăng nhập bằng credential trong ảnh hoặc tạo user thật. Đây là desktop Chromium mô phỏng mobile, chưa quan sát lại điện thoại vật lý. PostgreSQL ID/start/mount/config/root.envhash/volume/network trước-sau giữ nguyên; chỉ recreate app --no-deps, không restart PostgreSQL. Nếu còn lỗi trên máy bạn, kiểm tra đúng URL này và tải lại trang để lấy cookie/token mới.

## Lịch sử cấu hình

FIX-LAN-01 (10/11/2026): web trước đây chỉ publish frontend trên127.0.0.1 nên localhost200 nhưng IP LAN không kết nối được. Đã đổi duy nhất binding frontend trong docker-compose.yaml sang `0.0.0.0:${FRONTEND_PORT:-3001}:3000`. Đồng bộ environment MARKETPLACE_PUBLIC_ORIGIN của hai app đang chạy thành `http://192.168.110.101:3001`, bằng biến PowerShell theo phiên, không sửa root .env. Chỉ up backend/frontend --no-deps, không build hoặc restart PostgreSQL.

Máy tính đang nối Wi-Fi **Phuc An T2 2**, IP192.168.110.101. Điện thoại cần nối cùng mạng, sau đó mở **http://192.168.110.101:3001**. Ảnh người dùng gửi hiển thị5G; địa chỉ private LAN không dùng trực tiếp qua mạng di động/Internet. Máy tính và Docker phải đang chạy. Không dùng localhost trên điện thoại vì đó là chính điện thoại.

Chạy lại từ root VS Code Terminal khi recreate app; biến origin cần được đặt lại trong mỗi terminal mới:

```powershell
$env:MARKETPLACE_PUBLIC_ORIGIN="http://192.168.110.101:3001"
docker compose up -d --no-deps --wait backend frontend
```

FIX-AUTH-02 (10/11/2026): máy tính hiện đăng nhập được qua cả localhost:3001 và IP LAN đã cấu hình. Compose truyền MARKETPLACE_ADDITIONAL_ORIGINS dạng JSON cho cả hai app, mặc định `["http://localhost:3001"]`, ngoài MARKETPLACE_PUBLIC_ORIGIN ở trên. Mỗi origin phải đầy đủ protocol/host/port, không wildcard/path/query/credentials. Browser giữ cookie host-only riêng từng địa chỉ, nên chuyển từ LAN sang localhost có thể cần đăng nhập riêng. Nếu IP Wi-Fi đổi, cập nhật biến origin và URL điện thoại; không bỏ kiểm tra CSRF hoặc tắt firewall. Điện thoại cùng Wi-Fi vẫn không kết nối được thì cần kiểm tra firewall/router client isolation; task này không mở/sửa firewall/router.

Production phải đặt MARKETPLACE_ADDITIONAL_ORIGINS=`[]` hoặc danh sách origin HTTPS được duyệt; backend từ chối additional origin HTTP trong production. Khi chạy app trực tiếp ngoài Compose, mặc định additional_origins rỗng; muốn dùng thêm địa chỉ phải truyền cùng JSON allowlist cho frontend/backend. Không suy ra quyền từ Host/Forwarded headers của request.

PASS: LAN URL /kenh-nguoi-ban HTTP200, trình duyệt390px tải ảnh/form không tràn hoặc JS errors. CSRF cookie qua LAN và Origin hợp lệ đi tới validation login422 với body rỗng; hostile Origin403, guest shop401. Không tạo tài khoản/shop/đơn hoặc mutation DB để thử. Hai app healthy. PostgreSQL ID/start/mount/service config, volume/network/root .env hash giữ nguyên. Compose config --quiet và git diff --check PASS. Không đổi source frontend/backend/dependencies/schema/Terraform, không commit/push hoặc public hosting.

Chưa kiểm chứng trên điện thoại thật sau khi chuyển Wi-Fi; local browser qua IP LAN không chứng minh được firewall/router cho thiết bị khác. Chưa HTTPS/remote access hoặc toàn bộ checkout trên mobile HTTP. Các kiểm thử250 backend/45 frontend không chạy lại vì chỉ đổi binding/environment; đã smoke kiểm đúng cấu hình runtime.
