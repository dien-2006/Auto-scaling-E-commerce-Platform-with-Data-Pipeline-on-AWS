# k6 qua cùng URL web

Xem [schema25/CRUD/k6](../../docs/schema25-crud-k6.md) cho kiến trúc AWS, cấu hình origin, kết quả và giới hạn.

```powershell
k6 run -e BASE_URL=https://YOUR_STAGING_DOMAIN tests/k6/web-smoke.js
```

Mặc định1VU/5iterations,25checks; không đăng ký tài khoản, đặt hàng hoặc thay đổi tồn. PubliccatalogGET/cookie-CSRF loginvalidation/guestAdmin denial được kiểm. K6 quản lý cookies theoVU; APIprivate không có đường bypass. BASE_URL bắt buộc, root origin không chứacredential/path/query. PUBLIC_ORIGIN mặc định bằngBASE_URL; override chỉ khi testcontainer dùng host.docker.internal để gọi app có origin riêng được cấu hình rõ ràng.

Load tùy chọn: `-e TEST_ENV=staging -e VUS=5 -e ITERATIONS=50`, chỉ môi trường test được chỉ định; các giới hạn không phải chứng nhận capacity/AutoScaling. Không dùng chính sách này để tự chạy stress lên DB nghiệp vụ. Không cần sửa CORS để chạy k6HTTP.

Smoke cô lập đã chạyPASS bằng `E2E_SUITE=k6` trên tests/e2e/run.py, Dockerk6v2.4.0 digestpin, Nextproduction/FastAPI/PostgreSQL16SQL25bảng test riêng. Chưa chạy từAWS/GrafanaCloud vì chưa cópublicURL. LAN/localhost không phảiURLpublic theo sơ đồ. Không cóAWSresource/Terraform/firewall được thay trong task.
