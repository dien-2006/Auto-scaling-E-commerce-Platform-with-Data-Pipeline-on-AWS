# E2E không cần bucket

Cập nhật14/11/2026: runner tạo schema từ SQL25bảng đã review trong backend/tests/fixtures, chỉ trong tmpfs marketplace_test mới của runner. Mode E2E_SUITE=crud kiểm UI CRUD cảshop/product; k6 kiểm client ngoài container qua web; bỏbiến hoặc đặtjourney khi chạy hành trình cũ. Full backend/reference schema dùng tests/schema25/run.py. [Hướng dẫn mới](../../docs/schema25-crud-k6.md) ghi rõ identity liveBYDEFAULT khác sourceALWAYS và phần AWS chưa kiểm.

P8-02, 11/11/2026. Bộ `journey.cjs` chạy Chromium thật qua Next production → FastAPI → PostgreSQL16 riêng. Không cần mật khẩu tài khoản thật hoặc dữ liệu nghiệp vụ. Dữ liệu có nhãn E2E và được xóa cùng container test.

## Chuẩn bị và chạy

Cần Docker đang chạy với image `postgres:16`, Python/uv và Node24 theo repo. Đồng bộ backend bằng `uv sync --locked`; trong frontend dùng `npm ci` và `npm run build`. Cần Playwright cùng Chromium hoặc Chrome có sẵn. Playwright là công cụ E2E bên ngoài, không thêm vào dependency production.

Ví dụ PowerShell từ root, sau khi đã cài Playwright vào thư mục công cụ riêng:

```powershell
$env:E2E_NODE = 'C:/path/to/node.exe'
$env:E2E_DOCKER = 'C:/path/to/docker.exe'
$env:PLAYWRIGHT_MODULE = 'C:/path/to/tools/node_modules/playwright'
$env:E2E_CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:E2E_ARTIFACTS = 'C:/path/to/e2e-artifacts'
New-Item -ItemType Directory -Force $env:E2E_ARTIFACTS | Out-Null
& backend/.venv/Scripts/python.exe tests/e2e/run.py
```

`E2E_NODE`/`E2E_DOCKER` có thể bỏ nếu có trong PATH. `PLAYWRIGHT_MODULE` có thể bỏ nếu Node resolve được package `playwright`; `E2E_CHROME` có thể bỏ khi Playwright đã cài Chromium. Thư mục ảnh chụp là tùy chọn, phải tạo trước và nên ở ngoài repo.

Runner tự chọn port loopback, tạo PostgreSQL tmpfs512MiB với tên UUID/label riêng, database `marketplace_test`, JWT secret/password ngẫu nhiên và hai app process riêng. Không đọc root .env; bỏ biến MARKETPLACE_/AWS_ kế thừa của child services, không cấu hình bucket. Chỉ tạo schema trong DB test vừa tạo. Script nâng quyền Admin chỉ nhận email `e2e-admin-…` và từ chối môi trường khác test/marketplace_test/127.0.0.1. Không dùng script này cho tài khoản nghiệp vụ.

Khi kết thúc hoặc lỗi kiểm thử thông thường, runner dừng đúng process mình tạo và chỉ xóa container có tên/label của mình. Nếu máy hoặc tiến trình runner bị tắt cưỡng bức, kiểm tra tài nguyên `marketplace-p802e2e-*` trước khi dọn thủ công; không dọn container/volume nghiệp vụ.

## Evidence và giới hạn

- Guest tìm sản phẩm bằng form, mở detail và thấy placeholder thật khi không ảnh.
- Buyer login bằng form về trang chủ; bàn phím sửa số lượng → Tab → Enter thêm giỏ; giỏ rỗng, thiếu địa chỉ chặn đặt hàng; tạo địa chỉ bằng UI → checkout COD → xác nhận tổng/quantity.
- Admin phê duyệt shop bằng UI; Seller xác nhận/giao/hoàn tất; Buyer theo dõi trạng thái. Admin không bypass quyền Seller hoặc đọc đơn Buyer khác.
- Admin ẩn sản phẩm/khóa shop qua UI; public404, đơn cũ giữ tổng và item snapshot, tồn còn đúng8 sau mua2 từ10.
- Seller quản lý ảnh hiển thị thiếu cấu hình và upload disabled; đã sửa fieldset/file input tràn ngang ở320px.
- Chặn response cart trong browser để quan sát loading, trả503 để kiểm error rồi bỏ chặn/reload phục hồi giỏ rỗng. Đây là fault injection trong test, không phải response giả production.
- Phiên hết hạn không hiển thị thông tin nhận hàng. Bảy màn hình kiểm không tràn ở320/390/768/1440; ảnh390/1440 khi có E2E_ARTIFACTS. Page JavaScript errors phải rỗng.

Shop/product/category và tài khoản được chuẩn bị qua API thật; riêng quyền Admin được cấp bằng fixture DB test. Không tuyên bố mọi bước đăng ký shop/tạo sản phẩm/danh mục đều được thao tác bằng UI trong bộ này; các bộ kiểm thử task trước có evidence riêng.

PASS lượt cuối: Chrome headless, không JS errors; đã xem ảnh Seller quản lý ảnh và checkout mobile. Lượt bàn giao đã kiểm thêm header nosniff/frame DENY/referrer/permissions qua response thật và chạy với Pillow13. NOT RUN S3 thật/URL ảnh sản phẩm trả lỗi từ storage, HTTPS, thiết bị vật lý, browser khác. P8-02 giữ IN_PROGRESS với phần ảnh thật còn chờ P6-03; phần độc lập không bucket đã kiểm tra. Đây không phải chứng nhận hệ thống sẵn sàng production. Đo tải/hai process chạy riêng qua [performance.md](../../docs/performance.md), đặt E2E_SUITE=performance rồi bỏ biến này khi chạy lại journey.
