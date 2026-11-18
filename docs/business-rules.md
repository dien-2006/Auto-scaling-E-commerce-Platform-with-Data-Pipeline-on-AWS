# Quy tắc nghiệp vụ Marketplace

**Quy tắc mới đang chuẩn bị (15/11/2026):** người dùng cho phép cộng dồn1mã/shop trước,1COCOGOODS sau và1COCOSHIPPING giảmriêngcước. CướcCOCOtựđặt25000/40000/60000mỗishop. Minimumgoods/ship và quy tắc snapshot ở [checkout-options-proposal.md](checkout-options-proposal.md). Chưa áp migration/featureflag vào web thật; các đoạn1coupon lịch sử vẫn mô tả bản đang chạy tới khi kích hoạt bản mới.

**15/11/2026 — Coupon/review/mua tiếp:** theo yêu cầu trực tiếp mới, mở coupon và đánh giá sản phẩm, thay thế giới hạn lịch sử “không thêm voucher/review”. Mỗi đơn1coupon, mỗi khách1lượt/mã; mã shop chỉ tính hàng shop, minimum không gồm shipping, hoàn lượt khi hủy toàn bộ. Chỉ buyer của dòng hàng đã COMPLETED được đánh giá1lần1–5sao. Đơn PENDING không ngăn mua sản phẩm khác. Chi tiết tại [buyer-coupons-reviews.md](buyer-coupons-reviews.md); không đổi schema.

**Quyết định mới nhất — Admin không mua hàng/tạo shop:** chỉ USER ACTIVE dùng giỏ/checkout/địa chỉ/đơn Buyer và hồ sơ đăng ký Seller. ADMIN vẫn đăng nhập/quản trị/xem catalog công khai nhưng các API trên trả403 COMMERCE_FORBIDDEN, kể cả replay key cũ sau nâng quyền. Không xóa shop/đơn/giỏ đã có. Quy tắc này thay thế các đoạn lịch sử cho phép Admin mua hoặc tạo shop như USER.

P1-03, ngày 09/11/2026 (Asia/Bangkok). Q03–Q06 đã được người dùng đồng ý trong phiên làm việc này. Tài liệu phân biệt yêu cầu nguồn, quyết định được duyệt và cách triển khai trong giới hạn schema. Không thay đổi SQL.

**Cập nhật trực tiếp từ người dùng ngày 10/11/2026:** đăng ký mới yêu cầu mật khẩu **trên8 ký tự (tối thiểu9), tối đa128**, có chữ hoa A–Z, số0–9 và ký tự đặc biệt (Unicode punctuation/symbol; khoảng trắng không tính là ký tự đặc biệt). Không bắt buộc chữ thường, không trim/normalize mật khẩu. Thay thế lựa chọn kỹ thuật min12 trước đây; không đổi schema hoặc mật khẩu đã lưu. Login kiểm hash cũ, không áp complexity đăng ký để tránh khóa tài khoản hiện hữu; hỗ trợ mật khẩu9 ký tự mới.

## Nguồn và các quyết định được duyệt

SQL marketplace_schema.sql và DOCX là nguồn chính; yêu cầu trực tiếp giới hạn mỗi lần một task. Audit P1-02 mới nhất xác nhận 12 bảng/86 cột thuộc schema marketplace phù hợp SQL.

| Mã | Quyết định được người dùng duyệt |
| --- | --- |
| Q03 | Buyer hủy đơn shop ở PENDING; Seller hủy ở PENDING/CONFIRMED; hoàn tồn đúng một lần. Shop bị khóa vẫn xử lý đơn cũ, user bị khóa không dùng API bảo vệ |
| Q04 | Access JWT 15 phút, logout xóa cookie, chưa refresh token |
| Q05 | Giỏ cần đăng nhập; chưa thu phí/giảm giá; chặn mua từ shop của mình; ẩn danh mục cha thì ẩn sản phẩm thuộc nhánh con |
| Q06 | Ảnh dùng S3; local cần endpoint S3 tương thích được cung cấp hoặc task thêm MinIO được duyệt riêng |

Chưa có endpoint/credentials storage local cụ thể; đây là dependency của P6-03, không ngăn khởi tạo frontend/backend. Không dùng MinIO của dự án ngân hàng hoặc thêm dịch vụ storage trong P2-04 nếu chưa được yêu cầu.

## Quy tắc từ SQL và DOCX

Guest xem và tìm sản phẩm/shop không cần login. USER ACTIVE là Buyer; owner có thêm quyền Seller mà không đổi user_role. Một owner tối đa một shop. Chỉ shop APPROVED được bán; shop LOCKED không đăng sản phẩm mới/nhận đơn mới. ADMIN quản lý user/shop/product/category; role ADMIN không tự cấp qua API công khai.

Mỗi giỏ thuộc một user, unique product/cart, quantity nguyên dương. Giỏ không giữ tồn hoặc cố định giá. Checkout nhiều shop, chỉ COD mô phỏng, kiểm lại tồn và giá, lưu snapshot tên/giá/địa chỉ. Một lần checkout tạo một order, một shop_order mỗi shop và order_items đúng composite FK. UUID idempotency unique theo buyer ngăn tạo trùng. Không sửa dòng/giá/địa chỉ snapshot sau mua.

Tạo product và inventory cùng transaction. Tồn không âm; seller update không được ghi đè số lượng sau checkout. Danh mục không có chu kỳ, không xóa liên kết dữ liệu. Có tối đa một ảnh primary/product và một địa chỉ default/user.

## Ma trận quyền

| Hành động | Guest | Buyer ACTIVE | Seller owner ACTIVE | Admin ACTIVE |
| --- | --- | --- | --- | --- |
| Catalog public | Có | Có | Có | Có |
| Địa chỉ/giỏ/đơn cá nhân | Không | Của mình | Của mình khi mua | Của mình khi mua |
| Đăng ký shop | Không | Khi chưa có shop | Không tạo shop thứ hai | Cùng giới hạn owner nếu dùng chức năng Buyer |
| Hồ sơ shop | Không | Nếu là owner | Xem/sửa shop mình | Quản trị trạng thái qua API riêng |
| Sản phẩm/ảnh/tồn | Không | Không nếu chưa có shop | Shop APPROVED của mình | Chỉ quyền quản trị nêu trong DOCX, không giả mạo Seller |
| Đơn shop | Không | Không | Chỉ shop mình, kể cả đơn cũ khi shop LOCKED | Không thêm chức năng xử lý đơn Admin |
| Khóa user/duyệt shop/ẩn product/quản lý category | Không | Không | Không | Có |

USER LOCKED bị từ chối mọi protected API dù JWT còn hạn. Admin không tự nhiên đọc giỏ/địa chỉ/đơn cá nhân của người khác. Với tài nguyên người khác, API trả 404; thiếu quyền chức năng trả 403. Catalog không lộ email/phone người mua, contact_email riêng hoặc password_hash.

## Trạng thái đơn được duyệt

| Nguồn | Đích | Người thực hiện | Hệ quả |
| --- | --- | --- | --- |
| PENDING | CONFIRMED | Seller owner | Không trừ tồn thêm |
| CONFIRMED | SHIPPING | Seller owner | Không trừ tồn thêm |
| SHIPPING | COMPLETED | Seller owner | COD mô phỏng; không giả tích hợp vận chuyển/thanh toán |
| PENDING | CANCELLED | Buyer owner hoặc Seller owner | Hoàn tồn một lần cùng transaction |
| CONFIRMED | CANCELLED | Seller owner | Hoàn tồn một lần cùng transaction |

COMPLETED/CANCELLED là terminal; không quay lùi. Hủy theo shop_order, không tự hủy shop khác trong order. Request lặp đúng target hiện tại là no-op, không hoàn tồn lại; transition không hợp lệ trả 409. Không có order_status tổng trong bảng orders: UI hiển thị trạng thái từng đơn shop, không phát minh enum lưu DB.

Nếu shop LOCKED nhưng owner ACTIVE, owner chỉ xử lý đơn cũ; không sửa catalog/tồn hoặc nhận đơn mới. Nếu owner LOCKED, phải chờ Admin mở khóa; không thêm đường impersonation hoặc quyền Admin xử lý đơn. Ẩn product/category không hủy đơn đã commit.

## Phiên đăng nhập được duyệt

JWT access TTL 15 phút, không refresh. Logout xóa cookie; JWT bị sao chép còn hạn vẫn có thể dùng đến exp nếu account ACTIVE. Mỗi protected request đọc role/status/shop hiện tại từ DB. Không thêm bảng token/session, không session trong bộ nhớ pod. Hết phiên chuyển login với return URL nội bộ; không tự tạo checkout key mới rồi gửi lại.

## Cách triển khai trong giới hạn schema

- Catalog public: product.is_active, shop APPROVED, category và toàn bộ ancestor active. Tồn 0 vẫn có thể hiện nhưng không mua. Product thiếu inventory không được mua, không tự tạo inventory trong GET.
- Giỏ cần login, không guest-cart merge. Bản đầu checkout toàn bộ giỏ; một dòng không hợp lệ thì không tạo đơn nào. Client gửi quantity/expected unit price để phát hiện thay đổi, server tính lại tổng. Không có phí/discount/tax line trong schema; tổng là tổng các dòng hàng.
- Giỏ add và checkout đều chặn self-purchase. Checkout kiểm user/shop/product/category và tồn dưới khóa trước commit, không tin UI.
- Cùng buyer/key đã commit trả đơn cũ; payload retry không được áp dụng lại. Không có request hash, vì vậy không hứa phát hiện mọi payload mismatch. Client phải dùng key mới cho ý định mua khác; key cũ giữ qua timeout.
- Schema chỉ có is_active, không lưu ai/lý do ẩn. Bản đầu chỉ có thao tác ẩn; không cung cấp thao tác bật lại qua API để tránh Seller gỡ quyết định Admin. Chưa thêm moderation column/bảng hoặc endpoint reactivation. Nếu cần bật lại phải lập quyết định/task riêng.
- Danh mục inactive không xóa product; bật cha lại không đổi is_active của con. API Admin cho cập nhật is_active danh mục vì thuộc quản lý danh mục; không tạo cascade mutation dữ liệu con.
- Shop creation PENDING; Admin PENDING→APPROVED/REJECTED, APPROVED→LOCKED. Chưa thêm resubmit/unlock workflow vì DOCX chưa quy định; không tự mở rộng enum hay tạo endpoint mở shop lại.
- Tồn Seller dùng delta có precondition số lượng hiện tại, không ghi tuyệt đối stale. Sau timeout phải đọc lại và xác nhận, không retry mù. Không tuyên bố exactly-once inventory adjustment khi schema không có operation ID.
- Không thêm chức năng chat/voucher/review/biến thể/thanh toán thật hoặc sửa profile cá nhân ngoài FR. Không fake catalog, giá, rating, số bán hay tồn.

## Walkthrough thiết kế và test dự kiến

| Tình huống | Kết quả | Task test |
| --- | --- | --- |
| Guest tìm tên, lọc category, mở shop | Chỉ catalog hợp lệ, không PII | P3-01–05 |
| Buyer checkout hàng hai shop | Một order, hai shop_orders, snapshots đúng | P5-01–03 |
| Hai buyer tranh tồn cuối | Tối đa một thành công, không đơn dở | P5-02 |
| Timeout sau commit, retry cùng key | Cùng order ID, không giảm tồn lại | P5-02–03 |
| Buyer/Seller truy cập đơn người khác | 404 | P4-02/P5-04/P6-05 |
| Seller PENDING đăng product | 403 | P6-01–02 |
| Seller chỉnh tồn cùng checkout | Không âm, không mất update | P6-04 |
| Hai request hủy một đơn | Hoàn tồn đúng một lần | P6-05 |
| Admin khóa shop cạnh tranh checkout | Thứ tự khóa/commit quyết định; sau khóa không nhận đơn | P7-02 |
| Sửa cây đồng thời tạo cycle | Cây không chu kỳ | P7-04 |
| JWT user vừa khóa | Protected API từ chối | P4-02 |
| Seller bật lại sản phẩm ẩn | Không có endpoint/field cho phép | P7-03 |

Đây là review thiết kế, chưa phải test ứng dụng đã chạy. P1-03 không cấp quyền bắt đầu P2 hoặc thay database.
