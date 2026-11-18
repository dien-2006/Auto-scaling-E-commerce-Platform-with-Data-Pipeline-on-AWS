# Cấp quyền quản trị local cho tài khoản đã đăng ký

Theo yêu cầu trực tiếp của chủ dự án, có CLI operator-only `python -m app.grant_admin`. Đây là thao tác riêng với quyền chạy lệnh backend; không có nút tự chọn Admin khi đăng ký/đăng nhập và không có API cấp quyền công khai. Tài khoản ADMIN vẫn đăng nhập bằng trang chung `/dang-nhap`.

## Thực hiện

Tài khoản cần tồn tại và ACTIVE. Người dùng chỉ cần chỉ định email, không gửi mật khẩu. Từ thư mục repository, dùng backend container đang chạy để đọc cấu hình DB hiện hữu:

```powershell
docker compose exec -T backend python -m app.grant_admin --email 'email-ban-da-dang-ky@example.com'
```

Mặc định chỉ xem trước trong transaction READ ONLY. Kết quả JSON gồm user_id, email, full_name, user_status, user_role, changed=false, dry_run=true. Kiểm đúng email/tài khoản và dùng user_id từ kết quả (thay123 dưới đây):

```powershell
docker compose exec -T backend python -m app.grant_admin --email 'email-ban-da-dang-ky@example.com' --apply --expected-user-id 123
```

Chỉ chạy `--apply` khi chủ dự án đã chỉ định rõ tài khoản được cấp quyền. Email chưa được chỉ định thì không đoán tài khoản, không cấp quyền cho tài khoản đầu tiên. Không tạo account mới hoặc chọn tất cả user.

Sau thành công, tải lại trang hoặc đăng nhập bằng tài khoản đó, vào **Tài khoản → Quản lý người dùng** hoặc `http://localhost:3001/admin/users`. Role được đọc lại từ DB; không cần đổi mật khẩu hay JWT secret. Tài khoản thường khác giữ nguyên quyền.

## Bảo toàn dữ liệu

Chỉ UPDATE user_role USER→ADMIN và updated_at của đúng một user đã kiểm ID/email dưới row lock, giữ đến COMMIT. Không chạm password_hash, email, user_status, shop, đơn, địa chỉ, schema hay sequence. Tài khoản đã ADMIN là no-op; chạy lặp/song song không tạo tài khoản hoặc cập nhật lại timestamp vô ích. Lỗi COMMIT rollback, không báo thành công trước COMMIT.

CLI chỉ cho environment local/test, từ chối production. Không tự mở khóa user LOCKED. Không có tính năng demote, cấp quyền hàng loạt hay sửa trạng thái ADMIN; tài khoản Admin trong UI quản lý người dùng vẫn chỉ xem theo phạm vi P7-01 đã thống nhất.

Lỗi được làm sạch, không in password/token/DSN/config: NOT_FOUND (chưa có tài khoản), USER_LOCKED, EXPECTED_USER_REQUIRED, IDENTITY_CHANGED, STATE_CHANGED, LOCAL_ONLY, DATABASE_NOT_CONFIGURED, INVALID_INPUT_OR_CONFIGURATION hoặc DATABASE_UNAVAILABLE. Không copy secrets vào command/chat, không sửa root.env hoặc restart PostgreSQL để chạy.

## Kiểm chứng

PASS383 backend full trên PostgreSQL16 tmpfs marketplace_test riêng + metadata audit hiện hữu READ ONLY. Thêm kiểm thử CLI riêng sau lượt full cho subprocess thật và che lỗi kết nối; kết quả cuối ghi tại [progress.md](progress.md). Có preview READ ONLY/no password query, grant đúng user/token hiện hữu đổi quyền, preserve hash/status/user khác, missing/locked/mismatched ID/thiếu expected ID, concurrent no-op và rollback COMMIT. Backend Ruff/build/help command được kiểm chứng; frontend không đổi.

CLI sẵn sàng không có nghĩa một tài khoản nghiệp vụ đã được cấp quyền. Xem progress để biết target cụ thể đã được chỉ định và thực thi hay chưa. Không tạo fixture/test account trên DB thật.
