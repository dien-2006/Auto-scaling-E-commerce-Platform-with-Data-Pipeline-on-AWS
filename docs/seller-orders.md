# P6-05 — Đơn bán và hủy đơn shop

Mở `/kenh-nguoi-ban/don-hang` từ mục **Đơn bán của tôi** trong gian hàng hoặc trang sản phẩm. Danh sách lọc theo trạng thái, phân trang 24 đơn; chọn **Xem đơn** để đọc sản phẩm và thông tin giao hàng được lưu lúc đặt. Chỉ hiển thị dòng của shop đang sở hữu, không tổng tiền hay dòng shop khác.

Seller xác nhận đơn, bắt đầu giao và hoàn tất theo thứ tự PENDING → CONFIRMED → SHIPPING → COMPLETED. Seller hủy ở PENDING hoặc CONFIRMED; Buyer hủy từng đơn shop PENDING từ chi tiết đơn mua. Mọi thao tác có xác nhận. COMPLETED/CANCELLED là terminal. COD chỉ mô phỏng, chưa tích hợp thanh toán hay hãng vận chuyển.

## API

- `GET /api/v1/seller/orders?status=PENDING&page=1&page_size=24`: `items,page,page_size,total`; status tùy chọn, enum năm trạng thái, page1..2147483647, page_size1..100; query lạ bị từ chối. Sắp xếp created_at DESC, shop_order_id DESC; không query con trên từng đơn, không trả địa chỉ/số điện thoại trong list.
- `GET /api/v1/seller/orders/{shop_order_id}`: envelope `data` chứa shop_order_id/order_id/shop_id chuỗi BIGINT, order_status, subtotal Decimal string, created_at/updated_at UTC, recipient_name/phone/shipping_address snapshot, payment_method và items snapshots. Không buyer ID, email, tổng order, dòng shop khác hoặc storage keys.
- `PATCH /api/v1/seller/orders/{shop_order_id}/status`: body chỉ `expected_status,status`. Trạng thái nguồn hiện tại khác expected hoặc transition không hợp lệ trả409 `INVALID_TRANSITION`. Target đã là trạng thái hiện tại trả no-op200 kể cả expected cũ; không ghi timestamp hay hoàn tồn lại.
- `POST /api/v1/orders/{order_id}/shop-orders/{shop_order_id}/cancel`: không body, Buyer chỉ hủy PENDING; CANCELLED đã có trả no-op200. Kiểm cả ownership order, shop_order và quan hệ giữa chúng. Response cùng envelope chi tiết đơn shop của chính Buyer.

Các API riêng `no-store`; read dùng transaction READ ONLY. Mutation dùng cookie/CSRF/Origin và transaction đến COMMIT. User phải ACTIVE. Seller sở hữu shop APPROVED hoặc LOCKED mới được xử lý đơn cũ; PENDING/REJECTED bị403, không có shop403. Đơn shop khác trả404 kể cả Admin; Admin không impersonate. Khóa user ngăn protected API. Product/category ẩn không làm mất quyền đọc hoặc hủy đơn cũ.

## Hoàn tồn và cạnh tranh

Khóa user → shop → product theo ID → inventory theo product ID → shop_order; bỏ qua tài nguyên không cần như cart/category nhưng không đảo thứ tự chung. Đọc lại trạng thái dưới khóa, conditional transition và cộng tồn từ số lượng snapshot cùng một transaction. CANCELLED là guard ngăn hoàn tồn hai lần khi Buyer/Seller hoặc nhiều request cùng hủy. Không thay giá/dòng/địa chỉ/tổng đã lưu; hủy một shop không ảnh hưởng shop còn lại.

Thiếu inventory hoặc cộng tồn vượt INT_MAX trả409 `RESTOCK_CONFLICT`, toàn bộ trạng thái/tồn rollback; không tự tạo bản ghi giả. SQL lỗi/COMMIT lỗi trả503 đã làm sạch và rollback. Checkout/chỉnh tồn sử dụng cùng thứ tự khóa nên không ghi đè phép cộng hoàn tồn.

Client không tự retry mutation. Khi stale/lỗi/mất phản hồi, bỏ xác nhận cũ và yêu cầu tải lại đơn để xác minh server đã lưu hay chưa. Chặn submit trùng ở UI chỉ hỗ trợ UX; guard tại DB mới quyết định kết quả. Chuyển route/hết phiên có thể hủy chờ phản hồi nhưng không đảo COMMIT đã hoàn tất. Dữ liệu riêng xóa khi tải lại thất bại hoặc phiên không hợp lệ; không lưu PII/token vào browser storage.

## Kiểm chứng và giới hạn

PASS358 backend full trên PostgreSQL16 tmpfs `marketplace_test` riêng, gồm14 test cases mới cho ma trận25 transition, Buyer terminal, ownership/Admin, snapshot, locked shop/user, hủy lặp/song song Buyer–Seller, confirm đua cancel, cancel đua checkout/inventory, thiếu tồn/overflow/COMMIT rollback. Audit metadata DB hiện hữu READ ONLY. Có3 Pydantic UnsupportedFieldAttributeWarning trong lượt full; không test fail/skip. Ruff check/format PASS; không thay dependency/schema.

PASS61 frontend tests, lint/typecheck/production build và Docker builds. Browser thật Next → FastAPI → PostgreSQL test kiểm quy trình Seller/Buyer, snapshot/cross-shop privacy, hủy mất phản hồi sau COMMIT cả hai vai trò rồi tải lại không replay, stale, phân trang25 đơn/filter, locked shop,503 recovery, expiry và320/390/768/1440 không overflow/JS errors. Đã xem ảnh desktop/mobile; harness `D:/HealthBeauty/.p605-*`, ảnh `p605-detail-390.png`/`p605-detail-1440.png`; tài nguyên test riêng được dọn.

Không kiểm thử tải cao, điện thoại vật lý hoặc tích hợp giao hàng/thanh toán thật. S3 P6-03 còn chờ bucket, Admin P7 chưa triển khai. Không fixture/seed/migration trên DB nghiệp vụ, không AWS/Terraform/commit/push.
