# P7-02 — Phê duyệt và khóa gian hàng

Đăng nhập bằng ADMIN ACTIVE, mở `/admin/shops` hoặc vào trang quản trị → **Gian hàng**. Hai mục Người dùng/Gian hàng dùng điều hướng chung; trang `/admin` vẫn về quản lý người dùng. Guest đăng nhập giữ returnTo `/admin/shops`; USER/Seller không truy cập được dữ liệu quản trị.

Tìm theo tên, slug hoặc email liên hệ, lọc bốn trạng thái, phân trang24 shop. Mỗi hồ sơ hiển thị owner ID, contact email, mô tả và timestamps riêng cho quản trị; không email/phone tài khoản chủ shop hay password/raw storage key. Logo URL vẫn null theo phạm vi upload logo chưa có.

## Chuyển trạng thái

| Hiện tại | Thao tác | Kết quả |
| --- | --- | --- |
| PENDING | Phê duyệt | APPROVED, được bán sản phẩm đủ điều kiện |
| PENDING | Từ chối | REJECTED, không có gửi duyệt lại ở bản này |
| APPROVED | Khóa gian hàng | LOCKED, không nhận đơn mới/sửa catalog/tồn |
| LOCKED/REJECTED | Không có thao tác tiếp | Không mở khóa/resubmit/reactivation |

Mọi thao tác có xác nhận tên/ID/trạng thái. Không tự duyệt hoặc khóa một shop nghiệp vụ trong lúc triển khai. Shop LOCKED vẫn cho owner ACTIVE xử lý đơn cũ, không tự hủy đơn/hoàn tồn. Owner LOCKED không dùng protected API; mở khóa user không đồng nghĩa mở khóa shop.

## API và transaction

- `GET /api/v1/admin/shops?q=&status=PENDING&page=1&page_size=24`: items/page/page_size/total; q≤200, status tùy chọn enum, page1..2147483647/page_size1..100. Tìm không phân biệt hoa/thường, escape literal `%`, `_`, `\`. Sắp xếp created_at DESC,shop_id DESC, count + một page query, không N+1.
- `PATCH /api/v1/admin/shops/{shop_id}/status`: body chỉ expected_status/shop_status. Response envelope data ShopPrivate gồm ID chuỗi BIGINT và timestamps UTC. Input/extra sai422, missing404, stale/transition sai409 INVALID_TRANSITION. Target đã là hiện tại trả no-op200 kể cả expected cũ; không ghi timestamp lại.
- ADMIN ACTIVE đọc từ DB, không tin role client/JWT; USER/Seller403, guest401, role bị thu hồi hoặc user khóa bị từ chối. Seller không tự approve bằng API Admin hoặc chèn status vào PATCH hồ sơ riêng.

Read READ ONLY, private no-store. Mutation dùng WriteAccess cookie/CSRF/Origin, khóa user Admin → shop đến COMMIT; conditional UPDATE source→target. Checkout khóa cùng shop trước kiểm trạng thái: nếu khóa commit trước thì checkout bị409, nếu checkout commit trước thì giữ đơn đã đặt. Không thay product/inventory/order hay giá snapshot. Lỗi DB/COMMIT503 sanitized và rollback; repository không commit.

Next proxy giới hạn route/method/ID/query/body/cookie, không chuyển credentials tùy ý. Client dùng chung shape riêng shop, kiểm ID/owner/enum/date/page/filter/duplicates và loại raw fields. Khi stale/lỗi/mất phản hồi, xóa kết quả/xác nhận cũ, yêu cầu tải lại để xác minh; không tự retry mutation. Account/role/expiry thay đổi xóa dữ liệu riêng, response muộn bị bỏ qua; không PII/token browser storage.

## Kiểm chứng

PASS401 backend full PostgreSQL16 tmpfs marketplace_test riêng và metadata audit DB hiện hữu READ ONLY;16 cases mới cho ma trận16 trạng thái, stale/no-op, readonly/search/page/shape/no N+1, permissions/Seller self-approval, validation, rollback, approve-vs-reject đồng thời, khóa đua checkout không có đơn dở/oversell và đơn cũ vẫn xử lý. Lượt full có3 Pydantic UnsupportedFieldAttributeWarning trong tests concurrent hiện hữu, không fail/skip. Sau khi chỉnh test timestamp lấy sau COMMIT fixture, chạy riêng16 tests Admin shops PASS. Ruff check/format PASS116 files, không schema/dependency changes.

PASS69 frontend tests, thêm4 nhóm projection/client/proxy/returnTo, lint/typecheck/production build và Docker backend/frontend build. Browser thật Next→FastAPI→PostgreSQL test PASS Admin approve/reject/lock, Seller không tự duyệt, sản phẩm được bán sau approve, khóa làm checkout mới409/catalog404/Seller catalog403 nhưng đơn cũ CONFIRMED được, không mở khóa, mất phản hồi COMMIT→GET xác minh không replay, stale409,27 shops phân trang/filter/empty,503 retry/expiry/privacy/login returnTo và320/390/768/1440 không overflow/JS errors. Đã xem ảnh desktop/mobile.

Harness/screenshots `D:/HealthBeauty/.p702-*`, `p702-shops-390.png`, `p702-shops-1440.png`; fixtures/bulk chỉ tạo trên test DB được guard. Tài nguyên test riêng được dọn. Live localhost guest page/navigation/returnTo/API401/query400/hostile403/readiness200 PASS; không đăng nhập thay Admin thật hoặc sửa shop nghiệp vụ.

Chỉ build/up app --no-deps healthy, giữ baseline PostgreSQL ID/StartedAt/mount/config/root.env hash/volume/network. Không DDL/seed/root.env/Compose/dependency/Terraform/AWS/commit/push. P7-03 sản phẩm và P7-04 danh mục chưa triển khai; S3 còn chờ bucket. NOT RUN tải cao/HTTPS/điện thoại vật lý.
