# Mã giảm giá, đánh giá và mua tiếp

Ngày 15/11/2026. Yêu cầu trực tiếp của người dùng mở rộng phạm vi coupon/review trước đây. Dùng schema25 hiện hữu; không migration, seed dữ liệu thật hoặc sửa SQL nguồn.

## Mua tiếp khi đơn trước đang chờ

Tài khoản USER sở hữu gian hàng vẫn có đầy đủ quyền mua từ shop khác và xem đơn mua của chính mình; trạng thái shop PENDING/APPROVED/LOCKED không khóa quyền Buyer nếu tài khoản còn ACTIVE. Trong Kênh người bán, chọn **Đơn mua** ở thanh đầu trang để mở `/tai-khoan/don-hang`. **Đơn bán** ở `/kenh-nguoi-ban/don-hang` là các đơn khách mua tại shop. Hai danh sách giữ ownership riêng, không dùng role Seller để đọc đơn cá nhân của khách.

Cập nhật CHECKOUT-AUTO-RESOLVE: khi mở trang có intent cũ, UI tự GET `/api/v1/orders/checkout-status` với header Idempotency-Key. Chỉ đọc đơn của buyer hiện tại; trả `{data:order|null}`, no-store, USER ACTIVE. Đã có đơn thì xóa intent và mở form giỏ hiện tại, kèm link đơn trước. Chưa có đơn thì giữ UUID cũ và mở form cho người mua kiểm tra rồi chủ động đặt; GET không tạo đơn hoặc tự replay POST. Khi lỗi tra cứu, chưa thể mở đặt đơn mới; hiển thị lỗi/thử lại ngắn gọn, không yêu cầu người mua “gửi lại yêu cầu”. Không hứa GET loại trừ một POST đang trên đường mạng; giữ UUID ở kết quả null để chống trùng trong trường hợp này.

Đơn shop PENDING không khóa tài khoản hoặc giỏ hàng mới. Sau khi API xác nhận tạo đơn (201 hoặc replay200 và response hợp lệ), UI xóa checkout intent đã hoàn tất. Người mua có thể thêm sản phẩm khác và tạo UUID mới ngay. Nếu mất phản hồi hoặc chưa xác minh được kết quả, giữ intent cũ để retry cùng UUID, tránh trùng đơn. Xác nhận tạo đơn khác với shop xác nhận xử lý đơn.

## Coupon

- Một mã mỗi đơn; nhập và bấm Áp dụng ở `/thanh-toan` để xem số tiền giảm.
- Toàn sàn: tính trên tổng hàng hóa đủ điều kiện; coupon shop: chỉ phần hàng của shop đó. Minimum áp trên chính phần hàng đủ điều kiện, không tính shipping. Hiện shipping checkout là0.
- Mã khớp chính xác code trong DB sau trim, phân biệt hoa/thường. Mã cần có sẵn trong bảng coupons; task này không bổ sung giao diện phát hành/quản lý mã hoặc tạo mã trong dữ liệu thật.
- Kiểm active, starts_at≤giờ DB<expires_at, used_count<usage_limit. Theo xác nhận người dùng: mỗi khách tối đa1lượt cho mỗi coupon. Không thêm trường hạn mức khách vào schema.
- Decimal, round HALF_UP đến0.01, tối đa100% giá trị hàng áp dụng. UI gửi expected_coupon_discount; server từ chối409 COUPON_CHANGED nếu mức giảm khác preview. Giá/tồn/cart vẫn kiểm lại.
- used_count và coupon_usages chỉ ghi cùng transaction tạo đơn, trừ tồn, xóa giỏ; rollback hoàn tất cả. Replay buyer/UUID trả snapshot cũ, không ghi lượt thêm. Quote không giữ lượt.
- Hủy hợp lệ toàn bộ shop orders mới hoàn1lượt tổng và lượt của khách. Hủy một phần giữ lượt. Lưu lịch sử coupon_usages, không xóa; lượt khách tính qua usage có ít nhất một shop order chưa CANCELLED. No-op hủy không hoàn lần nữa. Đơn gốc giữ snapshot total/discount; không thực hiện refund tiền thật.
- Khóa checkout: user→cart→category→shop→product→inventory, rồi coupon. Hủy: user→shop→product→inventory→shop_order, rồi coupon. Lock coupon serialize kiểm toàn bộ đơn sau transition, không khóa coupon trước stock.
- Shop subtotal là tiền hàng trước giảm; Order.discount_amount là giảm toàn đơn; Order.total_amount=tổngsubtotal-discount+shipping. List/detail/checkout UI hiểu công thức mới. Không tự chia khoản giảm cho settlement Seller.

| Đường dẫn | Contract |
| --- | --- |
| POST /api/v1/coupons/quote | USER ACTIVE, CSRF/Origin; body `{code}`; trả code/subtotal/discount_amount/total_amount từ giỏ server |
| POST /api/v1/orders/checkout | Thêm coupon_code? và expected_coupon_discount? (decimal string); giữ Idempotency-Key |
| GET /api/v1/orders, /orders/{id} | Thêm discount_amount, shipping_fee dạng decimal string |

Lỗi409: COUPON_INVALID, COUPON_MINIMUM, COUPON_CUSTOMER_LIMIT, COUPON_CHANGED. Admin không được quote/checkout.

## Đánh giá

Người mua USER ACTIVE mở `/tai-khoan/don-hang/{id}`. Chỉ dòng thuộc shop order COMPLETED có form1–5 sao, bình luận plain text tùy chọn≤2000ký tự. Mỗi order_item được1đánh giá; lần mua khác có thể đánh giá riêng. Không cho khai user/product/order; không sửa/xóa đánh giá trong task này. Server kiểm ownership/completed trước insert, unique order_item và lock user/shop_order bảo vệ gửi đồng thời. Mất response thì UI đọc lại trước khi cho gửi tiếp.

| Đường dẫn | Contract |
| --- | --- |
| GET /api/v1/order-items/{id}/review | USER ACTIVE/owner/completed, `{data:review|null}` |
| POST /api/v1/order-items/{id}/review | USER ACTIVE/owner/completed + CSRF, `{rating,comment?}` →201 `{data:review}`; đã có409 REVIEW_EXISTS |
| GET /api/v1/products/{id}/reviews | Public, product còn public; page≥1/page_size1..50; items/total/average_rating/page/page_size |

Public chỉ tính review liên kết đúng buyer/product/order_item và đơn COMPLETED. Trả review_id/rating/comment/created_at, không email/phone/userID/orderID. Hiển thị chung “Người mua đã xác minh”. Trang sản phẩm có empty/loading/error/pagination và trung bình từ DB. Sản phẩm/shop bị ẩn/khóa trả404 như catalog. React hiển thị bình luận như text, không render HTML; không ảnh review.

Proxy Next cố định endpoint/ID/method/query, giữ cookie/Origin/CSRF cho API riêng; public review GET không forward cookie/Authorization. Giữ body limit8KiB, checkout128KiB. Extra fields bị từ chối; không triển khai AWS hoặc thay quyền bucket.
