# Mua ngay riêng sản phẩm

URL /thanh-toan?product=ID&quantity=N được validate trên page; chỉ đọc productdetail để dựng review, không POST/PATCH/DELETE cart. Đăng nhập và quay lại từ địa chỉ giữ query. Gửi purchase_mode=BUY_NOW và đúng một CheckoutItem. Chế độ CART mặc định giữ đối chiếu toàn bộ giỏ và clearcart cũ.

Backend BUY_NOW không khóa/đọc/xóa cart; dùng cùng validation ownership/address/category/publicshop/price/stock, khóa catalog/inventory, transaction/idempotency và order snapshot của checkout. Replay cùngUUIDtrảđơn cũ,khôngtrừtồn2lần. Mã giảm giá legacy nhận direct_item trong quote, tính trên sản phẩm được chọn, serverkiểmlạikhiđặt. Không mua được sản phẩm ẩn/shopkhóa/shopmình/Admin; cart không thay đổi cả khi đặt đơn thành công.

Runtime hiện dùng COD và một coupon trên schema25 legacy. Checkout-options/stackedcoupon/shipping chưa kích hoạt; luồng quotechoices chuẩn bị vẫn phụ thuộc cart, cần mở rộng direct_item trước khi bật tính năng đó cho Mua ngay. Không áp migration/bảngmới trong tasknày.
