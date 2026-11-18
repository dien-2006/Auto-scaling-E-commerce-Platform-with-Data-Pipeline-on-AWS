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
