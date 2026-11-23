# Nghiệm thu FR-A01–04

Phạm vi: bảng yêu cầu và bốn quy tắc nghiệp vụ người dùng xác nhận. Không tự đổi trạng thái shop/tài khoản hoặc tạo danh mục trong DB nghiệp vụ để chứng minh chức năng.

| Mã | Giao diện | API và kiểm soát |
| --- | --- | --- |
| FR-A01 | `/admin/users`: danh sách, tìm kiếm, lọc, khóa/mở khóa có xác nhận | GET users, PATCH users/{id}/status; ADMIN ACTIVE, kiểm role/status DB, USER bị khóa mất quyền protected API ngay với token cũ |
| FR-A02 | `/admin/shops`: xem, tìm/lọc, duyệt/từ chối/khóa | GET shops, PATCH shops/{id}/status; chỉ ADMIN, expected_status chống thao tác trạng thái cũ; PENDING→APPROVED/REJECTED, APPROVED→LOCKED |
| FR-A03 | `/admin/products`: xem/tìm/lọc và xác nhận ẩn | GET products, POST products/{id}/hide; chỉ ADMIN, sản phẩm ẩn không còn trong tìm kiếm/detail công khai hoặc checkout mới |
| FR-A04 | `/admin/categories`: thêm/sửa/đổi cha/bật/tắt | GET/POST categories, PATCH categories/{id}; không cung cấp DELETE, giữ FK sản phẩm, không tạo vòng lặp; tắt cha ẩn cả nhánh công khai |

Các endpoint quản trị nằm dưới `/api/v1/admin`. API Seller/checkout kiểm độc lập tại backend; không chỉ ẩn nút trên UI. Guest401, USER/owner không phải ADMIN403. CSRF/Origin/no-store, xác nhận, lỗi/loading/empty/retry và không tự lặp mutation khi mất response được triển khai theo tài liệu từng chức năng.

Shop LOCKED không tạo/sửa sản phẩm hoặc điều chỉnh tồn, không nhận checkout mới; owner ACTIVE được xử lý đơn cũ. Ẩn sản phẩm/tắt danh mục không sửa order snapshot hoặc tự hoàn tồn. Không xóa danh mục đang có sản phẩm; vô hiệu hóa giữ nguyên product.category_id.

Giữ các quyết định trước: tài khoản ADMIN chỉ xem, không khóa/mở khóa Admin (người dùng đã chọn bỏ qua chính sách này). FR-A01 khóa/mở khóa áp dụng USER. Không tự thêm quyền Admin cho Seller hoặc miễn kiểm duyệt shop của Admin. Chưa có duyệt lại shop REJECTED/mở khóa shop LOCKED/bật lại sản phẩm ẩn; bảng yêu cầu hiện tại không yêu cầu các transition đó. Danh mục bị vô hiệu hóa có thể bật lại bằng PATCH.

Evidence: `backend/tests/integration/test_z_admin_requirements.py` kiểm liên thông cả bốn FR, Guest/Buyer/owner bị chặn, approve/reject/lock, lock/unlock USER, hidden search, create/edit/disable category, DELETE405 và FK/tồn giữ nguyên. Các bộ `test_admin_{users,shops,products,categories}_postgres.py`, `test_checkout_postgres.py`, `test_inventory_postgres.py` bổ sung rollback/concurrency, validation và quyền. Frontend có bốn nhóm admin client/proxy tests; browser journey có approve/hide/lock, các lượt P7 có evidence đầy đủ cho từng UI trong progress.

Chạy trên PostgreSQL16 tmpfs marketplace_test, metadata audit hiện hữu chỉ READ ONLY; không fixtures/DDL/seed trên dữ liệu thật. Kết quả lượt nghiệm thu ghi tại đầu [progress.md](progress.md). Kiểm chứng bốn FR không phụ thuộc có bucket: chỉ upload/delivery ảnh S3 thật vẫn chờ cấu hình.
