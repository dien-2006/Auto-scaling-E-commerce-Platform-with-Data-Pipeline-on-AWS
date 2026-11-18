# Chọn sản phẩm và lưu mã

Giỏ chọn mặc định các dòng có thể mua, chọn từng dòng/chọn tất cả, tổng tiền Decimal bằng cent BigInt. Checkout?selected=ID,ID lọc review từ giỏ server; missingID dừng. purchase_mode=SELECTED_CART bắt buộc qty các dòng chọn khớp cart đã khóa, kiểm ownership/giá/tồn/trạng thái/địa chỉ như cũ, chỉ xóa cart rows đã mua trong transaction. Các dòng còn lại không đổi; replay không xóa/trừ lần2. CART toàn giỏ và BUY_NOW vẫn độc lập.

Couponquote selected_product_ids chỉ tính các dòng chọn; không đổi kho/giỏ. Runtime COD/legacycoupon hiện tại đã kiểm; stacked quotechoices chuẩn bị chưaactive vẫn cần mở rộng phạm vi selected trước enable.

Lưu mã: localStorage coco.coupons.v1:{userID}, tối đa100, deduplicate/expiryvalidation, không đồng bộthiếtbị hay dành trước lượt coupon. Guest cầnlogin; cóstatus/error khi lưu. Checkout chọn mãđãlưu rồi Ápdụng, server tiếp tục kiểm điều kiện/lượt/giỏ, không tinbrowser. Chỉ liệtkê mã trongFlashSaleđãtải, không hứa toàn bộcoupon. Khôngthêm bảng/schema.
