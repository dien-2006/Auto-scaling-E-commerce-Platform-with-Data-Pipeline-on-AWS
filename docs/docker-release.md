# Một Docker Compose cho local và EC2

Chỉ dùng `docker-compose.yaml`. Local đọc `.env` và không bật Nginx. EC2 đọc
`.env.ec2`, bật profile `ec2` để chạy thêm Nginx/HTTPS. File Compose EC2 riêng đã
được gộp và xóa; không dùng `docker-compose.ec2.yaml` nữa.

Quy trình dưới đây dành cho bản sửa phạm vi báo giá checkout và IP giới hạn OTP.
Các lệnh chỉ là hướng dẫn để người dùng tự chạy. Agent chưa chạy test, build,
Docker, SQL, migration hoặc triển khai EC2.

Không có script tạo bảng, migration hoặc seed nào được thêm vào quy trình.
`database/init` giữ nguyên và không còn được mount làm thư mục init của PostgreSQL.
Việc tạo schema/restore dữ liệu do người dùng xem xét
và thực hiện thủ công. Không dùng `docker compose down -v` với dữ liệu cần giữ.

## 1. Kiểm tra local

Cần Docker Engine/Compose v2 hoạt động, Node 24, Python 3.13 và uv nếu chạy các
kiểm thử trên máy. Mọi lệnh bên dưới dùng Bash/WSL và bắt đầu từ thư mục gốc repo.
Nếu dùng Docker Desktop với WSL, bật WSL integration trước.

Giữ `.env` local hiện tại. Với local, `MARKETPLACE_ENVIRONMENT` phải là `local`,
origin phải khớp chính xác URL mở trong trình duyệt (mặc định
`http://localhost:3001`). Không đưa `MARKETPLACE_PROXY_SECRET` của EC2 vào `.env`
local: cấu hình local không có reverse proxy công khai để xác thực IP khách.

Kiểm thử mới của backend chỉ dùng dữ liệu trong bộ nhớ, không kết nối PostgreSQL,
không tạo bảng. Không bật biến `MARKETPLACE_TEST_DB_*` hoặc tự chạy toàn bộ nhóm
integration để làm theo hướng dẫn này.

```bash
cd backend
uv sync --locked
uv run --locked pytest -q tests/test_checkout_quote_scope.py tests/test_client_ip.py
uv run --locked ruff check app tests
uv run --locked ruff format --check app tests
cd ..
```

```bash
cd frontend
npm ci
npm test
npm run lint
npm run typecheck
npm run build
cd ..
```

Kiểm tra trạng thái các service hiện có và cú pháp Compose, không in cấu hình
đã nội suy vì có thể chứa secret:

```bash
docker compose -f docker-compose.yaml config --quiet
docker compose -f docker-compose.yaml ps
```

Chỉ tiếp tục nếu PostgreSQL và Redis hiện hữu đang chạy và database đã có schema
do người dùng chuẩn bị. Nếu thiếu bảng, dừng ở đây để người dùng xử lý thủ công.
Build/cập nhật riêng hai ứng dụng; `--no-deps` không khởi tạo lại database:

```bash
docker compose -f docker-compose.yaml build backend frontend
docker compose -f docker-compose.yaml up -d --no-deps --wait --wait-timeout 120 backend frontend
curl -fsS http://127.0.0.1:8000/health/live
curl -fsS http://127.0.0.1:8000/health/ready
```

Mở `http://localhost:3001`, thử đăng nhập, danh mục, thêm/cập nhật giỏ hàng và chọn
địa chỉ. Chỉ tự bấm xác nhận đặt hàng nếu đồng ý ghi dữ liệu đơn và giảm tồn kho
trong database local. Việc yêu cầu OTP sẽ gửi email thật nếu SMTP đang bật.

Giữ `MARKETPLACE_CHECKOUT_OPTIONS_ENABLED=false` với schema legacy hiện tại.
Các test backend ở trên kiểm tra được báo giá Mua ngay/sản phẩm đã chọn mà không
cần thay schema. Chỉ kiểm thử giao diện checkout options sau khi chính người dùng
xác nhận database đã có các cột cần thiết; không bật cờ để thử trên schema thiếu.

Với local không có Nginx, giới hạn OTP dùng IP kết nối của Next.js. Kiểm thử mới
xác nhận cơ chế IP ký và chống giả mạo bằng dữ liệu trong bộ nhớ. Việc phân biệt
IP khách thực tế được dùng khi bật profile `ec2` và chạy qua Nginx bên dưới.

## 2. Chuẩn bị cấu hình EC2, chưa triển khai

- `docker-compose.yaml`: cấu hình duy nhất cho cả local và EC2.
- `.env.ec2.example`: mẫu biến môi trường EC2; sao chép thủ công thành `.env.ec2`, không đổi `.env`.
- `deploy/ec2/nginx.conf`: HTTPS, chuyển HTTP sang HTTPS, ghi đè header IP do khách gửi.
- `deploy/ec2/certs/`: chỉ chứa certificate/key do người dùng cung cấp; không commit.

Điền domain HTTPS thật, mật khẩu database mạnh và hai secret ngẫu nhiên riêng
cho JWT/proxy. Nếu bật OTP, cần thêm secret OTP riêng, chọn provider `smtp`, và
điền đầy đủ email người gửi/SMTP. Bản mẫu để OTP tắt đến khi cấu hình hoàn tất;
việc này chỉ áp dụng cho môi trường EC2 mới, không thay local.

Người dùng có thể tự tạo từng secret bằng lệnh sau; chạy riêng cho mỗi secret rồi
tự điền vào file, không gửi giá trị secret vào chat:

```bash
openssl rand -hex 32
```

Backend/frontend phải dùng cùng `MARKETPLACE_PROXY_SECRET`; Compose đã nối
biến này cho cả hai service. Không dùng secret proxy chung với JWT hoặc OTP.
Origin chính và mọi origin bổ sung phải là HTTPS khi chạy production.

Chuẩn bị `fullchain.pem` và `privkey.pem` hợp lệ cho domain trong thư mục certificate
trước khi chạy Nginx. Cấu hình hiện tại dành cho truy cập trực tiếp vào Nginx EC2.
Nếu thêm ALB/CloudFront, cần cấu hình lại nguồn IP đáng tin cậy trước; không bật
tin toàn bộ `X-Forwarded-For` từ Internet.

Chỉ Nginx publish cổng 80/443 ra ngoài khi bật profile `ec2`. Backend, frontend và
PostgreSQL chỉ bind các cổng host trên `127.0.0.1`; Redis không publish cổng.
Local vì vậy dùng `localhost:3001`, không truy cập trực tiếp qua IP LAN.
Security Group cho phép 80/443 theo nhu cầu;
không cần mở công khai 3000, 3001, 8000, 5432 hoặc 6379.

Mẫu `.env.ec2.example` đặt project, container PostgreSQL, volume và network riêng
để không trùng local. Giữ các tên này ổn định sau khi database đã có dữ liệu.
`COCO_ENV_FILE=.env.ec2` bảo đảm backend đọc đúng file EC2 khi dùng `--env-file`.
`COMPOSE_PROFILES=ec2` bật Nginx; `MARKETPLACE_TRUST_PROXY_HEADERS=true` bật IP ký.
Image ứng dụng không mang schema hoặc dữ liệu. Compose không mount `database/init`
và không chạy migration/seed.

Sau khi local đạt yêu cầu, chính người dùng xem lại và đưa đầy đủ mã nguồn lên Git
hoặc chuyển source/image sang EC2. Trước đó hai thư mục ứng dụng còn untracked;
không giả định clone repository sẽ có sẵn toàn bộ mã nguồn. Không chuyển `.env`
local, khóa AWS/SMTP hoặc certificate qua Git.

## 3. Các lệnh EC2 để người dùng tự chạy sau khi local đã đạt

Không chạy phần này trên máy local đang có dữ liệu. Trên EC2, từ thư mục repo,
sau khi tự chuẩn bị `.env.ec2` và certificate:

```bash
docker compose --env-file .env.ec2 -f docker-compose.yaml config --quiet
docker compose --env-file .env.ec2 -f docker-compose.yaml build backend frontend
docker compose --env-file .env.ec2 -f docker-compose.yaml up -d --wait postgres otp-redis
```

**Dừng tại đây để người dùng tự chuẩn bị schema/restore dữ liệu đã duyệt.**
Không có lệnh SQL hoặc script khởi tạo bảng tự động trong hướng dẫn này.
Giữ `MARKETPLACE_LEGACY_SCHEMA=true` nếu dùng schema legacy, và giữ checkout
options tắt cho đến khi người dùng xác nhận schema tương ứng đã sẵn sàng.

Chỉ sau khi database đã được chuẩn bị thủ công:

```bash
docker compose --env-file .env.ec2 -f docker-compose.yaml up -d --no-deps --wait --wait-timeout 120 backend frontend
docker compose --env-file .env.ec2 -f docker-compose.yaml run --rm --no-deps nginx nginx -t
docker compose --env-file .env.ec2 -f docker-compose.yaml up -d --no-deps nginx
docker compose --env-file .env.ec2 -f docker-compose.yaml ps
```

Mở domain HTTPS đã cấu hình. Kiểm tra đăng nhập, OTP và ảnh S3 trước khi cho khách
truy cập. Nếu dùng S3, quyền IAM, bucket CORS và nguồn phân phối ảnh phải được
người dùng cấu hình cho origin mới. Không coi kết quả trang chủ trả 200 là đủ để
xác nhận mọi chức năng hoạt động.

---

# Tài liệu đóng gói cũ — tham khảo lịch sử

Các ví dụ bên dưới phản ánh cấu hình đóng gói cũ, không thay thế quy trình local
và EC2 phía trên. Đặc biệt, file `docker-compose.otp.yaml` được nhắc trong lịch sử
không có trong cây thư mục đã kiểm tra; không dùng các lệnh đó cho bản hiện tại.

# Một file cấu hình, Docker image và đưa mã nguồn lên Git

Cập nhật 18/11/2026. Cấu hình private duy nhất trong dự án là **`.env` tại thư mục gốc**. `.env.example` là bản mẫu được đưa lên Git. Các file `.env.auth`, `.env.storage`, `.env.commerce`, `.env.otp` cũ đã được gộp; Compose không còn đọc chúng.

## Bạn cần làm gì trên máy hiện tại?

Ứng dụng tiếp tục dùng thông tin đăng nhập/S3/Brevo cũ. Không thay mật khẩu PostgreSQL vì việc gộp env. Khi chỉnh cấu hình, chỉ mở `.env` gốc.

```powershell
# Chỉ khi đã sửa env/code và muốn cập nhật ứng dụng:
docker compose -f docker-compose.yaml -f docker-compose.otp.yaml build backend frontend
docker compose -f docker-compose.yaml -f docker-compose.otp.yaml up -d --no-deps --wait backend frontend
```

Giữ PostgreSQL và Redis đang chạy. Không dùng `down -v` hoặc recreate database. PostgreSQL và frontend chỉ nhận các biến chỉ rõ trong Compose; toàn bộ file private chỉ được backend đọc. File `.env` không nằm trong Docker build context của hai image.

## Hai image đã tách riêng

| Image | Nội dung | Cổng nội bộ |
| --- | --- | --- |
| `coco-backend:2026.11.18` | FastAPI và thư viện Python | 8000 |
| `coco-frontend:2026.11.18` | Next.js standalone và tài nguyên giao diện | 3000 |

Image dành cho Linux; xem platform chính xác trong `manifest.json`. Hai image **không chứa database, dữ liệu S3, thông tin trong `.env`, volume PostgreSQL hoặc Redis**. Redis dùng image công khai `redis:7.4-alpine`, PostgreSQL hiện dùng `postgres:16`; đây là hai service phụ thuộc riêng.

Thư mục xuất: `artifacts/docker/2026.11.18/`:

- `coco-backend-2026.11.18.tar`
- `coco-frontend-2026.11.18.tar`
- `manifest.json`, `SHA256SUMS.txt`
- Compose, `.env.example` và hướng dẫn này.

Thư mục artifacts bị Git ignore. Khi có bản mới, đổi `COCO_IMAGE_TAG` trong `.env` sang phiên bản mới, rồi chạy từ thư mục dự án:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/package-images.ps1
```

Script build hai image, dùng `docker image save` trực tiếp ra file nhị phân và tạo SHA256. Không ghi secret ra console. Nếu image đã build đúng phiên bản, dùng thêm `-SkipBuild`. Không tự ghi đè archive đã tồn tại; chọn tag mới để giữ bản cũ.

## Chạy trên máy khác từ hai file tar

1. Cài Docker hỗ trợ Linux containers và Docker Compose v2. Clone mã nguồn từ Git hoặc chép các file Compose đi cùng bundle. Dùng máy cùng kiến trúc với manifest; khác kiến trúc cần build lại image cho máy đích.
2. Chép hai file tar và manifest/checksum sang máy đích. Truyền `.env` thật **riêng**, không qua Git. Nếu tạo cấu hình cho môi trường mới, chép `.env.example` thành `.env` rồi điền đủ thông tin; không chép đè `.env` đang có. Đảm bảo `COCO_IMAGE_TAG` khớp phiên bản archive.
3. Chuẩn bị database schema 25 bảng và dữ liệu trên máy đích bằng quy trình backup/restore riêng. Image ứng dụng không mang database; khởi động PostgreSQL trống sẽ không tự tạo dữ liệu. Giữ nguyên database trên máy hiện tại. Không đưa bản backup dữ liệu thật lên Git.
4. Cấu hình S3/Brevo và URL thật trong `.env`: `MARKETPLACE_PUBLIC_ORIGIN`, danh sách origin cho phép, DB credentials, JWT/OTP secret, S3 credentials/IAM role và SMTP login/key. Giữ `MARKETPLACE_LEGACY_SCHEMA=true` nếu database chưa áp các đề xuất checkout-options. Không tự bật đề xuất schema.
5. Nạp image:

```powershell
docker load --input coco-backend-2026.11.18.tar
docker load --input coco-frontend-2026.11.18.tar
```

Nếu chạy từ repository, thêm đường dẫn `artifacts/docker/2026.11.18/` trước tên tar. Có thể đối chiếu SHA256 bằng `Get-FileHash` với `SHA256SUMS.txt` trước khi nạp.

Sau khi PostgreSQL đã sẵn sàng trên network `marketplace_network`, chạy:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.otp.yaml up -d --no-deps --wait otp-redis
docker compose -f docker-compose.yaml -f docker-compose.otp.yaml up -d --no-build --pull never --no-deps --wait backend frontend
```

Lệnh `--no-build` dùng image đã load, không build lại. `--no-deps` không tạo lại PostgreSQL. Đường `postgres:5432` trong cấu hình hiện tại là PostgreSQL trong Compose network; nếu chuyển sang DB ngoài như RDS, cần điều chỉnh cấu hình kết nối theo môi trường trước khi chạy.

Mở `http://localhost:3001`. Kiểm tra `/health/ready` ở backend và đăng nhập/ảnh/OTP trên môi trường đích. Domain/IP/port mới phải khớp origin; production cần HTTPS. Chưa có triển khai AWS/registry push tự động trong lần đóng gói này.

## Đưa gì lên Git?

Đưa **mã nguồn và cấu hình mẫu**:

- `frontend/`: `src`, `public`, Dockerfile, `.dockerignore`, package.json/package-lock.json và config.
- `backend/`: `app`, `tests`, Dockerfile, `.dockerignore`, pyproject.toml/uv.lock và tài liệu/đề xuất SQL được rà soát. Đề xuất SQL chỉ là file review, không tự áp vào database.
- `tests/`, `scripts/`, `docs/`, `AGENT.md`, `AGENTS.md`, README, `.gitignore`, `.env.example`, hai file Compose.

Không đưa lên Git: `.env` thật, access/secret/SMTP/JWT/OTP keys, `.venv`, `node_modules`, `.next`, Docker tar trong `artifacts/docker/`, database dump/backup/volume hoặc thư mục backup cấu hình private.

Gợi ý lệnh từ thư mục repository (chỉ tự chạy sau khi đã xem danh sách file):

```powershell
git status --short
git add .gitignore .env.example README.md AGENT.md AGENTS.md docker-compose.yaml docker-compose.otp.yaml backend frontend docs tests scripts
git diff --cached --stat
git diff --cached --name-only
# Kiểm tra nội dung staged trong IDE, bảo đảm không có credential hoặc dữ liệu thật.
git commit -m "Prepare COCO marketplace apps and Docker release"
git push
```

Không dùng `git add -f .env`. Repository hiện có nhiều file app chưa được Git theo dõi; cần add mã nguồn, không chỉ Dockerfile. Agent không tự stage/commit/push trong lần chuẩn bị này. Không up tar image lên Git; chuyển file riêng hoặc dùng container registry khi bạn chọn nơi lưu.
