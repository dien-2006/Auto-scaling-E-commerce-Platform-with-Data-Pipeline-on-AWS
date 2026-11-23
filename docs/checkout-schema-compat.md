# Checkout tương thích schema 25 bảng hiện tại

**Cấu hình hiện tại:** chỉ dùng `.env` ở thư mục gốc; xem [hướng dẫn gộp env và Docker release](docker-release.md). Các tên env theo service trong phần lịch sử không còn được Compose đọc.

Backend/.env.commerce bật MARKETPLACE_LEGACY_SCHEMA=true; đây là cấu hình mapping lúc khởi động, không chạy DDL. Bỏ ánh xạ orders.shipping_discount_amount và coupons.coupon_type trong chế độ này, phí giảm vận chuyển trả0/coupon loạiGOODS. Checkout chỉ ghi trường tồn tại; history/replay không đọc cột tương lai. Giữ MARKETPLACE_CHECKOUT_OPTIONS_ENABLED=false. Chỉ tắt legacy mode sau khi được phép áp migration checkout-options và đã kiểm schema. Không bật shipping coupon/stacked options trên schema cũ.

Đổi chế độ cần recreate app, không restart PostgreSQL. Local backend ngoài Docker phải nhận cùng envflag. Test legacy: PowerShell đặt MARKETPLACE_LEGACY_SCHEMA=true và PYTEST_ADDOPTS lọc các checkout/cart tests, chạy tests/schema25/run.py; runner bỏ proposalDDL chỉ trong DBtest riêng và chuyển flag sang pytest. Test mặc định vẫn kiểm schema đích đầy đủ.

Giỏ không giữ hàng, không trừ tồn khi thêm/sửa. Khi checkout thành công transaction khóa/trừ tồn; lỗi rollback, cùngUUIDkhôngtrừlần2, hủy hợp lệ hoàn1lần. UUIDv4 lấy128bit từcrypto.getRandomValues, đặtversion/variant đúng; khôngMath.random, dùng đượcHTTP LAN.
