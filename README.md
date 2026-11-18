# Nền tảng thương mại điện tử tự động mở rộng trên AWS

Multi-Vendor Marketplace với Next.js, FastAPI và PostgreSQL. Một tài khoản có thể mua hàng và sở hữu tối đa một shop. Mục tiêu dài hạn là backend stateless để triển khai Kubernetes/Auto Scaling trên AWS; hạ tầng AWS và ETL chưa triển khai.

Dự án đã có catalog/tìm kiếm, đăng ký/đăng nhập, giỏ nhiều shop, địa chỉ/checkout COD mô phỏng, đơn Buyer, shop/sản phẩm/tồn/đơn Seller và quản trị users/shops/products/categories bằng API thật. Mở http://localhost:3001; Admin tại `/admin`, Seller tại `/kenh-nguoi-ban`. Logo COCO đã trong suốt và responsive. Ảnh upload vẫn tắt khi chưa có bucket; không có sản phẩm mẫu tự seed vào dữ liệu nghiệp vụ.

**Bàn giao mới nhất:** [hướng dẫn sử dụng/cấu hình/giới hạn](docs/handoff.md), [ma trận kiểm thử](docs/test-matrix.md), [E2E có thể chạy lại](tests/e2e/README.md), [baseline hai backend](docs/performance.md). Các mục P2–P6 bên dưới được giữ làm lịch sử, không phải trạng thái hiện tại. S3 thật, ảnh/mapping nghiệp vụ, một số gate cuối P8 và AWS/ETL còn mở; xem checklist thay vì coi mọi task đã DONE.

## Cấu hình một file và Docker image

Cấu hình thật duy nhất: `.env` ở thư mục gốc. Không chép đè file đang dùng bằng mẫu. Hai image ứng dụng tách riêng `coco-backend`/`coco-frontend`; PostgreSQL và Redis là dịch vụ phụ thuộc, không nằm trong hai image. Xem [đóng gói, chuyển máy và đưa lên Git](docs/docker-release.md).

## Tài liệu bắt đầu

Cập nhật14/11/2026: mapping25bảng, CRUD cảgian hàng/sản phẩm (xóa có guardFK giữ lịch sử), publiccatalogAPI cùngURLweb và scriptk6. Xem [hướng dẫn schema25/CRUD/k6](docs/schema25-crud-k6.md). k6đã kiểm từcontainerđộc lập; đườngpublicAWS còn chờdomain/ALBURL, không coi localtest là deployAWS.

Tài khoản ADMIN không được mua hàng hoặc tạo gian hàng; các luồng Buyer/đăng ký shop chỉ dành USER ACTIVE. Dùng tài khoản thành viên riêng khi cần mua bán. Dữ liệu shop/đơn đã có không bị xóa khi thay đổi quyền; xem [phân quyền](docs/authorization.md).

- [AGENT.md](AGENT.md): quy tắc viết code và phạm vi được phép thay đổi.
- [AGENTS.md](AGENTS.md): điểm dẫn đến bộ quy tắc chung cho repository.
- [Kế hoạch TASK](docs/task-plan.md), [tiến độ mới nhất](docs/progress.md).
- [Kiến trúc](docs/architecture.md), [nghiệp vụ](docs/business-rules.md), [API contract](docs/api-contract.md).
- [Kiểm tra database](docs/database-audit.md): đọc kết quả mới nhất, phần cũ là lịch sử.
- [Dữ liệu cần chuẩn bị](docs/data-requirements.md): có thể tiếp tục code khi chưa có dữ liệu.
- [Hướng dẫn backend](backend/README.md), [hướng dẫn frontend](frontend/README.md).
- [Địa chỉ giao hàng](docs/addresses.md): API, giao diện, transaction mặc định và cách kiểm tra P4-04.
- [Giỏ hàng nhiều shop](docs/cart.md): API thật, thêm/sửa/xóa, giá/tồn và cách kiểm tra P5-01.
- [Checkout COD API](docs/checkout-api.md): transaction, khóa tồn kho, idempotency và kiểm thử P5-02; UI xem hướng dẫn P5-03.
- [Giao diện checkout](docs/checkout-ui.md): chọn địa chỉ, COD thật qua API và phục hồi yêu cầu P5-03.
- [Đơn mua Buyer](docs/buyer-orders.md): lịch sử phân trang, chi tiết/snapshot/trạng thái từng shop, quyền sở hữu P5-04.
- [Gian hàng Seller](docs/seller-shop.md): đăng ký shop chờ duyệt, một shop mỗi owner, xem/sửa hồ sơ và dashboard P6-01.
- [Giao diện đăng ký Seller](docs/seller-registration-ui.md): mở thẳng form từ Kênh người bán, thiết kế theo ảnh tham chiếu UI-15.
- [Truy cập bằng điện thoại cùng Wi-Fi](docs/mobile-local.md): URL LAN, public origin và lệnh recreate app khi kiểm trên mobile.

## Stack và cấu trúc hiện có

| Thành phần | Công nghệ |
| --- | --- |
| Frontend | Next.js App Router, React, TypeScript strict, Tailwind |
| Backend | FastAPI, Pydantic, SQLAlchemy 2, psycopg |
| Database | PostgreSQL 16, schema marketplace, 25 bảng |
| Local runtime | Docker Compose, hai app chạy non-root |
| Tooling trực tiếp tùy chọn | Node 24/npm; Python 3.13/uv |
| Ảnh | Thiết kế S3-compatible, chưa kết nối storage |

```text
frontend/
  src/app/                  trang chủ, danh sách, chi tiết, loading/error/404
  src/components/layout/    header/footer
  Dockerfile
backend/
  app/api/                  health và API v1
  app/core/                 config, errors, logging, request ID
  app/db/                   base, pooling/session
  app/models/               mapping schema hiện có
  app/schemas/              request/response models
  app/repositories/         query SQLAlchemy
  app/services/             nghiệp vụ
  tests/                    unit/ASGI và integration riêng
  Dockerfile
  pyproject.toml, uv.lock
docs/
docker-compose.yaml
.env.example                placeholder, không phải credential thật
AGENT.md, AGENTS.md
```

.env thật nằm tại root, không commit. Không ghi nội dung .env vào tài liệu/log hoặc copy vào image.

## Chạy bằng Docker Compose hiện có

Cần Docker Desktop chạy Linux containers và Docker Compose v2. Trên máy hiện tại không cần cài Node/Python hệ thống để chạy app bằng Docker.

PostgreSQL hiện hữu phải đang chạy. Database/container/volume đã có không được tạo lại. Root .env đang giữ credential thực; không chép đè bằng .env.example, không đổi POSTGRES_PASSWORD vì nghĩ đó là cách cập nhật password của DB đã khởi tạo.

Từ thư mục dự án:

```powershell
docker compose build backend frontend
docker compose up -d --no-deps --wait --wait-timeout 90 backend frontend
docker compose ps
```

Hai lệnh đầu chỉ build/chạy app services. --no-deps không khởi động hoặc recreate PostgreSQL; nếu database đang dừng, cần khởi động đúng container marketplace_postgres đang có trước. Không dùng down -v hoặc SQL init để cập nhật app.

| URL mặc định | Nội dung |
| --- | --- |
| http://localhost:3001 | coco homepage/danh sách/chi tiết/shop API thật |
| http://localhost:8000/docs | Swagger local/test |
| http://localhost:8000/health/live | Tiến trình backend, không phụ thuộc DB |
| http://localhost:8000/health/ready | DB/query/schema sẵn sàng: 200; chưa sẵn sàng: 503 |
| http://localhost:8000/api/v1/categories | Cây danh mục public; DB chưa có danh mục trả items=[] |
| http://localhost:8000/api/v1/shops/{shop_slug} | Thay placeholder bằng slug shop APPROVED thật; missing/hidden trả 404 |

Frontend dùng cổng 3001 vì có ứng dụng khác tại 3000. Có thể cấu hình FRONTEND_PORT/BACKEND_PORT qua environment hoặc root .env; ports ứng dụng chỉ bind localhost. Backend trong Docker kết nối postgres:5432, không dùng localhost.

Giữ nguyên service postgres, volume marketplace_postgres_data và network marketplace_network. App startup không create_all/migrate/seed; readiness dùng truy vấn chỉ đọc. INTERNAL_API_URL=http://backend:8000 dùng cho server-side fetch homepage từ P3-03; browser không gọi hostname Docker. Chưa cần thêm frontend API proxy.

Xem logs ứng dụng hoặc chỉ dừng hai app khi cần:

```powershell
docker compose logs --tail 100 backend frontend
docker compose stop frontend backend
```

Khi sửa backend đã được yêu cầu, có thể build và up riêng backend với --no-deps để giữ frontend/database đang chạy. Không dừng/recreate container của dự án khác để lấy cổng.

## Trạng thái chức năng

| Phần | Hiện trạng |
| --- | --- |
| Frontend layout/loading/error/404 | Có |
| PostgreSQL mapping/pooling/readiness | Có |
| Danh mục public | Có; ẩn cả nhánh có tổ tiên inactive |
| Chi tiết shop public | Có; chỉ APPROVED, không lộ email riêng/owner/storage key |
| API sản phẩm/tìm kiếm/phân trang | P3-02 DONE; dữ liệu thật, chưa nối frontend |
| Trang chủ với API thật | P3-03 DONE, tìm kiếm/danh mục trên homepage |
| Danh sách/tìm kiếm/phân trang API thật | P3-04 DONE, URL giữ bộ lọc và trang |
| Chi tiết/shop tích hợp API | P3-05 DONE; gallery, tồn kho, shop list và 404 thật |
| Auth và phân quyền chức năng | P4-01–03 có API/UI/JWT/CSRF/ownership; cần cấu hình secret local |
| Địa chỉ giao hàng | P4-04 có API và UI `/tai-khoan/dia-chi` |
| Giỏ hàng nhiều shop | P5-01: `/gio-hang`, thêm/sửa/xóa bằng API thật; không giữ tồn kho |
| Checkout COD API | P5-02: transaction nhiều shop, chống overselling/idempotency; UI đã nối P5-03 |
| Checkout UI | P5-03: `/thanh-toan` chọn địa chỉ/COD/review/xác nhận server/retry cùng key |
| Lịch sử đơn Buyer | P5-04: `/tai-khoan/don-hang` và chi tiết, snapshot/trạng thái từng shop, chỉ đơn của mình |
| Gian hàng Seller | P6-01: `/kenh-nguoi-ban` đăng ký PENDING, xem/sửa hồ sơ, ownership và unique owner/slug |
| Sản phẩm/tồn/đơn Seller, Admin dashboard | P6-02–05/P7, chưa làm |
| S3, Kubernetes, AWS Auto Scaling, ETL | Chưa triển khai |

logo_url hiện null đến khi có delivery storage hợp lệ, kể cả DB có logo_key. API không trả dữ liệu mock. Riêng UI-01 dùng dữ liệu minh họa local được ghi nhãn, không gọi API, không giả tồn kho/đơn hàng hoặc ghi dữ liệu vào PostgreSQL.

## Chưa có dữ liệu thì cần làm gì

Vẫn tiếp tục được P3-02 và các task UI; hệ thống phải có empty state thật. Trước khi demo mua hàng cần chuẩn bị:

1. Danh mục: tên, slug, quan hệ cha/con.
2. Shop: tên, slug, mô tả, người sở hữu; tài khoản tạo qua quy trình hợp lệ và shop cần APPROVED.
3. Sản phẩm: tên, SKU, shop, danh mục, mô tả, giá VND và tồn kho.
4. Ảnh có quyền sử dụng, tham chiếu đúng SKU; cấu hình S3/local storage trước khi upload.

Gợi ý cho demo nhiều shop: 3–5 danh mục, 2 shop thuộc 2 owner khác nhau, 10–20 sản phẩm và một Buyer độc lập. Đây là gợi ý, không bắt buộc để code. Giỏ/địa chỉ/đơn sẽ tạo qua ứng dụng khi chức năng hoàn thành; không cần tự điền cả 12 bảng.

Đọc [dữ liệu cần chuẩn bị](docs/data-requirements.md) để biết các trường có thể gửi. Không gửi mật khẩu/keys qua chat. Nếu chưa có catalog thật, có thể yêu cầu một task dữ liệu demo riêng cho local/test; chưa có import/seed được tự động thực hiện. Dataset review HealthBeauty không đủ giá/tồn/SKU/ownership để import trực tiếp.

## Kiểm thử

Backend, từ backend/ với Python 3.13 và uv:

```powershell
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q -W error
uv lock --check
```

Kết quả P3-02: 68 tests đạt khi bật đầy đủ integration. Mặc định 56 tests chạy, 12 integration skip nếu thiếu cấu hình. MARKETPLACE_AUDIT_DB_* chỉ đọc DB hiện hữu; MARKETPLACE_TEST_DB_* dành PostgreSQL riêng có tên marketplace_test. Fixture tạo schema/ghi dữ liệu chỉ trong DB test riêng, không mount production volume. Rollback không hoàn tác sequence nên không seed fixture vào DB thật.

Frontend, từ frontend/ với Node 24:

```powershell
npm ci
npm run test
npm run lint
npm run typecheck
npm run build
```

Docker build đã chạy production build Next.js. HTTP smoke không thay thế kiểm browser visual hoặc E2E nghiệp vụ. Bộ lint frontend có giới hạn dev dependencies đã ghi tại progress; không tự audit fix --force.

## Quy trình tiếp tục

Bạn yêu cầu task bằng ID trong task-plan. Tôi triển khai trong phạm vi, kiểm thử, cập nhật progress và dừng; chỉ làm nhiều task khi bạn yêu cầu rõ. Task chức năng tiếp theo là P4-01; chỉ bắt đầu khi được yêu cầu.

SQL/DOCX là nguồn yêu cầu nhưng không tự cấp quyền chạy SQL. Bản marketplace_schema.sql trong Downloads đã quan sát có DROP TABLE, không dùng làm init/import. Không thay schema, dữ liệu, Terraform, deploy AWS hoặc commit/push nếu chưa được yêu cầu.


## UI-09 — Trang danh sách/chi tiết và bố cục giỏ/checkout

Danh sách `/san-pham` và chi tiết `/san-pham/{product_id}` có menu6 danh mục và giao diện xanh đồng bộ, vẫn dùng API thật. `/gio-hang` và `/thanh-toan` là **bản xem trước bố cục**, chưa kết nối giỏ, tài khoản, địa chỉ hay checkout transaction. Không nhập PII/đặt hàng/tổng tiền mẫu. Chỉ COD mô phỏng sẽ được tích hợp theo P5; không hỗ trợ thẻ/ví/QR. Header giỏ có link đến preview, có thể đi tới checkout và quay lại catalog.

Kiểm tra http://localhost:3001/gio-hang và http://localhost:3001/thanh-toan, responsive và liên kết quay lại. Chạy root: `docker compose build frontend`, `docker compose up -d --no-deps --wait frontend`. Frontend: `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build` đều PASS (21 tests); browser fixture và real UI PASS. DB/config giữ nguyên. P4/P5 vẫn chưa thực hiện.


## P4-01 — Backend xác thực

API register/login/logout/me/csrf đã triển khai; xem [hướng dẫn](docs/auth-development.md). Cần tự cấu hình MARKETPLACE_JWT_SECRET random để bật auth; root .env giữ nguyên. Frontend auth/policy/giỏ nghiệp vụ còn task riêng. 95 tests PASS với PostgreSQL16 test riêng; dữ liệu thật chỉ audit READ ONLY.


## P4-02 — Phân quyền và ownership đã hoàn thành

Backend có policy dùng chung cho Buyer/Seller/Admin; auth/me lấy quyền/trạng thái hiện tại từ DB. SQL kiểm owner, Admin không bypass dữ liệu riêng, shop LOCKED chỉ xử lý đơn cũ. Xem [hướng dẫn](docs/authorization.md). Không có dashboard/CRUD mới ở task này. 111 tests PASS với PostgreSQL16 riêng và audit READ ONLY; schema/data/config giữ nguyên. Task tiếp theo P4-03 chỉ khi được yêu cầu.


## P4-03 — Giao diện tài khoản

Đã có /dang-ky, /dang-nhap, /tai-khoan và đăng xuất trên header; API thật qua proxy same-origin, JWT HttpOnly cookie, CSRF, safe return URL. Xem [hướng dẫn](docs/auth-ui.md). Cần JWT secret của backend để bật auth local; thiếu khóa UI báo chưa sẵn sàng, không fake login. Root .env và DB giữ nguyên;24 tests/lint/typecheck/build và browser E2E với PostgreSQL16 riêng PASS. Chưa làm địa chỉ, giỏ thật hoặc dashboard.

## BRAND-01 / P6-02 — Logo và sản phẩm Seller (10/11/2026)

Logo dùng ảnh COCO do chủ dự án cung cấp trên header/footer/auth/Seller và favicon. Vào **Kênh người bán → Sản phẩm của tôi** tại `/kenh-nguoi-ban/san-pham` để thêm/sửa/ẩn, tìm/lọc/phân trang sản phẩm bằng API thật. Chỉ chủ shop APPROVED được thao tác; tạo sản phẩm và tồn kho ban đầu cùng giao dịch. Ảnh S3 và điều chỉnh tồn kho thuộc task tiếp theo, chưa bật trong lượt này. Xem [hướng dẫn và kiểm chứng](docs/seller-products.md).

## BRAND-02 / P6-03 — Logo trong suốt và chuẩn bị ảnh S3 (10/11/2026)

Logo đã bỏ nền trắng và tăng chiều cao hiển thị. Seller có **Sản phẩm của tôi → Quản lý ảnh**; code API/upload/ảnh chính/thứ tự/bỏ reference đã chuẩn bị. Chưa có bucket nên upload hiện disabled và API báo STORAGE_NOT_CONFIGURED; chưa triển khai AWS. Xem [cấu hình và kiểm chứng S3](docs/s3-images.md). P6-03 vẫn IN_PROGRESS tới khi kiểm bucket thật;315 backend/52 frontend tests và build PASS.

## FIX-AUTH-02 — Đăng nhập localhost/LAN

Đã sửa CSRF403 khi truy cập localhost trong lúc canonical origin là IP LAN bằng exact additional-origin allowlist đồng bộ hai app. Dùng lại localhost:3001/dang-nhap; hai host giữ phiên cookie riêng. Xem [cấu hình local và production](docs/mobile-local.md).323 backend/53 frontend tests, build và browser login test DB PASS; PostgreSQL và root .env giữ nguyên.
