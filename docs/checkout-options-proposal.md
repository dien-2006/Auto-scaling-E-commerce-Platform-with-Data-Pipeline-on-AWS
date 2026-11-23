# Checkout mở rộng — sẵn sàng kiểm thử, chờ áp dụng schema

**Cấu hình hiện tại:** chỉ dùng `.env` ở thư mục gốc; xem [hướng dẫn gộp env và Docker release](docker-release.md). Các tên env theo service trong phần lịch sử không còn được Compose đọc.

Ngày 15/11/2026. Quy tắc theo lựa chọn mới nhất của chủ dự án.

## Hành vi đã chuẩn bị

- Mỗi shop tối đa một mã GOODS, chỉ giảm phần hàng của shop đó.
- Thêm tối đa một mã COCO GOODS giảm tiền hàng còn lại sau mã shop.
- Thêm tối đa một mã COCO SHIPPING giảm tổng cước vận chuyển, không giảm tiền hàng. Minimum của mã vận chuyển tính trên tiền hàng sau các giảm giá hàng hóa; minimum COCO GOODS tính sau mã shop. Tất cả vẫn kiểm active/thời gian/tổng lượt và một lượt mỗi khách.
- Mã vận chuyển tính theo phần trăm cước, tối đa 100%; không tự chuyển coupon GOODS thành SHIPPING dựa vào tên mã. Các mã cũ mặc định GOODS. Chưa có giao diện phát hành mã trong task này.
- Cước COCO tự đặt theo yêu cầu: STANDARD 25.000đ/shop, EXPRESS 40.000đ/shop, COCOEXPRESS 60.000đ/shop. Không phụ thuộc cân nặng/tỉnh/khoảng cách, không tuyên bố là báo giá hay booking hãng giao hàng. COCOEXPRESS được lưu bằng shipping_method=INSTANT/carrier=COCO Express trong schema hiện có.
- Cước trước giảm bằng số shop nhân mức cước. Giảm cước phân bổ đến từng shop bằng số nguyên cent, phần dư phân theo shop_id tăng dần, không có cước âm hoặc sai tổng do rounding.
- Order.discount_amount chỉ là giảm tiền hàng; shipping_discount_amount là giảm cước; shipping_fee là cước còn trả. total_amount = tổng tiền hàng - discount_amount + shipping_fee. Cước gốc = shipping_fee + shipping_discount_amount.
- Coupon usages/counters, Order, ShopOrder, OrderItem, Inventory, Shipment và Payment cùng transaction. Lock tất cả coupon theo coupon_id tăng dần sau inventory. Retry/replay không ghi lượt hoặc trừ tồn thêm. Hủy toàn bộ đơn hoàn lượt tất cả các mã đúng một lần, hủy một phần giữ lượt theo quy tắc người dùng đã chốt trước đó; giữ lịch sử usages.
- COD có thể dùng. Chuyển khoản chỉ bật khi đủ ngân hàng/số tài khoản/chủ tài khoản. Đơn chuyển khoản có Payment PENDING, nội dung COCO{order_id}, không tự xác nhận đã nhận tiền. Thông tin nhận tiền hiển thị là cấu hình hiện tại, không phải snapshot ngân hàng lịch sử.
- Seller không xác nhận/giao/hoàn tất đơn trả trước khi chưa có Payment SUCCESS đúng amount/method. Hủy toàn bộ đơn dừng các Payment PENDING thành FAILED. Chưa có giao diện đối soát/xác nhận tiền ngân hàng, refund hoặc tự động thu tiền COD; đây là phần cần tích hợp trước khi vận hành thanh toán thực tế.
- MoMo/VNPay hiển thị disabled, giải thích chưa tích hợp; backend từ chối sử dụng với PAYMENT_NOT_CONFIGURED. Chưa có merchant/API/callback, không có nút giả báo trả tiền thành công.

## Thay đổi schema cần được cho phép

File cụ thể: `backend/migrations/proposals/20261115_checkout_options.sql`.

1. Thêm coupons.coupon_type, mặc định GOODS cho dữ liệu cũ; CHECK GOODS/SHIPPING và shop chỉ được GOODS.
2. Thay UNIQUE(order_id) của coupon_usages bằng UNIQUE(coupon_id,order_id), thêm index order_id thay chỉ mục unique cũ để giữ hiệu quả tra cứu.
3. Thêm orders.shipping_discount_amount NUMERIC(14,2) mặc định0, CHECK không âm.
4. Mở CHECK payment_method ở orders/payments để nhận BANK_TRANSFER cùng COD/VNPAY/MOMO.

Vẫn25bảng,184cột,28explicitindexes. Không xóa row/bảng, đổi cột cũ hoặc reset identity/sequence. Không chạy lại SQL Downloads. File SQL dùng transaction, lock_timeout5s/statement_timeout30s; lỗi thì rollback. Chưa được chạy vào DB nghiệp vụ. Đã áp vào DB test riêng để kiểm chứng metadata và nghiệp vụ. Live vẫn182cột và cấu trúc cũ; identity drift BY DEFAULT/ALWAYS đã ghi từ trước vẫn không tự sửa.

Trước khi áp thật cần xác nhận của chủ dự án theo AGENT.md, kiểm tra đúng DB/constraint hiện hữu và chuẩn bị bản sao lưu theo quy trình của chủ DB. Không rollback về UNIQUE(order_id) một cách mù quáng sau khi đã có nhiều usages/đơn; cần đánh giá dữ liệu hoặc forward fix. Không có migration startup tự động.

## Cấu hình

Template `.env.example`, file local riêng `.env`, Compose chỉ nạp cho backend. Không ghi đè root .env hoặc đưa credentials vào image/client.

- MARKETPLACE_CHECKOUT_OPTIONS_ENABLED=false mặc định. Chỉ đổi true SAU khi schema được cập nhật và kiểm tra.
- MARKETPLACE_SHIPPING_STANDARD_FEE=25000
- MARKETPLACE_SHIPPING_EXPRESS_FEE=40000
- MARKETPLACE_SHIPPING_COCOEXPRESS_FEE=60000
- MARKETPLACE_BANK_NAME, MARKETPLACE_BANK_ACCOUNT_NUMBER, MARKETPLACE_BANK_ACCOUNT_HOLDER: để comment khi chưa có thông tin, điền riêng trên máy khi có.

Khi bật lựa chọn mới, checkout bắt buộc shipping_method và expected_coupon_discount/expected_shipping_discount/expected_shipping_fee lấy từ quote. Client cũ không được bỏ shipping_method để né phí. Replay đơn đã ghi vẫn trả snapshot cũ trước khi kiểm cấu hình mới.

Không có biến môi trường có thể tự bật MoMo/VNPay chưa tích hợp. Thông tin merchant/secret và callback cần task tích hợp thật, không gửi secret qua chat.

## API và UI

- GET /api/v1/checkout/options: USER ACTIVE, no-store; trả enabled, ba loại ship/cước mỗi shop, bốn cách thanh toán/trạng thái sẵn sàng và thông tin ngân hàng nếu đã cấu hình.
- POST /api/v1/checkout/quote: USER ACTIVE + CSRF/Origin. Nhận shipping_method, payment_method, shop_coupons[{shop_id,code}], coco_coupon_code?, shipping_coupon_code?. Tính giỏ server; trả từng mã, tổng giảm tiền hàng, giảm cước, cước từng shop và tổng thanh toán. Quote không giữ lượt.
- POST /api/v1/orders/checkout: thêm các trường trên và ba giá trị expected; unknown fields bị từ chối. Một mã không hợp lệ làm toàn bộ giao dịch thất bại.
- UI có ô riêng cho từng loại mã, radio vận chuyển/thanh toán. Đổi lựa chọn hoặc mã sẽ hủy quote; người mua bấm Áp dụng và tính tổng tiền trước khi đặt. Bank pending có hướng dẫn và đọc lại từ chi tiết đơn.

## Kiểm chứng

Có test PostgreSQL cho bốn mã trên đơn hai shop, phạm vi/type, số tiền và phân bổ cước, tamper quote, replay/rollback/hoàn lượt, lượt COCO cuối giữa hai khách mua ở các shop khác nhau, bank chưa trả tiền không được fulfill. Browser suite options dùng DB/seed test riêng; không thử thanh toán hay tạo đơn ở DB thật. Suite journey cũ vẫn kiểm khả năng phục hồi và mua tiếp.

Không nạp image mới vào container đang phục vụ cho tới khi schema được cho phép và áp thành công. Web đang chạy vẫn giữ bản trước.
