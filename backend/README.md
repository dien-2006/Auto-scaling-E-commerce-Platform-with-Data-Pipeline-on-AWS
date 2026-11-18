# P6-01 — Gian hàng Seller

**Cấu hình hiện tại:** chỉ dùng `.env` ở thư mục gốc; xem [hướng dẫn gộp env và Docker release](../docs/docker-release.md). Các tên env theo service trong phần lịch sử không còn được Compose đọc.

POST/GET/PATCH `/api/v1/seller/shop` đã triển khai: đăng ký PENDING, unique owner/slug, hồ sơ theo ownership USER/ADMIN ACTIVE, PATCH tên/mô tả/email không đổi owner/slug/status/logo. WriteAccess user→shop lock xuyên COMMIT, GET READ ONLY, JWT/CSRF/no-store. [Code/contract/kiểm thử và UI](../docs/seller-shop.md). Không Admin duyệt hoặc sản phẩm/tồn/đơn Seller trong task này.

# P5-04 — Theo dõi đơn Buyer

GET `/api/v1/orders?page=1&page_size=24` và GET `/api/v1/orders/{id}` đã có. ReadAccess READ ONLY, SQL ownership theo buyer hiện tại (ADMIN cũng không xem đơn người khác), snapshot/Decimal/BIGINT/no-store, pagination ổn định và query batch. UI `/tai-khoan/don-hang`. [Hướng dẫn/code/kiểm thử](../docs/buyer-orders.md). Hủy và hoàn tồn theo state machine ở P6-05; ghi chú chưa có lịch sử phía dưới là trạng thái trước task này.

# P5-01 — Giỏ nhiều shop

P5-02 mới nhất: backend POST `/api/v1/orders/checkout` có transaction COD nhiều shop, row locks/conditional stock update, idempotency và rollback. [Hướng dẫn checkout](../docs/checkout-api.md). UI checkout đã nối ở P5-03, xem docs/checkout-ui.md. Đăng ký mới yêu cầu password9–128 ký tự có A–Z, số và ký tự đặc biệt; login tài khoản cũ giữ tương thích.

GET `/api/v1/cart`, POST `/api/v1/cart/items`, PATCH/DELETE `/api/v1/cart/items/{id}` có JWT/ownership/CSRF, transaction và kiểm quantity/visibility/self-purchase/tồn. Không giữ hàng hoặc giảm inventory. Xem [hướng dẫn giỏ hàng](../docs/cart.md). Checkout thuộc task sau.

# P4-04 — Địa chỉ giao hàng

GET/POST `/api/v1/addresses`, PATCH/DELETE `/api/v1/addresses/{id}` đã có ownership, CSRF và transaction mặc định. Xem [hướng dẫn địa chỉ](../docs/addresses.md). Dùng DB/schema hiện hữu; không khởi tạo lại hoặc seed dữ liệu thật. Các phần bên dưới ghi lịch sử nền tảng; auth UI đã có từ P4-03.

# P4-01 — Auth backend đã triển khai

Xem [hướng dẫn xác thực](../docs/auth-development.md) để cấu hình khóa, thử CSRF/cookie và chạy tests. Thiếu khóa thì auth503 có chủ ý, không dùng secret mặc định.

# P3-02 — API công khai hiện có

- GET http://localhost:8000/api/v1/categories — cây danh mục đang bật, ẩn nhánh có tổ tiên bị vô hiệu hóa, không phân trang.
- GET http://localhost:8000/api/v1/shops/{shop_slug} — thông tin public shop APPROVED; hidden/missing cùng 404.
- GET http://localhost:8000/api/v1/products — tìm tên, lọc category_id/shop_id, phân trang và sort.
- GET http://localhost:8000/api/v1/products/{product_id} — chi tiết public, tồn kho và metadata ảnh; hidden/missing cùng 404.
- Swagger: http://localhost:8000/docs . logo_url tạm null đến khi delivery S3/logo được cấu hình; không fake URL hoặc lộ key/email/owner.

Các endpoint dùng dữ liệu DB thật qua READ ONLY; không seed/mock production. Phần giới thiệu P2 bên dưới là lịch sử nền tảng. Auth backend hoàn thành P4-01; giỏ/đơn chưa triển khai. Frontend catalog/detail/shop dùng API thật; auth UI chưa tích hợp.

# Marketplace backend

P2-03/P2-04: FastAPI app factory, SQLAlchemy 2/psycopg, mapping 12 bảng thuộc marketplace, bounded connection pool và request-scoped sessions. Không auto DDL/create_all/migrations/seed hoặc commit ngầm. Business APIs/auth vẫn thuộc task sau.

## Docker (khuyến nghị)

Từ thư mục gốc, PostgreSQL hiện hữu phải đang chạy:

```powershell
docker compose build backend frontend
docker compose up -d --no-deps --wait --wait-timeout 90 backend frontend
```

Backend nghe http://localhost:8000; docs tại /docs trong local/test. Docker inject DB credentials từ root .env qua MARKETPLACE_DB_*, hostname postgres và port 5432. Không tự đọc root .env trong code; không copy credentials vào image hoặc log. Root .env/service postgres/volume/network giữ nguyên.

- /health/live: 200, không phụ thuộc DB.
- /health/ready: 200 khi SELECT 1 và đủ 12 bảng schema marketplace qua kiểm tra READ ONLY; 503 khi chưa cấu hình, DB lỗi hoặc thiếu bảng. Không scan/đọc dữ liệu nghiệp vụ.
- /docs,/redoc,/openapi.json: local/test, tắt public docs production.

## Chạy trực tiếp và cấu hình

Cần Python 3.13 và uv; dependencies dùng uv.lock. Cho chạy trực tiếp, tự tạo backend/.env từ .env.example rồi điền credential thực của DB hiện có, host local 127.0.0.1 và port host đã publish. Không chép đè root .env.

```powershell
cd backend
uv sync --locked
uv run --locked --env-file .env uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

Không có DB configuration thì liveness vẫn hoạt động và readiness trả 503. Partial credentials hoặc giá trị pool/timeouts sai bị từ chối. Password dùng SecretStr và URL.create để xử lý ký tự đặc biệt; không in settings/DSN ra log. Production origin nếu cấu hình phải HTTPS exact origin.

Pool mặc định size=5/max_overflow=5, pre_ping, timeout=5s, recycle=1800s; connect_timeout=3s và statement_timeout=3000ms. Tổng tối đa = replicas * workers * (size+overflow), cần dành dư cho admin/ETL và điều chỉnh theo max_connections. Readiness chạy sync thread và trả connection về pool; lifespan dispose engine. get_session không commit khi dependency kết thúc; service phải dùng transaction tường minh, context rollback/close khi lỗi.

Models chứa kiểu/default/identity/PK/FK/CHECK/UNIQUE và indexes đúng SQL; updated_at do trigger DB quản lý, không lấy giờ Python thay thế. Không thêm relationships/cascade gây xóa dữ liệu. Thay schema cần task được duyệt riêng.

## Kiểm tra

```powershell
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q -W error
uv lock --check
```

Mặc định 12 tests integration skip (3 audit và 9 catalog); xem phần catalog cuối tài liệu. Muốn audit database hiện hữu, cấu hình riêng MARKETPLACE_AUDIT_DB_HOST/PORT/NAME/USER/PASSWORD bằng environment rồi chạy pytest. Các tests audit chỉ SELECT metadata trong READ ONLY và rollback, đối chiếu cột/default/identity/PK/FK/CHECK/unique/index và readiness thật; không create_all, CREATE, INSERT, UPDATE, DELETE, nextval hoặc fixture vào production. Không đưa credential trong command line/log/git.

Uvicorn dùng --no-access-log để tránh URL/query trong access log mặc định; application logs route template/status/duration/request ID, không body/cookie/token/exception text. Lỗi sau streaming bắt đầu không đổi được sang JSON mới. Proxy/logging hạ tầng cần cấu hình riêng ở task tương ứng. Chưa có JWT/CSRF/CORS/rate-limit hay auth/checkout nghiệp vụ; không coi skeleton là API chức năng hoàn thiện.

Tham khảo: https://docs.sqlalchemy.org/en/20/orm/session_basics.html,
https://docs.sqlalchemy.org/en/20/core/pooling.html,
https://fastapi.tiangolo.com/tutorial/testing/.

## Kiểm thử catalog riêng biệt

Tổng hiện tại 68 tests khi bật mọi integration: 56 unit/ASGI, 3 audit READ ONLY trên DB hiện hữu và 9 catalog tests trên PostgreSQL riêng. Mặc định 12 integration tests skip nếu chưa cấu hình.

Catalog tests chỉ chạy khi MARKETPLACE_TEST_DB_NAME=marketplace_test, với MARKETPLACE_TEST_DB_HOST/PORT/USER/PASSWORD riêng; không dùng credential/database thật. Fixture tạo schema/tables duy nhất trong DB test này, seed trong transaction rồi rollback. Không dùng file SQL Downloads làm init vì có lệnh DROP. Để chạy đúng cả hai loại integration, MARKETPLACE_AUDIT_DB_* là DB chỉ đọc, MARKETPLACE_TEST_DB_* là DB test riêng; không trộn hai nhóm biến.

Trong task P3-01 đã dùng container postgres:16 tmpfs riêng, port host ngẫu nhiên, không mount volume production, rồi xóa đúng container test sau kiểm thử. Chưa thêm dịch vụ test vào Compose chính. Test fixtures không commit hàng dữ liệu; sequence test có thể tiến nên việc rollback không được xem là an toàn để seed DB thật.

## Kiểm tra P3-02 trong VS Code Terminal

Từ root repository, khi PostgreSQL hiện hữu đang chạy:

```powershell
docker compose build backend
docker compose up -d --no-deps --wait backend
Invoke-RestMethod 'http://localhost:8000/api/v1/products?page=1&page_size=24&sort=price_asc'
Invoke-RestMethod 'http://localhost:8000/api/v1/products?q=serum'
```

Nếu Docker chưa có trong PATH Windows, dùng `& "$env:LOCALAPPDATA/Programs/DockerDesktop/resources/bin/docker.exe"` thay `docker`. Mở Swagger tại http://localhost:8000/docs, chọn Public products → Try it out. Lấy category_id thật từ /api/v1/categories; không coi số thứ tự 1–6 của danh sách UI là identity DB. Lấy product_id từ items rồi gọi /products/{product_id}. Khi catalog chưa có hàng public, `items:[],total:0` và product detail 404 là đúng; không tự seed để có kết quả.

Query: q tối đa 200 ký tự, không phân biệt hoa/thường nhưng chưa hỗ trợ tìm không dấu; %, _ và / được escape thành ký tự literal. page 1..2147483647; page_size 1..100, mặc định 24; sort chỉ newest/price_asc/price_desc. Lọc danh mục gồm nhánh con đang active và có toàn bộ tổ tiên active; ID filter không tồn tại trả danh sách rỗng. Unknown query parameter bị từ chối 422. Thứ tự có product_id DESC làm tie-breaker. Không có filter khoảng giá trong contract API này.

Luồng: router products.py validate → ProductService tạo response → ProductRepository dùng SQLAlchemy SELECT → PostgreSQL marketplace qua postgres:5432 trong Docker. Dùng session READ ONLY hiện có, không commit hoặc DDL. List có 2 truy vấn (count/page), detail có tối đa 2 (product/images); inventory thiếu hoặc bằng 0 trả hết hàng. Giá Decimal được trả chuỗi, BIGINT trả chuỗi. URL ảnh null đến khi P6-03 cấu hình delivery S3; API vẫn trả image ID/is_primary/sort_order đã có, không đọc/trả image_key. Frontend integration là task riêng, không fallback từ API sang mẫu.


## P4-02 — Phân quyền và ownership đã hoàn thành

Backend có policy dùng chung cho Buyer/Seller/Admin; auth/me lấy quyền/trạng thái hiện tại từ DB. SQL kiểm owner, Admin không bypass dữ liệu riêng, shop LOCKED chỉ xử lý đơn cũ. Xem [hướng dẫn](../docs/authorization.md). Không có dashboard/CRUD mới ở task này. 111 tests PASS với PostgreSQL16 riêng và audit READ ONLY; schema/data/config giữ nguyên. Task tiếp theo P4-03 chỉ khi được yêu cầu.

## P6-02 — Sản phẩm Seller (10/11/2026)

GET list/detail, POST create, PATCH, POST hide `/api/v1/seller/products` đã triển khai theo [seller-products.md](../docs/seller-products.md). ACTIVE owner/shop APPROVED, Decimal và SKU unique theo shop, category/tổ tiên active; product+inventory cùng transaction, rollback khi COMMIT lỗi. Khóa user→shared category→shop→product; reads READ ONLY; không reactivation/sửa tồn qua PATCH hoặc DDL. PASS287 full tests với PostgreSQL16 test riêng và metadata audit hiện hữu READ ONLY; Ruff/format/lock PASS. S3/inventory adjustments/seller orders vẫn task riêng.

## P6-03 — Code S3 đã chuẩn bị, chưa bucket

ObjectStorage dùng boto3/Pillow, presigned POST5 phút, grant metadata có chữ ký riêng, MIME/size/bytes/ETag validation và immutable final key. Image API kiểm ownership, serialize primary và chỉ xóa reference. Public/Seller/cart delivery từ key đã xác minh; thiếu bucket null URL/upload503 và không credential discovery. Compose chỉ thêm backend-only optional .env.storage, template storage.env.example.315 full tests/PostgreSQL riêng+SDK double+audit READ ONLY/Ruff/lock PASS; S3 integration thật NOT RUN. Xem [hướng dẫn IAM/CORS và giới hạn](../docs/s3-images.md).


### OTP email qua Brevo — cấu hình chuẩn bị

Xem [hướng dẫn OTP](../docs/otp-setup.md) và `otp.env.example`. Cấu hình private ở `.env` gốc; kiểm tra `MARKETPLACE_OTP_ENABLED` theo môi trường của bạn. Chỉ bật sau khi cấu hình Brevo SMTP và Redis dùng chung. OTP hết hạn sau 60 giây. Không cần SQL/migration; giữ nguyên 25 bảng và cột email NOT NULL. File SQL OTP cũ đã rút lại. Overlay Redis local: `docker-compose.otp.yaml`.
