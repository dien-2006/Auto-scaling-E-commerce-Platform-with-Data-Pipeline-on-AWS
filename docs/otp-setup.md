# Xác nhận email và quên mật khẩu bằng Brevo

**Cấu hình hiện tại:** chỉ dùng `.env` ở thư mục gốc; xem [hướng dẫn gộp env và Docker release](docker-release.md). Các tên env theo service trong phần lịch sử không còn được Compose đọc.

Cập nhật 18/11/2026 theo yêu cầu mới: **chỉ OTP qua email, không đăng ký bằng số điện thoại, không thêm bảng và không đổi schema PostgreSQL**. Giữ nguyên 25 bảng hiện tại. Mã OTP gồm 6 số, hết hạn sau **1 phút** kể từ lúc máy chủ cấp mã.

## 1. Chuẩn bị tài khoản Brevo

1. Tạo tài khoản Brevo và dùng gói Free để thử. Gói này hiện có **300 email/ngày**, dùng chung cho các email bạn gửi qua tài khoản; ngày gửi không hết không cộng dồn. [Giới hạn Free chính thức](https://help.brevo.com/hc/en-us/articles/208580669-FAQs-What-are-the-limits-of-the-Free-plan).
2. Trong Brevo, thêm và xác minh địa chỉ người gửi tại phần **Senders, Domains & Dedicated IPs**. Nếu dùng domain riêng, hoàn tất xác thực domain theo hướng dẫn Brevo. [Xác minh người gửi](https://help.brevo.com/hc/en-us/articles/208836149-Create-a-new-sender-From-name-and-From-email).
3. Mở **SMTP & API → SMTP**. Lấy **SMTP login** được Brevo hiển thị và tạo **SMTP key**. Không dùng API key hoặc mật khẩu đăng nhập Brevo làm mật khẩu SMTP. SMTP login có thể khác email người gửi. [Hướng dẫn SMTP](https://help.brevo.com/hc/en-us/articles/7924908994450-Send-transactional-emails-using-Brevo-SMTP), [Tạo SMTP key](https://help.brevo.com/hc/en-us/articles/7959631848850-Create-and-manage-your-SMTP-keys).
4. Nếu Brevo báo chưa kích hoạt transactional sending, hoàn tất yêu cầu của tài khoản trước khi thử OTP.

Không gửi SMTP key, password, OTP secret hoặc nội dung file cấu hình vào chat/Git.

## 2. Điền `.env`

File private đã có OTP secret riêng; giữ nguyên secret đó. Các trường cần điền:

```dotenv
MARKETPLACE_OTP_ENABLED=false
MARKETPLACE_OTP_REDIS_URL=redis://otp-redis:6379/0
MARKETPLACE_OTP_EMAIL_PROVIDER=smtp
MARKETPLACE_OTP_FROM_EMAIL=EMAIL_NGUOI_GUI_DA_XAC_MINH
MARKETPLACE_SMTP_HOST=smtp-relay.brevo.com
MARKETPLACE_SMTP_PORT=587
MARKETPLACE_SMTP_SECURITY=STARTTLS
MARKETPLACE_SMTP_USERNAME=SMTP_LOGIN_TU_BREVO
MARKETPLACE_SMTP_PASSWORD=SMTP_KEY_TU_BREVO
```

Thay các giá trị viết hoa bằng thông tin của bạn. `MARKETPLACE_OTP_FROM_EMAIL` phải là email hợp lệ đã xác minh trong Brevo. Nếu SMTP key có ký tự được dotenv hiểu đặc biệt, đặt giá trị trong dấu nháy đơn. Không đặt cấu hình này trong frontend hoặc `NEXT_PUBLIC_*`.

Cổng 587 dùng **STARTTLS bắt buộc** trong code. Không tắt TLS để xử lý lỗi kết nối. Brevo cũng hỗ trợ 465 với TLS trực tiếp nếu môi trường chặn cổng 587; khi đổi, đổi cả port và `MARKETPLACE_SMTP_SECURITY=TLS`.

## 3. Redis lưu OTP, không thêm bảng

OTP, số lần nhập sai, thời gian chờ gửi lại và giới hạn gửi nằm trong Redis dùng chung giữa các backend. Không lưu trong memory từng process, không thêm cột/bảng PostgreSQL, không dùng email giả.

Đã chuẩn bị `docker-compose.otp.yaml` cho chạy local:

- Service `otp-redis`, không mở cổng ra host, dùng network hiện có.
- Mã sống 60 giây; bộ đếm giới hạn sống tối đa 1 giờ.
- Không lưu snapshot/AOF/volume. Redis restart làm các mã đang chờ mất hiệu lực; người dùng yêu cầu mã mới.
- Khi Redis không sẵn sàng, chức năng OTP từ chối xử lý và readiness báo lỗi nếu OTP đang bật.
- URL `redis://otp-redis:6379/0` chỉ dùng từ backend Docker trong cùng network. Backend chạy trực tiếp trên Windows cần Redis riêng và URL local đúng; không tự mở Redis công khai.
- Trên AWS dùng Redis riêng trong mạng private, ACL và TLS (`rediss://...`), giới hạn security group tới backend. Hướng dẫn này chưa triển khai AWS.

Không chạy SQL cho tính năng này. File đề xuất cũ `backend/migrations/proposals/20261118_auth_otp.sql` đã rút lại và chỉ còn chú thích. **Không áp bản cũ tạo `auth_security` hoặc cho email NULL.** Email hiện vẫn bắt buộc như schema gốc.

## 4. Kích hoạt sau khi điền đủ cấu hình

Giữ cấu hình Brevo riêng của bạn. Khi cập nhật phiên bản tiếp theo, từ thư mục repository:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.otp.yaml up -d --no-deps --wait otp-redis
docker compose -f docker-compose.yaml -f docker-compose.otp.yaml build backend frontend
```

Khi Redis đã healthy và các thông tin Brevo hợp lệ, đổi `MARKETPLACE_OTP_ENABLED=true` trong `.env`, rồi:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.otp.yaml up -d --no-deps --wait backend frontend
```

Chỉ cập nhật các service được chỉ rõ; giữ PostgreSQL/container/volume/network/root `.env`. Không chạy `down -v`, migration, seed hoặc tạo lại database. Backend đọc `.env` gốc; frontend/PostgreSQL chỉ nhận các biến được chỉ rõ trong Compose.

Sau lần bật OTP, các phiên đăng nhập cũ chưa có credential stamp cần đăng nhập lại. Không tắt OTP để vượt lỗi gửi mail: việc đó mở lại đăng ký cũ không yêu cầu OTP. Nếu cần rollback, phải đánh giá phiên/token cũ trước.

## 5. Luồng trên web

**Đăng ký:** nhập email → bấm **Gửi mã** cạnh ô xác minh → nhập mã 6 số, họ tên, mật khẩu và xác nhận → **Đăng ký** → Đăng nhập. Gửi mã không yêu cầu nhập mật khẩu trước và không lưu mật khẩu chờ trong Redis. Máy chủ xác minh OTP trước, rồi mới cho tạo tài khoản USER bằng bằng chứng email đã xác minh.

**Quên mật khẩu:** ở trang đăng nhập bấm Quên mật khẩu → nhập email → **Gửi mã OTP** → nhập OTP → **Xác minh mã OTP** → chỉ sau khi mã đúng mới hiện ô mật khẩu mới/xác nhận → **Đổi mật khẩu** → Đăng nhập. API xác minh không nhận mật khẩu; API đổi mật khẩu yêu cầu bằng chứng xác minh do máy chủ cấp. Bằng chứng này có hạn 5 phút, chỉ dùng một lần và chỉ dành cho đúng thao tác. Mã OTP vẫn hết hạn sau 1 phút. Reset không mở khóa tài khoản; các phiên mang credential cũ hết quyền.

Các tài khoản có sẵn vẫn đăng nhập bình thường; chức năng này không tự gắn nhãn đã xác minh hồi tố cho dữ liệu cũ. Reset yêu cầu chứng minh quyền truy cập email hiện gắn với tài khoản.

## 6. Kiểm tra và lỗi thường gặp

- Thử với email của chính bạn: đăng ký → nhận OTP → sai mã → đúng mã; quên mật khẩu → đổi mật khẩu → đăng nhập lại. Kiểm tra cả thư rác và Brevo transactional logs.
- Mã hết hạn sau **60 giây từ lúc cấp**, kể cả thư đến chậm. Brevo nhận SMTP không đồng nghĩa thư đã vào inbox. Khi chạm hạn mức, Brevo có thể xếp hàng thư; thư tới trễ vẫn không dùng được sau hạn. Không tự kéo dài hạn theo thời gian nhận thư.
- `OTP_NOT_CONFIGURED`: OTP/SMTP/Redis chưa được cấu hình đầy đủ. `OTP_UNAVAILABLE`: Redis/DB tạm lỗi; chưa có kết quả chắc chắn. `OTP_INVALID`: mã sai, hết hạn, chưa gửi thành công hoặc đã dùng. Mã không được trả về API hay ghi log.
- Gửi lại thủ công sau 60 giây. Tối đa 5 yêu cầu/email/mục đích/giờ và 100 yêu cầu/peer IP/giờ; mỗi mã tối đa 5 lần nhập sai. Giới hạn IP sau proxy có thể tính chung frontend; không tin tùy ý X-Forwarded-For. Đây không phải giới hạn chi phí/ngày toàn hệ thống; cần theo dõi hạn mức Brevo.
- Redis xử lý kiểm tra/tiêu thụ mã nguyên tử. Mã đúng được tiêu thụ để cấp bằng chứng xác minh ngẫu nhiên 256 bit; Redis chỉ giữ HMAC của token làm key, hạn 5 phút. Token nằm trong bộ nhớ form, không ở URL/localStorage/sessionStorage/log. API hoàn tất tiêu thụ token trước transaction tạo user/đổi mật khẩu; không thể dùng lại hay đổi mục đích. Redis và PostgreSQL không phải một transaction: nếu DB lỗi sau khi token bị xóa, hãy kiểm tra đăng nhập trước rồi xác minh lại nếu cần. Trạng thái khóa, email và credential stamp được kiểm lại khi đổi mật khẩu.
- Gửi thư bằng background task hiện là best effort; process chết có thể chưa gửi được. Không có hàng đợi mail bền vững/bounce webhook. Redis lỗi không chuyển sang mã giả hoặc bỏ xác minh.
- Bản sửa giao diện và luồng xác minh đã được cập nhật lên ứng dụng local. Cấu hình hiện tại bật OTP và đủ các trường gửi email; giữ nguyên SMTP key của bạn. Đợt kiểm thử này dùng PostgreSQL/Redis riêng và SMTP test double, không gửi email thật hoặc đổi mật khẩu tài khoản thật. Sau cập nhật, tải lại trang để nhận form mới; mã đang chờ từ phiên bản cũ có thể cần yêu cầu lại.
