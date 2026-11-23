# Hiệu năng và nhiều backend — P8-03

Ngày 11/11/2026. Hoàn thành phạm vi đo local trên DB test; không phải sizing AWS, SLO production hoặc bằng chứng đã triển khai Auto Scaling.

## Kết quả

Hai tiến trình Uvicorn/FastAPI riêng, cùng PostgreSQL16 tmpfs marketplace_test trên Docker Desktop Windows. Dataset test2.000 sản phẩm, một shop APPROVED, một danh mục, không ảnh; không thay index/extension/schema nghiệp vụ. Warm mỗi backend một request trước đo. 120 request GET catalog chia đều2 backend,8 concurrent, page_size24, luân phiên trang1–4; không qua Next/load balancer/network Internet.

| Chỉ số | Lượt đo local |
| --- | ---: |
| Lỗi HTTP/projection | 0/120 |
| Thời gian workload | 0,451 giây |
| Throughput | 266,28 request/giây |
| p50 | 27,26 ms |
| p95 | 47,19 ms |
| Lớn nhất | 62,68 ms |

Giá trị có thể thay đổi theo máy/cache/Docker. Đây là baseline ngắn, không phải stress/soak test, không đo CPU/RAM saturation, WAN, S3 hoặc tải login Argon2. Không đặt ngưỡng PASS tốc độ dựa trên một máy; PASS là tính đúng đắn, không lỗi và phép đo tái lập.

## Tính đúng đắn giữa các tiến trình

- Cùng Buyer, cùng JWT secret/DB,4 checkout HTTP đồng thời chia2 process và cùng UUID key:1 response201,3 response200, cùng order_id; chỉ giảm tồn một lần từ10→9.
- Hai Buyer trên2 process tranh sản phẩm tồn1:1 response201,1 response409, tồn0, không âm; tổng chỉ2 order cho cả hai kịch bản.
- Dùng barrier trước HTTP, mỗi worker tự lấy CSRF cookie/token và giữ binding cùng access. Không dùng TestClient để thay thế hai backend process trong phép đo này.
- Uvicorn process thứ hai nhận tín hiệu đóng qua test-only file monitor (`server.should_exit`), exit0 sau lifespan; backend thứ nhất tiếp tục readiness200. Đây là graceful shutdown lúc idle, chưa mô phỏng rolling deploy có transaction đang chạy.
- Dừng đúng container PostgreSQL test có label của runner: backend thứ nhất live200/readiness503. Không tác động PostgreSQL nghiệp vụ.

Lượt harness đầu checkout bị CART_CHANGED vì fixture chứa thêm item ngoài payload; đã sửa fixture theo yêu cầu xác nhận toàn bộ giỏ. Các lượt cuối dùng đúng request nghiệp vụ, không nới validation production.

## Query plans và pool

Chạy EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) từ chính `ProductRepository.public_statement`, sort newest/ID và page_size24, sau ANALYZE bảng test. Trang1: execution3,722ms/planning0,582ms,24 rows/6.081 shared hits. Trang80: execution7,348ms/planning0,289ms,24 rows/9.873 shared hits. OFFSET sâu tăng công việc; baseline nhỏ chưa đủ căn cứ thêm index hay đổi pagination. SQL compile literal chỉ từ query/model nội bộ trong test, không nhận SQL từ HTTP. Full plans tại [performance-baseline.json](performance-baseline.json).

Mỗi backend process có pool_size5/max_overflow5, tức tối đa10 connection/process. Hai process tối đa20; N replica × W worker × (pool_size + overflow), cộng migration/test/admin/monitoring và dự phòng, phải nằm dưới ngân sách kết nối DB thực tế. Số pool này không chứng minh PostgreSQL chịu được tải tối đa. Không tự tăng max_connections/pool hoặc thêm PgBouncer trong lượt này. Session theo request, finally rollback/close, lifespan dispose; không lưu cart/idempotency/business lock trong process memory. Advisory/row locks và unique constraints ở PostgreSQL quyết định tính nhất quán.

## Chạy lại

Từ root sau khi `uv sync --locked` trong backend, có Docker với postgres:16:

```powershell
$env:E2E_SUITE='performance'
$env:E2E_DOCKER='C:/path/to/docker.exe' # bỏ nếu docker có trong PATH
$env:PERF_REPORT='C:/path/to/performance-report.json'
& backend/.venv/Scripts/python.exe tests/e2e/run.py
Remove-Item Env:E2E_SUITE
```

Không cần frontend/Node/Playwright cho mode này. Không cung cấp DSN nghiệp vụ: runner tạo DB/port/password/secret riêng. Report không chứa credential hoặc PII. Runner dọn đúng resource của mình cả khi assertion fail. Chạy browser tiếp theo phải bỏ E2E_SUITE hoặc đặt journey. Không dùng workload này trên DB hiện hữu.
