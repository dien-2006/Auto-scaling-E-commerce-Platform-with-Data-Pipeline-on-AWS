# Bàn giao local và giới hạn còn mở

**Cấu hình hiện tại:** chỉ dùng `.env` ở thư mục gốc; xem [hướng dẫn gộp env và Docker release](docker-release.md). Các tên env theo service trong phần lịch sử không còn được Compose đọc.

**ADMIN-COMMERCE-01:** ADMIN bị chặn bằng403 COMMERCE_FORBIDDEN ở API giỏ/địa chỉ/đơn Buyer/checkout và hồ sơ đăng ký shop. Chỉ USER ACTIVE dùng các luồng này. Giữ nguyên dữ liệu cũ; quy tắc mới thay thế các ví dụ lịch sử cho Admin mua hàng hoặc tạo shop bên dưới.


Ngày 11/11/2026. Website local đã có luồng Buyer/Seller/Admin; chưa hoàn tất triển khai production hoặc AWS/ETL. Kế hoạch chi tiết: [task-plan.md](task-plan.md), evidence [test-matrix.md](test-matrix.md), E2E [README](../tests/e2e/README.md), baseline [performance.md](performance.md).

## Sử dụng

- Mở http://localhost:3001. Đăng nhập thường về trang chủ; link protected giữ returnTo hợp lệ. LAN IP cũ trong canonical config có thể không còn truy cập được; alias localhost vẫn được allowlist. Không tự đổi origin theo Host header.
- Buyer: Sản phẩm → thêm giỏ → địa chỉ → COD mô phỏng → đơn mua. Giỏ không giữ hàng; server kiểm lại giá/tồn lúc đặt.
- Seller: `/kenh-nguoi-ban` đăng ký shop → chờ Admin duyệt → sản phẩm/tồn/đơn. Shop LOCKED vẫn xử lý đơn cũ khi user ACTIVE.
- Admin: đăng nhập tài khoản đã cấp quyền → `/admin`. Users chỉ khóa USER; ADMIN chỉ xem. Shops duyệt/từ chối/khóa; products ẩn; categories thêm/sửa/cha/bật/tắt. Chưa bật lại sản phẩm hoặc mở khóa shop theo contract hiện tại.
- Tạo sản phẩm thật cần danh mục, shop APPROVED, SKU, tên/mô tả, giá và tồn chính xác. Xem [data-requirements.md](data-requirements.md). Không seed giá/tồn hoặc dùng ảnh minh họa làm dữ liệu bán hàng.

## Cấu hình và cập nhật

Giữ root .env và PostgreSQL hiện hữu; không copy env mẫu đè lên cấu hình đang chạy. JWT secret chỉ .env ignored. Storage chỉ .env khi đã có bucket; xem [s3-images.md](s3-images.md). Không gửi key/password qua chat hoặc NEXT_PUBLIC_*.

Để cập nhật app đã được yêu cầu: build service thay đổi, rồi `docker compose up -d --no-deps --wait backend frontend` (hoặc chỉ service vừa đổi), giữ MARKETPLACE_PUBLIC_ORIGIN và additional origins khớp cả hai app. Không `down -v`, restart/recreate postgres, chạy lại SQL Downloads, create_all/migration/seed trên DB nghiệp vụ. Schema test do runner tạo chỉ trong tmpfs marketplace_test.

Trước/sau cập nhật đối chiếu PostgreSQL ID/StartedAt/mount/service config, root .env hash, named volume marketplace_postgres_data và marketplace_network. Không log giá trị env/secret khi kiểm. Liveness `/health/live` không phụ thuộc DB; readiness `/health/ready` kiểm kết nối và các bảng, trả503 khi không sẵn sàng; load balancer nên dùng readiness cho nhận traffic. Kiểm graceful idle shutdown đã có trong performance runner, graceful drain đang tải vẫn chưa được đo.

## Bảo mật đã kiểm và rủi ro

JWT HttpOnly/SameSite cookie, production dùng Secure/__Host cookie và HTTPS origin; access15 phút, chưa refresh token và chưa thu hồi tức thì JWT sau logout. Quyền/status đọc DB mỗi protected request. CSRF ký ràng buộc access cookie + exact Origin/Referer allowlist, không wildcard. Backend ownership/transaction guard, SQL parameterized/allowlisted sort, projection không password_hash/private storage key. Error/request logging không echo body/token/DSN, debugfalse; docs API tắt trong production.

Next thêm X-Content-Type-Options:nosniff, X-Frame-Options:DENY, Referrer-Policy:strict-origin-when-cross-origin, Permissions-Policy chặn camera/microphone/geolocation. E2E xác minh header thật trên HTTP. HSTS/TLS termination, CSP phù hợp nonce/Next, distributed rate limiting/abuse controls và giám sát phải thiết kế/kiểm trước production; không bật HSTS cho localhost HTTP hoặc thêm limiter in-memory rồi coi là bảo vệ nhiều replica.

Dependency review11/11/2026: OSV47 packages backend ban đầu báo Pillow12.3.0 có advisories, gồm JPEG decoder đang được ứng dụng dùng. Cập nhật Pillow13.0.0 theo [release notes chính thức](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html), thêm decoder allowlist trước cả verify/load; test JPEG/PNG/WebP publish và TIFF giả PNG bị từ chối. Audit OSV sau cập nhật không còn finding. Không suy ra mọi kiểu lỗi đã được kiểm hoặc S3 thật đã an toàn.

`npm audit` còn7 mức moderate trong chuỗi dev-only TypeScript ESLint/minimatch10.2.6 ([advisory](https://github.com/advisories/GHSA-g3hv-75wg-m249)); không force override minimatch sang major khác để làm sạch audit. Đây là rủi ro tooling cần theo dõi bản tương thích; không đưa input không tin cậy vào glob tooling. Report và lockfile giữ nguyên phần này. Audit production-only được ghi riêng trong progress. Quét pattern có giới hạn trên Git-visible files không thấy AWS ID/private key/GitHub token/private env, không thay thế secret scan đầy đủ/Git history hoặc pentest.

Chạy lại từ root: `backend/.venv/Scripts/python.exe tests/security/review.py` và `... tests/security/dependencies.py`. Dependency script gửi tên/version package công khai tới OSV, không gửi credential/source. Với frontend: `npm audit --json` và `npm audit --omit=dev --json`; luôn ghi ngày và findings, không gọi audit lỗi mạng là PASS.

## Chưa thể hoàn tất

1. **S3/bộ ảnh:** chủ dự án chưa có bucket. Code/hướng dẫn/missing-storage UI đã có; cần bucket test được chỉ định, region/endpoint, IAM/CORS và credential provider trên máy. Sau đó kiểm upload/HEAD/conditional PUT/delivery/expiry/mất response trên bucket thật. Không yêu cầu gửi secret qua chat. P6-03 còn mở; các gate S3 của P8-01/02/04 vẫn mở.
2. **Dữ liệu và UI-04:** branding COCO/logo đã xong; ảnh sản phẩm và mapping thật chưa được cung cấp. Không tự tạo dữ liệu bán hàng hoặc dùng ảnh logo/banner gán vào sản phẩm.
3. **Production:** chưa HTTPS/device thật/soak test/rolling deploy đang tải/backup-restore; còn tooling audit và các kiểm soát edge nêu trên. Thanh toán/vận chuyển vẫn mô phỏng, không thẻ/ví/cổng thanh toán thật.
4. **AWS/ETL:** chưa Auto Scaling EC2/EKS, hai AZ, monitoring/cloud deployment, S3 data pipeline/Athena. Cần scope/hạ tầng/tài khoản riêng; yêu cầu hoàn tất website local không tự cấp quyền triển khai hoặc phát sinh chi phí AWS.

Không đánh dấu mọi task DONE chỉ vì phần local đã chạy. Sau khi có đầu vào S3/ảnh, chạy lại gate còn mở rồi cập nhật status theo evidence.
