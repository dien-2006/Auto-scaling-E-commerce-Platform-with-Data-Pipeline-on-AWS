# P7-03 — Kiểm duyệt sản phẩm

Đăng nhập ADMIN ACTIVE, mở `/admin/products` hoặc chọn **Sản phẩm** trong điều hướng quản trị. Tìm tên/SKU, lọc mã shop và trạng thái đang bật/đã ẩn, phân trang24. Hồ sơ có mô tả, giá VND, tồn kho, shop, category ID, thời gian cập nhật và liên kết xem ảnh khi có URL S3 hợp lệ. Không bịa ảnh khi storage chưa cấu hình.

**Đang bật** phản ánh product.is_active; sản phẩm chỉ công khai khi shop và toàn bộ danh mục đủ điều kiện. Admin có thể ẩn sản phẩm ở mọi shop_status. Ẩn không xóa sản phẩm/ảnh, không hủy đơn, đổi giá snapshot hay hoàn tồn.

## API và quyền

- `GET /api/v1/admin/products?q=&shop_id=&is_active=true&page=1&page_size=24`: items/page/page_size/total. q≤200 tìm tên hoặc SKU không phân biệt hoa/thường, literal wildcard; shop_id BIGINT dương, is_active tùy chọn boolean; page1..2147483647/page_size1..100. Sắp xếp created_at DESC,product_id DESC; ảnh query theo batch, không N+1.
- `POST /api/v1/admin/products/{id}/hide`: không body; response envelope data AdminProduct tương đương SellerProduct/ProductDetail + is_active/timestamps. Đã ẩn trả no-op200, không cập nhật timestamp lại. ID thiếu404, validation422, thiếu quyền403, guest401. Không API kích hoạt lại.
- Role/status đọc từ DB, không role client/JWT cũ; USER/Seller không gọi Admin hide ngay cả sản phẩm shop mình. Admin không được dùng Seller API để sửa sản phẩm shop người khác.
- Giá Decimal string/ID BIGINT string/UTC, ảnh là URL đã kiểm hoặc null. Không password, owner email/phone, contact email hay raw image_key. Admin và Seller dùng chung projection cho dữ liệu quản lý, không thay ownership Seller.

Read READ ONLY/no-store. Mutation WriteAccess cookie/CSRF/Origin, khóa user → shared category → shop → product đến COMMIT, tương thích checkout/Seller cập nhật. Chỉ đặt is_active=false và updated_at, không đổi shop/stock/order. Nếu hide commit trước thì checkout từ chối; checkout commit trước giữ đơn đã mua. Lỗi DB/COMMIT503 sanitized và rollback.

## Không bật lại sản phẩm đã ẩn

Schema hiện không phân biệt Admin hay Seller đã ẩn sản phẩm. Theo contract hiện tại, giữ không có reactivation cho cả hai vai trò; Seller PATCH chỉ nhận trường hồ sơ, không is_active. Seller sửa giá/mô tả hoặc chỉnh tồn/ảnh không tự bật lại; không thêm field/moderation table hoặc endpoint mở lại khi chưa được đặc tả. Đơn cũ tiếp tục dùng snapshot đã lưu.

Catalog search/detail không hiện sản phẩm bị ẩn. Giỏ hàng giữ dòng cũ để Buyer có thể xóa, đánh dấu HIDDEN_PRODUCT/is_available=false; thêm mới/checkout không mua được. Không tự giảm/hoàn tồn khi ẩn.

## Giao diện và phục hồi

Có xác nhận tên/SKU/product ID/shop trước ẩn, submit guard, loading/empty/error/retry, filter/page. Client kiểm ID/shop/Decimal/bounds/ảnh/enum/timestamp và response identity; proxy chỉ đúng route/method/query/cookie, mutation CSRF/Origin. Link ảnh chỉ HTTPS, mở tab mới với noopener/noreferrer. Không PII/token browser storage.

Không tự retry POST. Mất phản hồi hoặc lỗi xóa xác nhận và dữ liệu cũ, yêu cầu tải lại để xác minh đã ẩn chưa. Role/account/expiry thay đổi xóa dữ liệu riêng; response muộn bị bỏ qua khi unmount.

## Kiểm chứng

PASS417 backend full trên PostgreSQL16 tmpfs marketplace_test riêng + metadata audit hiện hữu READ ONLY;16 integration cases mới cho search/shop/active/page/projection/READ ONLY/no N+1, public/cart/checkout, Seller không bật lại, giữ snapshot ở bốn shop_status, hide đua checkout/Seller edit, role/CSRF/input/COMMIT rollback. Có1 Pydantic alias warning query ở test_inventory concurrency, không fail/skip. Shared Seller projection được regression full. Ruff check/format PASS.

PASS73 frontend tests (4 nhóm mới projection/client/proxy/returnTo), lint/typecheck/production build và Docker builds. Browser thật Next→FastAPI→PostgreSQL test PASS USER403, hai shop, tên/SKU/shop/active filters, ẩn thường và mất phản hồi sau COMMIT→GET không replay, public detail404/search loại bỏ/cart HIDDEN_PRODUCT/checkout409, Seller PATCH is_active422/sửa giá không bật lại, order snapshot nguyên,28 products phân trang/empty/503/expiry/privacy/login returnTo và320/390/768/1440 không overflow/JS errors. Đã xem ảnh desktop/mobile.

Harness `D:/HealthBeauty/.p703-*`, ảnh p703-products-390.png/p703-products-1440.png; fixtures/bulk chỉ DB test guard riêng, resources đã dọn. Live localhost guest page/returnTo/navigation/API401/query400/hostile403/readiness200 PASS; không đăng nhập thay Admin thật hoặc ẩn sản phẩm nghiệp vụ. Chỉ app build/up --no-deps, baseline PostgreSQL ID/start/mount/config/root.env hash/volume/network giữ nguyên.

Không schema/data/seed/root.env/Compose/dependency/Terraform/AWS/commit/push. NOT RUN load/HTTPS/điện thoại vật lý/real S3 ảnh; P7-04 danh mục chưa triển khai. Không tạo file Excel theo yêu cầu chuyển hướng trở lại phát triển website.
