# Schema 25 bảng, CRUD Seller và k6

Ngày14/11/2026. Yêu cầu người dùng: cập nhật schema25bảng, CRUD cho cả gian hàng và sản phẩm; k6 gọi web qua Internet theo sơ đồ AWS. Không triển khai AWS hoặc chạy SQL trên DB nghiệp vụ trong lượt này.

## Schema và phạm vi chức năng

Nguồn được đọc đầy đủ: `C:/Users/ADMIN/Downloads/coco_marketplace_25_tables.sql`. Bản tham chiếu để test tại [marketplace_25.sql](../backend/tests/fixtures/marketplace_25.sql). Có25bảng/182cột/27index khai báo tường minh. Model12bảng lõi được giữ; bổ sung mapping metadata cho13bảng audit/history/coupon/review/payment/shipping trong models/extensions.py. Không chạy reflection/create_all/migration trong startup.

Order thêm discount_amount/shipping_fee mặc định0, payment_method VARCHAR20 và constraint nguồn COD/VNPAY/MOMO. **Checkout hiện vẫn chỉ cho COD mô phỏng**, chưa tự tích hợp cổng thanh toán/voucher/phí giao hàng. Mapping13bảng không đồng nghĩa đã có UI/API hoặc tự ghi audit/price/inventory/approval history; phần đó cần task nghiệp vụ riêng. Không nhập review/coupon/payment giả hoặc đọc private audit data ra API công khai.

DB hiện hữu đã có25bảng nhưng24cột identity đang là BY DEFAULT; SQL gửi dùng ALWAYS. Giữ nguyên DB và sequence; ứng dụng tạo dữ liệu bằng ID tự sinh, không chấp nhận ID tùy ý từ payload. Đây là khác biệt metadata **chưa được sửa**. Lượt audit strict trực tiếp DB hiện hữu phát hiện identity mismatch; không gọi đó là đã khớp100%. Bộ460tests sau đó chạy trên schemaSQL gốc trong DB test riêng, không thay expectation identity để che chênh lệch live. Cần quyết định nguồn chuẩn/migration riêng nếu muốn đồng nhất hai cách sinh ID.

## CRUD gian hàng

| Thao tác | API dưới /api/v1 | Quy tắc |
| --- | --- | --- |
| Tạo | POST /seller/shop | USER ACTIVE, một owner một shop; luôn PENDING |
| Xem | GET /seller/shop | Chỉ hồ sơ của mình |
| Sửa | PATCH /seller/shop | Tên/mô tả/email; không tự đổi owner/status/slug |
| Xóa | DELETE /seller/shop/{shop_id} | Chỉ shop mình và chưa có FK tham chiếu;204 hoặc409 SHOP_IN_USE |

Giao diện `/kenh-nguoi-ban`: có nút Xóa gian hàng và xác nhận riêng. API xóa gắn đúng ID; nếu shop cũ đã xóa và tạo lại, request/tab cũ404, không xóa shop mới. Shop còn sản phẩm/đơn/approval history/coupon hoặc liên kết khác không được xóa. Không cascade xóa sản phẩm/đơn để đạt CRUD; muốn bỏ shop đang có lịch sử cần thiết kế lưu trữ riêng. Admin vẫn không được tạo shop hoặc mua hàng theo quy tắc trước.

## CRUD sản phẩm

| Thao tác | API dưới /api/v1 | Quy tắc |
| --- | --- | --- |
| Tạo/xem/sửa | POST collection, GET list/detail, PATCH /seller/products/{id} | Owner ACTIVE/shop APPROVED, validation như trước |
| Xóa | DELETE /seller/products/{id} | Owner/shop APPROVED; không còn FK từ cart/order/history/... |

Giao diện `/kenh-nguoi-ban/san-pham`: nút Xóa sản phẩm riêng với Ẩn. DELETE thành công204 xóa product, inventory tương ứng và reference ảnh qua FK cascade hiện có. Không gọi xóa object S3. Có giỏ/đơn/price history/inventory history/review hoặc FK khác thì409 PRODUCT_IN_USE; transaction rollback cả inventory, không mất tồn và không mất liên kết. Sản phẩm đã sử dụng có thể Ẩn thay vì xóa. Product/Inventory locks theo thứ tự user→category→shop→product→inventory đếnCOMMIT, FK là guard cuối.

UI có busy/confirm, lỗi409 rõ nghĩa; client hiểu204 không JSON. Không tự retry DELETE khi response mất; yêu cầu đọc lại trước thao tác tiếp. CSRF/Origin/no-store và ownership backend giữ nguyên. Category không có DELETE; quy tắc bảo toàn liên kết vẫn giữ.

## k6 truy cập web và AWS

Thêm GET `/api/v1/products` và `/{id}` trên cùng origin Next: fixed upstream/path, allowlist/bounds query, bỏ Cookie/Authorization khi forward catalog. Các API riêng vẫn yêu cầu session/CSRF. k6 HTTP không cần bỏ CSRF hoặc nới CORS; cookie jar của từng VU giữ cookie, POST cần lấy token và gửi Origin đúng cấu hình. Tham khảo [Grafana cookies](https://grafana.com/docs/k6/latest/using-k6/cookies/), [biến môi trường](https://grafana.com/docs/k6/latest/using-k6/environment-variables/).

Theo sơ đồ, k6 ở ngoài AWS → Internet → URL public/HTTPS/load balancer → web/API. K6 từ EC2 hoặc Grafana Cloud không gọi localhost hoặc IP LAN máy phát triển. Cần cung cấp domain/ALB URL thực tế để xác minh DNS/TLS/Ingress/security groups. Hai app phải cấu hình PUBLIC_ORIGIN khớp domain, không tin Host tùy ý; các backend replica phải dùng cùng JWT signing key để cookie/CSRF dùng được khi request đổi replica. Không mở PostgreSQL ra Internet, không thêm IP wildcard hoặc bỏ auth riêng cho k6. Chưa thay Terraform, IAM, ALB, EKS, autoscaler, replicaDB hoặc ETL.

Script [web-smoke.js](../tests/k6/web-smoke.js) bắt buộc BASE_URL; mặc định1VU/5iterations, chỉ GET public và POSTlogin bodyrỗng để kiểm CSRF→422, guestAdmin401. Không tạo account, mua hàng hoặc đổi tồn. Các expected401/422 được đánh dấu responseCallback, không che lỗi unexpected. Tăng tải chỉ khi TEST_ENV=isolated/staging, giới hạn20VU/1000iterations; không dùng để tự stress DB nghiệp vụ. Đây là smoke HTTP, không đo render browser/AutoScaling/S3 hoặc checkout load.

Ví dụ **sau khi có URL staging được chỉ định** và cài k6:

```powershell
k6 run -e BASE_URL=https://YOUR_STAGING_DOMAIN tests/k6/web-smoke.js
```

Tạo smoke cô lập local bằng Docker k6, không cần URL AWS:

```powershell
$env:E2E_SUITE='k6'
# E2E_NODE/E2E_DOCKER nếu không có trong PATH
& backend/.venv/Scripts/python.exe tests/e2e/run.py
Remove-Item Env:E2E_SUITE
```

Runner dùng k6v2.4.0 image digest đã kiểm, frontend process test bind0.0.0.0 trên port ngẫu nhiên để container gọi host.docker.internal, PUBLIC_ORIGIN riêng của app test được truyền tường minh. Không sửa binding/service/volume mạng nghiệp vụ. Bản desktopk6 hoặc Docker được Grafana hỗ trợ: [cài k6](https://grafana.com/docs/k6/latest/set-up/install-k6/).

## Kiểm chứng

- PASS460 backend tests gồm metadata columns/defaults/identity/constraints/indexes trên **SQL nguồn** trong PostgreSQL16marketplace_test tmpfs; tạo từ file trước test và không trỏ audit tới DB nghiệp vụ. Runner [tests/schema25/run.py](../tests/schema25/run.py); không fail/skip/warning lượt cuối.
- PASS80frontend tests/lint/typecheck/production build:3nhóm mới về publicproxy/private-cookie stripping, DELETE204/BIGINT/no replay, và CSRF/query/ownership-path proxy.
- PASS browserCRUD trên schemaSQL25: tạo/xem/sửa/xóa shop, tạo lại/staleID không xóa nhầm, productUIcreate/read/edit/delete, productcógiỏ409/giữtồn, shopcóproduct409;320/390/768/1440,khôngJSerrors. Đã xem screenshot confirm shop/product mobile, chỉnh spacing/nút shop và kiểm lại PASS.
- PASS journeyBuyer/Seller/Admin hiện hữu trên schemaSQL25 và Docker build. Tài khoản Admin không mua/tạo shop vẫn được kiểm ở journey.
- PASS k6container độc lập:25/25checks,0unexpectedHTTPerrors,5iterations/1VU trên testDB. Lượt đầucatalog404 do thiếu NextpublicAPI, đã thêmGETroute/test và chạy lại PASS. **NOT RUN từ AWS/Grafana Cloud hoặc URL public thực** vì chưa cóURL/hạ tầng.

E2E modes: `journey`, `crud`, `k6`, `performance`; tất cả schema test hiện dùng SQL25bảng trên tmpfs riêng. Tests không tạo dữ liệu bán hàng trong DB thật. Kiểm tra runtime và bảo toàn PostgreSQL ghi trong progress.
