# Kiến trúc Marketplace

Cập nhật 15/11/2026: [coupon/review](buyer-coupons-reviews.md) dùng Core Tables schema25. Checkout khóa coupon sau catalog/inventory; cancellation khóa coupon sau shop_order/inventory rồi kiểm toàn bộ child orders để hoàn lượt đúng một lần. Không đảo thứ tự lấy coupon trước inventory. Review write khóa user→shop_order, không lấy catalog/inventory sau đó. Không có DDL hoặc seed startup. UI bỏ checkout intent sau kết quả tạo đơn hợp lệ, giữ intent khi chưa rõ kết quả HTTP.

P1-03, ngày 09/11/2026. Thiết kế bám SQL/DOCX và các quyết định Q03–Q06 đã duyệt tại business-rules.md. Chưa viết code.

Cập nhật P5-02 (10/11/2026): backend checkout đã triển khai theo [checkout-api.md](checkout-api.md). Shared category advisory lock dùng namespace/key `(731921,1)`; category mutations phải lấy exclusive cùng key. Checkout tự sở hữu transaction qua COMMIT để retry tối đa3 attempt cho deadlock/serialization/idempotency conflict, dùng cùng AccessPolicy/JWT/CSRF nhưng không bọc WriteAccess/begin lồng nhau. Bản UI checkout thuộc P5-03. Mật khẩu đăng ký mới theo yêu cầu trực tiếp: 9–128 ký tự, A–Z, 0–9, punctuation/symbol; login không áp lại complexity của đăng ký cho hash cũ.

## Cấu trúc và đường đi request

```text
Browser -> Next.js UI / proxy /api/v1 -> FastAPI -> PostgreSQL
Browser -------- presigned upload/read ---------> S3-compatible storage
```

Frontend Next.js App Router, TypeScript strict, Tailwind; backend FastAPI modular monolith và SQLAlchemy. Tách deployable frontend/backend. Trong Docker: frontend gọi backend:8000, backend gọi postgres:5432 trên marketplace_network hiện hữu. Browser dùng URL tương đối /api/v1 qua proxy cùng origin, không hostname nội bộ. Proxy target cố định từ env, không nhận URL tùy ý; forward cookie/CSRF/request ID, không giữ state nghiệp vụ. FastAPI giữ toàn bộ auth/permission/transaction, không tin route guard UI.

```text
frontend/src/
  app/(store)/, app/(auth)/, app/account/, app/cart/, app/checkout/
  app/seller/, app/admin/, app/api/v1/
  components/{layout,ui,catalog}/
  features/{auth,cart,orders,seller,admin}/
  lib/{api,format,validation}/, hooks/, types/
backend/app/
  main.py, api/v1/routers/
  core/{config,security,errors,logging}/
  db/{base,session}/, models/, schemas/, repositories/, services/
backend/tests/{unit,integration}/
tests/e2e/, docs/
```

Routers xử lý HTTP, Pydantic validate, service quản lý nghiệp vụ/transaction, repository query và không tự commit. ORM schema-qualified marketplace, ánh xạ đúng 12 bảng; không create_all/migration/seed tự động. SQLAlchemy models tách response schemas, không expose password_hash. Version cụ thể chọn/lock và kiểm compatibility tại P2; không cài dependency trong task tài liệu.

Giữ nguyên service postgres, named volume marketplace_postgres_data, network marketplace_network, env database và dữ liệu. P2-04 chỉ thêm hai app services, không restart/recreate database hoặc thêm init SQL. Không Terraform/AWS/Kubernetes/ETL ở task này; hỗ trợ stateless không đồng nghĩa đã triển khai auto scaling.

## Bảo mật

Argon2id hash; email trim và lookup case-insensitive theo LOWER(email), không tự gộp tài khoản cũ. Password đăng ký 9–128 ký tự, có chữ hoa A–Z, số0–9 và ký tự đặc biệt punctuation/symbol theo yêu cầu mới; không trim, cho phép Unicode. Login giữ tương thích hash cũ. Registration luôn USER/ACTIVE, cấm mass assignment role/status/owner. Admin bootstrap không qua endpoint công khai, cần quy trình được yêu cầu riêng khi triển khai auth.

Access JWT trong cookie HttpOnly, SameSite=Lax, Path=/, Secure production; local HTTP dùng tên cookie riêng không __Host prefix. TTL 15 phút theo quyết định duyệt; không refresh/revocation store. JWT kiểm signature/allowlist thuật toán/exp/iat/sub/issuer/audience; secret từ env, không secret mặc định dùng được. Không trả token JSON hoặc localStorage. Logout xóa cookie, không hứa thu hồi JWT bị sao chép trước exp. User role/status và shop status đọc DB hiện tại mỗi protected request.

CSRF signed double-submit: /auth/csrf tạo token ký và cookie readable, client gửi X-CSRF-Token cho mọi unsafe method kể cả login/register/logout; backend kiểm signature, cookie/header và Origin/Referer allowlist. Không coi SameSite là bảo vệ duy nhất. Proxy giữ public Origin, không tin forwarded headers từ nguồn không cấu hình; CORS không wildcard credentials. Chưa cung cấp Bearer API làm đường bypass CSRF.

Cần rate-limit login ở shared gateway/store khi triển khai nhiều replicas; không giả định bộ đếm memory bảo vệ toàn cluster, không tự thêm Redis. Không log passwords/cookie/JWT/body chứa địa chỉ/phone. Errors không SQL/stack/DSN; request ID có validation.

## Đồng thời và checkout

READ COMMITTED cộng explicit row/advisory locks và conditional writes. Thứ tự khóa chung: user theo ID → cart → khóa cấu trúc danh mục → shop theo ID → product theo ID → inventory theo product ID → shop_order khi cần. Từng operation chỉ lấy khóa cần thiết, nhưng không đảo thứ tự. Category dùng PostgreSQL transaction advisory lock thống nhất giữa tree mutations và checkout khi cần visibility, không in-memory lock; category mutations đọc lại cây sau khi có khóa để chặn cycle nhiều nút.

Checkout khóa buyer/cart và kiểm đơn theo buyer/key trước khi đòi giỏ còn hàng. Nếu replay thì trả order snapshot. Lần đầu kiểm address ownership, toàn bộ giỏ/expected price, user/shop/catalog và tồn dưới khóa. Tính Decimal, insert orders/shop_orders/order_items snapshots, giảm tồn có điều kiện quantity>=requested, xóa các cart_items mua trong một transaction. Unique buyer/key là hàng rào cuối; conflict rollback rồi đọc lại đơn đã commit trong transaction mới. Request timeout sau commit retry cùng key, không giảm tồn lại; deadlock/serialization retry có giới hạn với key cũ. Không gọi S3 trong transaction checkout.

Seller/admin đổi status/price/visibility phối hợp cùng khóa để kiểm tra checkout không bị stale. Nếu khóa shop đã commit trước checkout thì checkout phải từ chối; không hứa hủy giao dịch đã commit trước thao tác khóa. Admin khóa user không ngăn request đã hoàn thành, nhưng request bảo vệ tiếp theo phải đọc trạng thái mới.

Hủy đơn khóa tài nguyên theo thứ tự trên, conditional transition nguồn → CANCELLED và hoàn tồn cùng commit. CANCELLED là guard để retry không hoàn tồn hai lần; không thêm bảng hoàn tồn. COMPLETED/CANCELLED không sửa dòng/giá. Seller inventory delta dùng khóa inventory và expected quantity; stale trả 409, không overwrite snapshot. Có giới hạn ABA nếu quantity quay lại cùng giá trị; không quảng cáo exactly-once cho adjustment.

Địa chỉ default serialize theo user rồi unset/set, giữ partial unique index. Ảnh primary serialize theo product rồi unset/set cùng transaction. Service không commit từng phần; rollback/close session mọi đường lỗi.

## Dữ liệu và ảnh

ID BIGINT biểu diễn chuỗi số dương để không mất chính xác JavaScript; tiền decimal string theo NUMERIC(14,2), tổng không overflow, không float. UI Intl vi-VN/VND, timestamps UTC ISO-8601; không tự làm tròn mất phần thập phân hợp lệ. Mô tả plain text và escape khi render, không arbitrary HTML.

S3 chỉ lưu object, PostgreSQL giữ image_key/logo_key. Presigned POST với policy MIME JPEG/PNG/WebP, giới hạn đề xuất 5 MiB, expiry ngắn. Confirm upload xác minh object size/content/owner-prefix trước liên kết. Không SVG/HTML, arbitrary object key hay cross-shop. DB fail có thể để orphan object; không tự xóa object hoặc cấu hình lifecycle AWS. Bỏ ảnh chỉ xóa reference khi được Seller yêu cầu, không xóa object storage cũ. Logo key read-only ở bản đầu vì chưa đặc tả quy trình upload logo.

Q06 đã chốt hướng storage nhưng endpoint/bucket local chưa có; P6-03 phải có cấu hình hợp lệ hoặc task MinIO riêng. Không mặc định MinIO của dự án ngân hàng, không lưu ảnh trong filesystem backend container. Thiếu ảnh hiển thị placeholder; thiếu catalog trả empty state, không fake production data. Không tự import dataset HealthBeauty ở workspace khác.

## Runtime, cấu hình và kiểm thử

Env ứng dụng dự kiến: DATABASE_URL (postgres trong Docker), pool_size/max_overflow/timeouts, PUBLIC_ORIGIN, INTERNAL_API_URL, JWT_SECRET/issuer/audience/TTL, S3_ENDPOINT/region/bucket và credential provider. .env.example chỉ placeholder, không secrets thật; P1-03 không sửa env. Tổng connections = replicas * workers * (pool_size+max_overflow), dành dư cho admin/ETL; chốt ngân sách theo max_connections/load ở task triển khai.

/health/live không gọi DB; /health/ready SELECT 1 có timeout, 503 khi DB không sẵn. Readiness không chạy DDL. Structured logging metadata request/action/status, không PII. Graceful shutdown drain request, đóng pool. Không giữ session/cart/idempotency hoặc upload trên pod, không background job quan trọng fire-and-forget.

Private APIs và auth no-store; Server Components không cache dữ liệu cá nhân và chỉ forward cookie cần thiết. Catalog ban đầu chưa cache để tránh ẩn/khóa sản phẩm bị stale; tối ưu sau đo baseline. Pagination ổn định, parameterized search, tránh N+1, không tự thêm extension/index.

Unit validation/policy; PostgreSQL 16 integration riêng cho lock/constraint/rollback; E2E vai trò/UI; concurrency nhiều backend cho tồn và idempotency. Không SQLite thay cho chứng minh lock PostgreSQL; không tạo/mount/reset DB test dùng volume thật. Các bài test này dự kiến cho P2–P8, chưa chạy trong task tài liệu.
