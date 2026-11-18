# P7-01 — Quản lý người dùng

Mở `/admin/users` bằng tài khoản ADMIN đang ACTIVE, hoặc chọn **Quản lý người dùng** trong trang Tài khoản. `/admin` chuyển về trang này. Guest có liên kết đăng nhập giữ returnTo; USER thấy không có quyền truy cập, không gọi danh sách riêng. Backend luôn đọc lại vai trò/trạng thái trong DB; ẩn nút trên giao diện không thay thế kiểm quyền API.

Cập nhật theo yêu cầu trực tiếp cấp quyền: có [CLI cấp ADMIN local](grant-admin.md) với preview và expected user ID. Chỉ thực thi cho email tài khoản đã được chủ dự án chỉ định; không tự bootstrap từ danh sách user hoặc thêm API tự nâng quyền. Không thay phạm vi tài khoản Admin chỉ xem trong UI P7-01.

Tìm theo tên, email hoặc số điện thoại, lọc ACTIVE/LOCKED, phân trang24 người dùng. Từ khóa tối đa200 ký tự, tìm không phân biệt hoa/thường; `%`, `_`, `\` được hiểu là ký tự thật. Sắp xếp created_at DESC rồi user_id DESC. Không tự tạo tài khoản quản trị hoặc nâng quyền tài khoản hiện hữu.

Theo yêu cầu người dùng “bỏ qua phần đó” sau khi giải thích các lựa chọn khóa Admin, phạm vi P7-01 bỏ thao tác đổi trạng thái tài khoản ADMIN: chỉ xem Admin, không khóa/mở khóa Admin, kể cả chính mình. API từ chối403 `ADMIN_PROTECTED` cho mọi đổi trạng thái target ADMIN; UI nút **Admin chỉ xem** bị vô hiệu hóa. Quy trình quản lý trạng thái Admin cần yêu cầu riêng sau này; không coi đây là người dùng đã chọn chính sách khóa Admin vĩnh viễn.

## API và dữ liệu

- `GET /api/v1/admin/users?q=&status=ACTIVE&page=1&page_size=24`: trả `items,page,page_size,total`; q/status tùy chọn, page1..2147483647, page_size1..100. Query lạ/giá trị sai bị từ chối.
- Mỗi AdminUser chỉ có user_id chuỗi BIGINT, email, full_name, phone nullable, user_role USER/ADMIN, user_status ACTIVE/LOCKED và created_at UTC. Không password_hash/token/owned_shop, không tải password_hash trong truy vấn quản trị. Chỉ Admin được xem PII phục vụ chức năng này.
- `PATCH /api/v1/admin/users/{id}/status`: body chỉ `{ "user_status": "LOCKED" }` hoặc ACTIVE; envelope `data` AdminUser. Không role/email/password hay mass assignment. Target thiếu404, input sai422, target ADMIN403. Trạng thái đã giống target trả no-op200, không đổi updated_at.
- Guest401; USER403; Admin bị khóa403 USER_LOCKED; vai trò bị thu hồi có hiệu lực ở request tiếp theo dù JWT còn hạn. Cookie/CSRF/Origin bắt buộc cho mutation, no-store cho dữ liệu riêng.

Read dùng transaction READ ONLY, count + một page query, không N+1. Mutation kiểm quyền trước khóa, khóa actor và target user theo ID tăng dần rồi kiểm lại quyền/status sau khi đợi; giữ khóa đến COMMIT. Repository không commit. Lỗi DB/COMMIT trả503 đã làm sạch và rollback, không trả200 trước COMMIT.

Khóa USER chặn protected API tiếp theo, giữ nguyên shop/catalog/đơn/dữ liệu và role; không hủy giao dịch đã hoàn tất. Mở khóa USER không mở khóa shop. JWT chưa hết hạn có thể dùng tiếp sau khi mở khóa vì mỗi request kiểm DB; không tuyên bố revoke copied JWT. Endpoint đặt trạng thái tuyệt đối, không nhận expected_status; request hợp lệ thực thi sau cùng quyết định trạng thái khi hai Admin cập nhật ngược nhau.

## Giao diện và phục hồi

Khóa/mở khóa USER có bước xác nhận tên/email, chặn submit lặp, loading/empty/error/retry. Client kiểm tra ID, enum, timestamp, trang/filter/duplicate và projection; proxy chỉ route/query/method/cookie được cho phép. Không lưu PII/token vào browser storage.

Không tự retry mutation. Sau lỗi hoặc mất phản hồi, bỏ dữ liệu/xác nhận cũ, yêu cầu tải lại để xem thao tác đã lưu hay chưa. Đổi account, role hoặc hết phiên xóa danh sách riêng; các response đến muộn bị bỏ qua và request chờ bị hủy khi unmount.

## Kiểm chứng và giới hạn

PASS374 backend full trên PostgreSQL16 tmpfs `marketplace_test` riêng và audit metadata DB hiện hữu READ ONLY;16 test cases mới gồm search/escape/pagination/projection/READ ONLY/no password query, role/status/CSRF, lock/unlock token cũ, bảo toàn shop, target ADMIN read-only, rollback COMMIT và hai Admin cập nhật cùng user. Ruff check/format PASS; không dependency/schema changes.

PASS65 frontend tests cho projection/validation/client/no retry/proxy/returnTo, lint/typecheck/production build/Docker build. Bằng chứng browser/runtime và giới hạn được cập nhật ở [progress.md](progress.md). Harness riêng `D:/HealthBeauty/.p701-*`; fixture nâng quyền chỉ dùng DB test đã kiểm tên/host/environment, không dùng DB nghiệp vụ.

PASS browser thật với27 tài khoản test: phân trang/search/status/empty, khóa/mở USER và kiểm JWT đang có, mất phản hồi sau COMMIT rồi đọc lại không lặp mutation, Admin chỉ xem/API403,503 recovery, demote/expiry privacy và login returnTo, bốn viewport320/390/768/1440 không overflow/JS errors. Đã xem ảnh desktop/mobile. PASS live localhost guest page/redirect/login returnTo/API401/query400/hostile403/readiness200; chỉ app build/up --no-deps healthy, baseline PostgreSQL ID/start/mount/config/root.env/volume/network giữ nguyên. Không fixture hay mutation nghiệp vụ trên DB thật.

S3 P6-03 còn chờ bucket; duyệt shop/P7-02, kiểm duyệt sản phẩm/P7-03 và danh mục/P7-04 chưa triển khai. Chưa kiểm tra tải cao, HTTPS hoặc điện thoại vật lý. Không tự bootstrap Admin trên DB thật; chưa commit/push/AWS/Terraform.
