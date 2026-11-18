# P7-04 — Quản lý cây danh mục

Đăng nhập ADMIN ACTIVE và mở `/admin/categories`, hoặc chọn **Danh mục** trong điều hướng quản trị. Bấm **Thêm danh mục**, nhập tên/đường dẫn, chọn danh mục cha hoặc để danh mục gốc, chọn trạng thái bật rồi **Kiểm tra thay đổi → Xác nhận lưu**. Bấm Chỉnh sửa để đổi thông tin, chuyển cha, đưa về gốc hoặc bật/tắt.

Giao diện hiển thị cấp, ID, đường dẫn nhánh và trạng thái riêng. Danh mục con đang bật vẫn bị ẩn khỏi mua sắm nếu có cha đang tắt; trạng thái này được ghi rõ. Ô chọn cha loại chính danh mục đang sửa và toàn bộ con/cháu, nhưng server vẫn kiểm lại cây mới nhất để ngăn form cũ tạo vòng lặp.

Tắt một node không sửa is_active của con/cháu, không xóa danh mục, không đổi category_id của sản phẩm hay hủy/hoàn tồn đơn. Bật lại node khôi phục hiển thị các nhánh con vốn đang bật, theo điều kiện shop/sản phẩm hiện hành; không bật lại sản phẩm đã ẩn. Danh mục inactive vẫn có thể là cha để Admin tổ chức dữ liệu trước khi công khai.

## API và validation

- `GET /api/v1/admin/categories`: `{items:CategoryTree[]}` gồm toàn bộ node active/inactive; root/children theo category_name ASC,category_id ASC của DB. Một query danh mục, không N+1, READ ONLY/no-store.
- `POST /api/v1/admin/categories`: category_name1..120 trim, category_slug1..140 lowercase ASCII chữ/số chia bằng gạch nối đơn, parent_category_id BIGINT dương hoặc null, is_active boolean strict (mặc định true). Trả201 envelope data Category.
- `PATCH /api/v1/admin/categories/{id}`: chỉ các trường trên, ít nhất một trường; parent_category_id=null đưa về gốc. Các trường khác không được null. Trả200 envelope data Category. Mutation trả node với children=[]; GET lại để có cây đầy đủ.
- Slug duy nhất toàn hệ thống, trùng409 SLUG_EXISTS; parent thiếu422 INVALID_PARENT; self-parent/cycle409 CATEGORY_CYCLE; target thiếu404; extra/sai kiểu/null sai422. Không delete endpoint. Đổi slug không tạo redirect từ slug cũ, ID và liên kết sản phẩm giữ nguyên.
- Giới hạn kỹ thuật100 cấp khớp public client hiện có (depth0..99), vượt422 CATEGORY_TOO_DEEP. GET gặp cây hỏng/cycle không bỏ node âm thầm hoặc tự sửa; trả lỗi INVALID_CATEGORY_TREE/CATEGORY_CYCLE để xử lý dữ liệu có chủ đích.

Chỉ ADMIN ACTIVE theo DB mới đọc/ghi; USER/Seller403, guest401, user khóa/role bị thu hồi bị từ chối. POST/PATCH cookie/CSRF/Origin; proxy từ chối query vì route không nhận bộ lọc. Không dùng role client hoặc JWT cũ thay kiểm DB.

## Đồng thời và transaction

Mutation khóa user rồi `pg_advisory_xact_lock(731921,1)` exclusive, đọc lại toàn bộ mapping parent sau khi có khóa. Checkout, Seller products, inventory và Admin hide dùng shared lock cùng namespace/key theo thứ tự chung. Hai Admin chuyển cha chéo nhau sẽ được serialize; request sau kiểm mapping đã commit, từ chối cycle. Không lock cây trong bộ nhớ process.

Kiểm tra toàn bộ cấu trúc đề xuất trước flush (cả depth của nhánh con khi reparent), parent existence/slug và constraint unique cuối tại DB. Repository không commit; giữ transaction qua COMMIT, lỗi503 sanitized và rollback. Không DDL/FK/trigger/sequence reset hoặc tự sửa dữ liệu có sẵn. Nếu tắt danh mục commit trước checkout thì checkout từ chối; đơn đã commit trước vẫn dùng snapshot cũ.

Không có expected_version trong contract. Sửa đồng thời được serialize và bảo toàn cấu trúc, nhưng cập nhật hồ sơ sau cùng có thể ghi đè trường cùng tên; không tuyên bố phát hiện mọi stale edit. Client không tự retry mutation. Sau lỗi/mất phản hồi, bỏ xác nhận/dữ liệu cũ, yêu cầu GET để xem đã tạo/lưu chưa; không tự tạo lại slug. Account/role/expiry thay đổi xóa dữ liệu riêng, bỏ response đến muộn và không lưu token/PII vào browser storage.

## Kiểm chứng

PASS438 backend full PostgreSQL16 tmpfs marketplace_test riêng + metadata audit hiện hữu READ ONLY;21 cases mới cho create/patch/root/parent inactive/public visibility, self/multinode cycle, reparent từ hai Admin khác nhau, slug race, tắt nhánh giữ product/stock/order và đua checkout atomic, quyền/CSRF/validation/no delete/COMMIT rollback/100-level boundary. Có3 Pydantic alias warnings payload/item_id trong concurrent tests, không fail/skip. Ruff check/format PASS127 files.

PASS77 frontend tests, thêm4 nhóm tree/ID/parent/duplicate/depth/inherited visibility, descendant exclusions, client no retry/allowlisted fields và proxy/returnTo/security. Lint/typecheck/production build/Docker backend/frontend build PASS.

Browser thật Next→FastAPI→PostgreSQL test PASS empty→create parent/child, slug gợi ý tiếng Việt, loại self/descendant khỏi lựa chọn cha, edit/reparent/về gốc, tắt/bật nhánh ảnh hưởng catalog/cart/checkout nhưng giữ đơn cũ; Seller403; stale form tạo cycle409; response mất sau COMMIT rồi GET đúng1 bản ghi không replay; slug trùng409,503 retry/expiry/privacy/login returnTo và320/390/768/1440 không overflow/JS errors. Đã xem ảnh desktop/mobile. Harness/screenshots `D:/HealthBeauty/.p704-*`, `p704-categories-390.png`, `p704-categories-1440.png`; resources test riêng đã dọn.

Live localhost guest UI/login returnTo/navigation/API401/query400/hostile403/readiness200 PASS. Chỉ app build/up --no-deps healthy; baseline PostgreSQL ID/StartedAt/mount/config/root.env hash/volume/network bảo toàn. Không đăng nhập thay Admin thật, tạo danh mục mẫu hoặc sửa danh mục nghiệp vụ. Không schema/data/seed/env/Compose/dependency/Terraform/AWS/commit/push. NOT RUN load/HTTPS/điện thoại vật lý; S3 còn chờ bucket, P8 tổng thể chưa triển khai.
