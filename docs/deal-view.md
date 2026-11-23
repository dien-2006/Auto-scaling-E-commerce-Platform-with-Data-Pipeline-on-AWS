# Deal từ coupon, giữ nguyên 25 bảng

SQL review: backend/migrations/proposals/20261117_deal_view.sql. Chỉ CREATE OR REPLACE VIEW; không thêm bảng/cột vào bảng nghiệp vụ. Giữ thứ tự/kiểu 10 cột view cũ, nối coupon_code và ends_at ở cuối. Cần chủ DB cho phép trước khi thực thi.

Đây là giá dự kiến sau coupon, không phải thay đổi products.price. Khách phải nhập mã ở checkout, server kiểm lượt mỗi khách/tổng lượt/giỏ hợp lệ. Không cộng giá giảm này lần nữa trước khi áp coupon. View dùng giá một sản phẩm để kiểm minimum; giỏ nhiều sản phẩm có thể có lựa chọn mã khác. Đồng hồ theo expires_at của mã được chọn cho từng sản phẩm, không tạo giờ kết thúc giả chung. Sản phẩm hết giờ bị gỡ khỏi hàng; không tự chọn coupon mới đến khi tải lại. Top100 sản phẩm, cuộn ngang/nút xem tiếp trong hàng, ảnh ký S3 qua storage hiện có. Chưa tự áp mã qua link sản phẩm.

SQL đã áp dụng ngày17/11/2026 sau khi người dùng cho phép; đã sao lưu định nghĩa cũ bên ngoài repo. API tương thích view cũ: coupon_code/ends_at null thì chỉ giá gốc, không clock/không cam kết giá coupon. Muốn bật đầy đủ phải thay view bằng SQL đã review. Coupon_type không có trong schema hiện tại; nếu sau này áp migration shipping coupon thì view phải loại SHIPPING.
