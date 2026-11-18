# Hợp đồng REST API Marketplace

**Checkout mở rộng đang chuẩn bị, chưa áp DB thật (15/11/2026):** GET /checkout/options, POST /checkout/quote; requestcheckout cóshop_coupons/coco_coupon_code/shipping_coupon_code/shipping_method vàexpectedtotals. Mỗi shop1mãGOODS+COCOGOODS+COCOSHIPPING;ship STANDARD/EXPRESS/COCOEXPRESS;COD/BANK_TRANSFER(cấuhình)/MOMO-VNPAYdisabled. Cần schema proposal vàfeatureflag trước khi dùng; contractchi tiết tại [checkout-options-proposal.md](checkout-options-proposal.md). Không coi đây là cổng thanh toán đã tích hợp.

**CHECKOUT-AUTO-RESOLVE (15/11/2026):** GET /api/v1/orders/checkout-status nhận header Idempotency-Key(UUID), USER ACTIVE, trả `{data:OrderDetail|null}` chỉ đơn của buyer hiện tại, READ ONLY/no-store. Không tạo đơn/không replay POST. UI tự dùng để mở form thay màn hình yêu cầu gửi lại; không có đơn thì giữ UUID để chống request cũ còn đang trên mạng. Xem [buyer-coupons-reviews.md](buyer-coupons-reviews.md).

**15/11/2026 — Coupon/review:** POST /coupons/quote; checkout nhận coupon_code?/expected_coupon_discount?; order list/detail trả discount_amount/shipping_fee. GET /products/{id}/reviews public phân trang; GET/POST /order-items/{id}/review chỉ Buyer đã mua và COMPLETED. Admin không dùng API coupon/private review. Contract và quy tắc transaction mới ở [buyer-coupons-reviews.md](buyer-coupons-reviews.md), thay thế giới hạn lịch sử chưa hỗ trợ coupon/review. Giữ CSRF/Origin/idempotency, không sửa schema.

**SCHEMA25/CRUD/K6 — 14/11/2026:** Seller có DELETE /seller/shop/{shop_id} (204/404/409SHOP_IN_USE, USER ACTIVE/owner, không cascade business history), DELETE /seller/products/{product_id} (204/404/409PRODUCT_IN_USE, shopAPPROVED/owner, rollback inventory khi FK chặn). Không có DELETE collection shop. Nextpublic GET /api/v1/products và /{id} fixed-proxy/queryallowlist không forward privatecookies; k6 cùng URL web, không authbypass. Order mapping thêm discount_amount/shipping_fee/paymentmethod20 theoSQL25, nhưng checkoutrequest vẫn COD. Các hạn chế lịch sử nói “chưa có xóa” đã bị thay thế ở phạm vi trên. Chi tiết docs/schema25-crud-k6.md.

**ADMIN-COMMERCE-01 — cập nhật quyền theo yêu cầu người dùng:** AccessPolicy.buyer chỉ nhận USER ACTIVE. ADMIN trả403 COMMERCE_FORBIDDEN ở cart/addresses/Buyer orders/cancel/checkout và GET/POST/PATCH seller/shop, trước truy cập dữ liệu cá nhân hoặc replay đơn. auth/me/login/logout và API Admin không đổi, public catalog vẫn đọc được. Các đoạn lịch sử USER/ADMIN dưới đây đã bị thay thế ở phạm vi Buyer/hồ sơ đăng ký shop. Không đổi schema/dữ liệu hoặc xóa đơn/shop tồn tại.

Thiết kế P1-03 ngày 09/11/2026 theo business-rules.md và architecture.md, Q03–Q06 đã được người dùng duyệt. Base /api/v1. Endpoint categories/shop/products đã triển khai trong P3-01–02; auth và các endpoint nghiệp vụ khác vẫn là kế hoạch. Xem ghi chú triển khai cuối tài liệu.

## Quy ước

JSON UTF-8. ID BIGINT là chuỗi số dương, money là Decimal string tối đa 2 chữ số thập phân, trong giới hạn NUMERIC(14,2); timestamps UTC ISO-8601. Validate quantity/delta integer và overflow, chuỗi nonblank/length theo SQL, email/slug/phone hợp lệ theo schema request. Không trim password; không mass assignment hoặc nhận unknown mutation fields.

Làm rõ P5-01: NUMERIC(14,2) áp dụng giá/cột tiền lưu DB. `line_total`, `subtotal`, `total_amount` dẫn xuất của giỏ không được lưu DB và có thể lớn hơn giới hạn cột khi quantity rất lớn; trả Decimal string chính xác, không clamp/làm tròn. Checkout phải từ chối tổng vượt giới hạn cột orders ở P5-02. Tổng giỏ gồm cả dòng unavailable, chỉ là tạm tính; không giữ giá/tồn. Xem docs/cart.md.

Response resource: {data:...}. Danh sách: {items:[],page:1,page_size:24,total:0}, page>=1, page_size 1..100 mặc định 24; quá cuối trả items=[]; query sai trả 422. Các danh sách nhỏ không phân trang ghi rõ shape riêng. DELETE/logout 204 không body; create 201, update 200. X-Request-ID cho response; auth/private data Cache-Control:no-store.

Error shape: {error:{code:"OUT_OF_STOCK",message:"Sản phẩm không đủ tồn kho",details:[{field:"items.0.quantity",reason:"insufficient_stock"}],request_id:"..."}}. Không echo password/token/input nhạy cảm trong validation, không stack/SQL/DSN.

| HTTP | Mã | Nghĩa |
| --- | --- | --- |
| 400 | INVALID_REQUEST | Request thiếu điều kiện cơ bản |
| 401 | AUTH_REQUIRED, INVALID_TOKEN, TOKEN_EXPIRED | Chưa xác thực hoặc phiên không hợp lệ |
| 403 | FORBIDDEN, USER_LOCKED, SHOP_NOT_APPROVED, CSRF_FAILED | Không đủ quyền hoặc trạng thái không cho phép |
| 404 | NOT_FOUND | Không tồn tại hoặc không thuộc quyền được xem |
| 409 | EMAIL_EXISTS, SHOP_EXISTS, SKU_EXISTS, SLUG_EXISTS, OUT_OF_STOCK, CART_CHANGED, PRICE_CHANGED, STALE_INVENTORY, INVALID_TRANSITION | Xung đột nghiệp vụ/dữ liệu |
| 422 | VALIDATION_ERROR | Sai kiểu/giới hạn/field |
| 503 | DEPENDENCY_UNAVAILABLE | DB/storage không sẵn sàng |
| 500 | INTERNAL_ERROR | Lỗi nội bộ, thông báo chung |

Auth: JWT cookie HttpOnly theo architecture.md. Mọi unsafe method cần X-CSRF-Token và Origin/Referer hợp lệ, kể cả register/login/logout. Tất cả protected API yêu cầu user ACTIVE. ADMIN không tự được truy cập tài nguyên Buyer/Seller người khác. Owner không đúng trả 404; role sai trả 403.

Search q tối đa 200 ký tự, tên ILIKE parameterized, escape wildcard để tìm literal; không hứa tìm không dấu. category_id bao gồm nhánh con, ancestor active theo chính sách. Sort allowlist: newest (created_at DESC,product_id DESC), price_asc (price ASC,product_id DESC), price_desc (price DESC,product_id DESC). Các list khác mặc định created_at DESC, ID DESC. Không nhận SQL expression làm sort.

## Endpoint public và authentication

Cập nhật 10/11/2026: password đăng ký9–128 ký tự, có chữ hoa A–Z, số0–9, ký tự đặc biệt (punctuation/symbol, không tính whitespace), không trim. Login nhận mật khẩu1–128 ký tự để kiểm hash cũ và mật khẩu9 ký tự mới, không buộc áp complexity của đăng ký cho tài khoản hiện hữu. Backend và frontend cùng kiểm đăng ký.

| Method/path | Request/query | Response |
| --- | --- | --- |
| GET /health/live (ngoài /api/v1) | Không | 200 {status:"ok"}, không DB |
| GET /health/ready (ngoài /api/v1) | Không | 200 {status:"ready"} hoặc 503; không DSN |
| GET /auth/csrf | Không | 200 {data:{csrf_token}}, signed cookie; no-store |
| POST /auth/register | email,password,full_name,phone? | 201 UserPrivate; chưa tự login |
| POST /auth/login | email,password | 200 UserPrivate, set JWT cookie |
| POST /auth/logout | Không; không bắt buộc JWT còn hạn | 204, clear cookies; không thu hồi token bị sao chép |
| GET /auth/me (protected) | Không | 200 UserPrivate + owned_shop {shop_id,shop_status}? |
| GET /categories | Không | {items:CategoryTree[]} public active tree |
| GET /shops/{shop_slug} | Không | ShopPublic; không hợp lệ trả 404 |
| GET /products | q?,category_id?,shop_id?,page,page_size,sort | ProductSummary list |
| GET /products/{product_id} | Không | ProductDetail; 404 nếu ẩn/không public |

## Buyer và địa chỉ

Mọi endpoint phần này yêu cầu Buyer ACTIVE và ownership. User ID lấy từ auth, không từ payload.

| Method/path | Request/query | Response |
| --- | --- | --- |
| GET /addresses | Không | {items:Address[]} của mình |
| POST /addresses | recipient_name,phone,address_line,ward?,district?,city,is_default | 201 Address |
| PATCH /addresses/{id} | Các field địa chỉ cần đổi | 200 Address; default unset/set nguyên tử |
| DELETE /addresses/{id} | Không | 204, không đổi snapshot order |
| GET /cart | Không | Cart; chưa có cart trả rỗng, không tạo DB bằng GET |
| POST /cart/items | product_id,quantity cộng thêm | 200 Cart; upsert atomic |
| PATCH /cart/items/{id} | quantity mục tiêu dương | 200 Cart; không quantity=0 |
| DELETE /cart/items/{id} | Không | 204 |
| POST /orders/checkout | UUID Idempotency-Key header; body address_id,payment_method:"COD",items:[{product_id,quantity,expected_unit_price}] | 201 OrderDetail lần đầu; 200 đơn đã commit khi replay |
| GET /orders | page,page_size | OrderSummary list của mình |
| GET /orders/{id} | Không | OrderDetail |
| POST /orders/{id}/shop-orders/{shop_order_id}/cancel | Không | 200 ShopOrder; Buyer chỉ PENDING; CANCELLED đã có trả no-op |

## Seller

Owner là chủ shop; tạo shop yêu cầu chưa có shop. Xem hồ sơ/catalog/đơn của chính mình không đòi APPROVED; tạo/sửa catalog/ảnh/tồn phải APPROVED. Đơn cũ của shop LOCKED vẫn xử lý được khi owner ACTIVE.

| Method/path | Request/query | Response |
| --- | --- | --- |
| POST /seller/shop | shop_name,shop_slug,description?,contact_email? | 201 ShopPrivate PENDING |
| GET /seller/shop | Không | ShopPrivate mọi trạng thái |
| PATCH /seller/shop | shop_name?,description?,contact_email? | 200 ShopPrivate; không owner/status/slug |
| GET /seller/products | q?,is_active?,page,page_size | SellerProduct list |
| GET /seller/products/{id} | Không | SellerProduct, kể cả inactive |
| POST /seller/products | sku,category_id,product_name,description?,price,initial_quantity | 201 SellerProduct; tạo inventory cùng transaction |
| PATCH /seller/products/{id} | sku?,category_id?,product_name?,description?,price? | 200 SellerProduct; không shop_id/is_active |
| POST /seller/products/{id}/hide | Không | 200 SellerProduct inactive |
| POST /seller/products/{id}/images/upload-url | content_type,size_bytes | {upload_url,fields,image_key,expires_at}; presigned POST |
| POST /seller/products/{id}/images | image_key,is_primary,sort_order | 201 ProductImage; verify S3 object trước liên kết |
| PATCH /seller/products/{id}/images/{image_id} | is_primary?,sort_order? | 200 ProductImage; không tự đổi key |
| DELETE /seller/products/{id}/images/{image_id} | Không | 204, bỏ reference; không xóa S3 object |
| GET /seller/products/{id}/inventory | Không | {product_id,quantity,updated_at} |
| POST /seller/products/{id}/inventory/adjustments | delta; X-Expected-Quantity header không âm | 200 Inventory; stale 409, không retry mù |
| GET /seller/orders | status?,page,page_size | ShopOrderSummary list |
| GET /seller/orders/{id} | Không | ShopOrderDetail chỉ shop mình |
| PATCH /seller/orders/{id}/status | expected_status,status | 200 ShopOrderDetail, đúng state machine |

Không có endpoint reactivation sản phẩm, resubmit/unlock shop hoặc upload logo trong bản đầu vì nguồn chưa quy định quy trình và schema chưa phân biệt ai ẩn. logo_key read-only, không cho gán arbitrary key.

## Admin

Tất cả yêu cầu ADMIN ACTIVE; không chấp nhận role client/JWT cũ thay cho đọc DB.

| Method/path | Request/query | Response |
| --- | --- | --- |
| GET /admin/users | q?,status?,page,page_size | AdminUser list không hash |
| PATCH /admin/users/{id}/status | user_status | 200 AdminUser; chỉ ACTIVE/LOCKED |
| GET /admin/shops | q?,status?,page,page_size | AdminShop list |
| PATCH /admin/shops/{id}/status | expected_status,shop_status | 200 AdminShop; PENDING→APPROVED/REJECTED, APPROVED→LOCKED |
| GET /admin/products | q?,shop_id?,is_active?,page,page_size | AdminProduct list |
| POST /admin/products/{id}/hide | Không | 200 AdminProduct inactive |
| GET /admin/categories | Không | {items:CategoryTree[]} gồm inactive |
| POST /admin/categories | category_name,category_slug,parent_category_id?,is_active | 201 Category |
| PATCH /admin/categories/{id} | category_name?,category_slug?,parent_category_id?,is_active? | 200 Category; ngăn cycle, không xóa dữ liệu |

Không có API delete user/shop/product/category/order hoặc chỉnh giá/dòng đơn đã mua. Admin user unlock là user_status ACTIVE theo DOCX; không đồng nghĩa unlock shop chưa được đặc tả.

P7-01 (11/11/2026): GET admin/users và PATCH user status đã triển khai, response list items/page/page_size/total hoặc mutation envelope data AdminUser. q tìm tên/email/phone không phân biệt hoa/thường, literal wildcard, tối đa200; status ACTIVE/LOCKED, mặc định page1/page_size24 tối đa100. Theo yêu cầu “bỏ qua phần đó” về khóa Admin, thao tác trạng thái chỉ áp dụng target USER; target ADMIN chỉ xem, mọi PATCH trả403 ADMIN_PROTECTED. Không role/PII mutation hay cấp quyền. Same status no-op200, missing404; DB/COMMIT lỗi503 rollback. ID string/UTC/no hash/no-store; xem [admin-users.md](admin-users.md).

P7-02 (11/11/2026): GET admin/shops trả items/page/page_size/total, q tìm tên/slug/contact_email literal≤200, status enum bốn trạng thái, page mặc định1/page_size24 tối đa100. PATCH /admin/shops/{id}/status nhận expected_status/shop_status; PENDING→APPROVED/REJECTED và APPROVED→LOCKED, không unlock/resubmit. Same target no-op200, stale/transition sai409 INVALID_TRANSITION, missing404; response envelope data ShopPrivate (logo_url null, không logo_key). ADMIN ACTIVE, cookie/CSRF/Origin, READ ONLY/no-store cho read và user→shop row lock/conditional update/COMMIT cho write. Khóa shop chặn checkout mới, không hủy đơn cũ; xem [admin-shops.md](admin-shops.md).

P7-03 (11/11/2026): GET admin/products q tìm tên/SKU literal≤200, shop_id/is_active/page/page_size; items/page/page_size/total, default24/max100. POST /admin/products/{id}/hide không body, envelope data AdminProduct tương đương SellerProduct, no-op nếu đã ẩn. ADMIN ACTIVE/mọi shop_status, shared category→shop→product locks sau user tới COMMIT; read READ ONLY/private no-store, errors404/403/422/503 theo contract. Không reactivation cho Seller/Admin vì schema chưa phân biệt ai ẩn; Seller sửa hồ sơ không bật lại. Public/cart/checkout chặn sản phẩm ẩn, không đổi tồn hay snapshot đơn. Xem [admin-products.md](admin-products.md).

P7-04 (11/11/2026): GET admin/categories có active/inactive theo CategoryTree. POST/PATCH category_name trim1..120, category_slug lowercase alnum/hyphen1..140 unique, parent_category_id chuỗi BIGINT/null, is_active strict boolean (POST mặc địnhtrue). PATCH nonempty, chỉ parent được null. Mutation trả201/200 envelope data node children=[], GET để đọc cây đầy đủ; không delete. ADMIN ACTIVE/CSRF/Origin, READ ONLY/no-store cho read, exclusive advisory tree lock sau user xuyên COMMIT cho writes. Slug409 SLUG_EXISTS, parent thiếu422 INVALID_PARENT, cycle409 CATEGORY_CYCLE, missing404, depth>100 cấp422 CATEGORY_TOO_DEEP (khớp public client). Tắt cha ẩn cả nhánh nhưng không thay con/product/order; không expected_version, cập nhật sau cùng quyết định field không vi phạm cây. Xem [admin-categories.md](admin-categories.md).

## Shapes response

Các field ID/timestamp/status ghi nhận từ server là read-only nếu không nằm trong mutation request ở trên. Tất cả resource trả trong data trừ list và health.

- UserPrivate: user_id,email,full_name,phone,user_role,user_status,created_at. AdminUser tương tự; không password_hash.
- Category: category_id,parent_category_id,category_name,category_slug,is_active; tree thêm children.
- ShopPublic: shop_id,shop_name,shop_slug,description,logo_url. ShopPrivate thêm owner_user_id,contact_email,shop_status,created_at,updated_at. AdminShop có các trường private theo chức năng quản trị.
- ProductSummary: product_id,product_name,price,currency:"VND",primary_image_url nullable,shop:{shop_id,shop_name,shop_slug},category_id,in_stock. ProductDetail thêm description,sku,images:[{product_image_id,url,is_primary,sort_order}],available_quantity. SellerProduct/AdminProduct thêm is_active và timestamps, không PII user khác.
- Address: address_id,recipient_name,phone,address_line,ward,district,city,is_default,created_at; không nhận user_id giả owner.
- Cart: shops:[{shop_id,shop_name,shop_slug,items:[{cart_item_id,product_id,product_name,quantity,unit_price,line_total,available_quantity,is_available,unavailable_reason,primary_image_url}],subtotal}],total_amount. Inactive product còn trong giỏ vẫn hiện để xóa nhưng không được checkout.
- OrderSummary: order_id,total_amount,payment_method,created_at,shop_orders:[{shop_order_id,shop_id,shop_name,order_status,subtotal}]. Không order_status tổng giả.
- OrderDetail: summary + recipient_name,phone,shipping_address snapshot; mỗi shop_order có items:[{order_item_id,product_id,product_name,unit_price,quantity,line_total}]. Seller ShopOrderDetail chỉ dòng shop mình và shipping snapshot cần thiết, không tổng/dòng shop khác.

P6-05 đã triển khai Seller list/detail/status và Buyer cancel theo bảng trên. Seller list trả items/page/page_size/total (mặc định24, tối đa100); summary gồm shop_order_id/order_id/shop_id/order_status/subtotal/created_at/updated_at. Detail và mutation/cancel trả envelope data cùng summary + recipient_name/phone/shipping_address/payment_method/items snapshot. APPROVED/LOCKED owner ACTIVE được xử lý đơn cũ; foreign404 kể cả Admin. Target hiện tại trả no-op200; stale/transition sai409 INVALID_TRANSITION, thiếu tồn hoặc hoàn vượt INT_MAX409 RESTOCK_CONFLICT và rollback. Đọc/mutation no-store; xem [seller-orders.md](seller-orders.md).
- ProductImage: product_image_id,product_id,image_key,url,is_primary,sort_order. Không đưa presigned upload fields vào public product response.

## Checkout và giới hạn retry

P5-02 đã triển khai backend theo [checkout-api.md](checkout-api.md): 201 tạo mới/200 replay, tối đa1000 dòng request, lock order/thực thi nguyên tử, tổng NUMERIC14,2, retry tối đa3 attempt lỗi PostgreSQL được chọn. UI/proxy checkout vẫn thuộc P5-03.

P5-03 đã triển khai UI/proxy theo [checkout-ui.md](checkout-ui.md): UUID + payload tham chiếu tối thiểu giữ sessionStorage theo user, retry/reload cùng key, xác nhận từ server. Không lưu JWT hoặc nội dung địa chỉ/tên/phone trong storage. Repair sau business error giữ key và yêu cầu review mới; không tạo key khác khi kết quả chưa rõ. Checkout proxy limit128KiB, các proxy auth/cart/address8KiB.

Client tạo key UUID một lần cho một ý định checkout. Giữ key qua timeout/reload trong sessionStorage, không lưu JWT/địa chỉ trong đó. Trước submit có thể thay giỏ và tạo intent mới; sau timeout không rõ commit phải retry key/payload cũ, không tự tạo đơn mới. UI vô hiệu nút khi loading chỉ hỗ trợ UX, unique DB mới chống trùng.

Sau auth và validate hình dạng request/key, service tìm order theo buyer/key trước kiểm giỏ. Replay trả đơn cũ, không áp dụng payload retry khác; không hứa phát hiện mismatch vì không có request hash. Lần đầu items phải khớp toàn bộ giỏ product_id/quantity; so expected_unit_price với Decimal DB. Địa chỉ phải thuộc Buyer, shop APPROVED và không self-purchase, catalog hợp lệ, tồn đủ. Mọi lỗi rollback toàn bộ, không đơn/giảm tồn dở. Nếu chưa có commit thì sửa payload và thử lại không gây đơn trùng; client nên quản lý intent rõ ràng.

Inventory adjustment không có operation ID persist: X-Expected-Quantity dưới row lock phát hiện stale thông thường nhưng có giới hạn ABA khi giá trị quay về cũ. Sau timeout UI GET lại và yêu cầu xác nhận mutation mới; không tự retry delta hoặc tuyên bố exactly-once.

P6-04 đã triển khai: GET/POST trả envelope `data` với product_id chuỗi BIGINT, quantity nguyên và updated_at UTC; `Cache-Control: no-store`. Delta nguyên khác 0 trong ±2147483647; expected nguyên 0..2147483647, header duy nhất dạng thập phân chuẩn. Input sai trả422; stale409 `STALE_INVENTORY`, kết quả âm/vượt INT_MAX409 `INVALID_STOCK`, thiếu inventory409 `INVENTORY_UNAVAILABLE` (không tự tạo). ACTIVE owner/shop APPROVED; foreign product404 kể cả Admin. Xem [seller-inventory.md](seller-inventory.md).

## Coverage FR và review

| FR | API chính | UI | Task kiểm thử |
| --- | --- | --- | --- |
| FR-B01 | /auth/* | /login,/register | P4-01–03 |
| FR-B02 | /categories,/products,/products/{id},/shops/{slug} | /,/products,/products/{id},/shops/{slug} | P3-01–05 |
| FR-B03 | GET /products?q=&category_id= | Header search/list | P3-02/04 |
| FR-B04 | /cart,/cart/items/* | /cart | P5-01 |
| FR-B05 | /addresses/*,/orders/checkout | /checkout | P4-04/P5-02–03 |
| FR-B06 | /orders,/orders/{id} | /account/orders/* | P5-04 |
| FR-S01 | POST /seller/shop | /seller/register | P6-01 |
| FR-S02 | GET/PATCH /seller/shop | /seller/shop | P6-01 |
| FR-S03 | /seller/products/* và images | /seller/products/* | P6-02–03 |
| FR-S04 | /seller/products/{id}/inventory* | /seller/inventory | P6-04 |
| FR-S05 | /seller/orders/* | /seller/orders/* | P6-05 |
| FR-A01 | /admin/users/* | /admin/users | P7-01 |
| FR-A02 | /admin/shops/* | /admin/shops | P7-02 |
| FR-A03 | /admin/products/* | /admin/products | P7-03 |
| FR-A04 | /admin/categories/* | /admin/categories | P7-04 |

Review thiết kế gồm 401/403/404 ownership, validation, response không secrets, pagination, concurrent checkout/inventory/hủy, rollback và state machine; các tình huống tại business-rules.md. Chưa có code để chạy runtime tests. Không dùng tài liệu này làm quyền tự bắt đầu P2.

## P3-01 — endpoint đã triển khai

GET /api/v1/categories trả {items:CategoryTree[]} không phân trang, chỉ các node active có toàn bộ tổ tiên active và nối về root. Root/children theo category_name ASC (collation database), category_id ASC. Nhánh thiếu tổ tiên hoặc cycle không được đưa ra public, không tự sửa dữ liệu. Một query danh mục, không N+1.

GET /api/v1/shops/{shop_slug} trả {data:ShopPublic} cho APPROVED; PENDING/REJECTED/LOCKED và không tồn tại đều 404 NOT_FOUND. Slug dài hơn 160 trả 422. ID là chuỗi, không contact_email/owner ID/logo_key hoặc dữ liệu đăng nhập. logo_url hiện null kể cả khi DB có key vì delivery S3/logo chưa cấu hình; không bịa URL hoặc public raw key. Hai GET dùng READ ONLY transaction, thiếu/lỗi DB trả 503 sanitized; có request ID/no-store. Chưa có list shops, sản phẩm/search hoặc auth trong task này.

## P3-02 — sản phẩm và tìm kiếm đã triển khai

GET /api/v1/products nhận ProductQuery (q tối đa 200, category_id/shop_id dương trong BIGINT, page 1..2147483647, page_size 1..100 mặc định 24, sort newest/price_asc/price_desc). Unknown query parameter trả 422. q trim khoảng trắng, ILIKE parameterized với wildcard literal được escape; chưa tìm không dấu. category_id gồm con/cháu; danh mục phải nối tới root qua toàn bộ tổ tiên active. Sản phẩm inactive hoặc shop không APPROVED không được trả. Trang quá cuối/ID filter không tồn tại trả items=[] với total phù hợp; 2 SELECT cho count và page, không N+1. Pagination offset không bảo đảm snapshot bất biến giữa các lần request khi catalog thay đổi.

GET /api/v1/products/{product_id} trả {data:ProductDetail}, missing/hidden/shop không hợp lệ/category ẩn cùng 404; ID sai định dạng/giới hạn trả 422 khi dependency DB sẵn sàng. Dùng cùng predicate public như list. Inventory thiếu hoặc quantity=0 trả in_stock=false, available_quantity=0; sản phẩm hết hàng vẫn xem được. Giá Decimal string chính xác, ID string. Không lộ owner/email/hash/key. READ ONLY session và sanitized 503 như P3-01; không thêm DDL/index/seed.

Điểm delivery ảnh được làm rõ trong phạm vi P3-02: primary_image_url và images[].url hiện null vì chưa có cấu hình S3 (giống logo_url P3-01); URL trở thành chuỗi sau task delivery P6-03. Metadata ảnh thật vẫn gồm product_image_id/is_primary/sort_order, xếp primary DESC, sort_order ASC, image_id ASC. Không đọc hoặc trả raw image_key, không bịa URL. Chi tiết tối đa 2 SELECT bất kể số ảnh. Frontend preview chưa tích hợp API; không coi các mẫu UI là dữ liệu response production.

## P3-04 — frontend danh sách đã tích hợp

Trang `/san-pham` gọi categories/products API thật qua Next server (INTERNAL_API_URL). URL frontend q/danh-muc/sort/page/page_size ánh xạ sang q/category_id/sort/page/page_size của API; page size UI chọn 12/24/48, nằm trong giới hạn 1..100 của backend. Category ID lấy từ active tree, ưu tiên slug unique rồi tên unique, không đoán khi tên trùng. Sửa filter/search/sort/size quay trang1; pagination giữ query. Không thêm API, đổi schema hoặc mở filter khoảng giá/sort tên chưa có trong contract. List không fallback mock; chỉ detail UI-01 vẫn preview có nhãn, chờ P3-05.


## Frontend P3-05 / UI-08

Chi tiết `/san-pham/{product_id}` lấy GET products/{id}; shop `/gian-hang/{shop_slug}` lấy GET shops/{slug} và products?shop_id={id}. Giữ BIGINT/Decimal string, ảnh HTTPS nullable, public projection, resource404 tách lỗi upstream. Giao diện UI-08 chỉ thay bố cục/link, không thêm endpoint hoặc đổi contract backend. Auth/cart/sale/ranking chưa tích hợp ở task này.


## P4-01 — Authentication đã triển khai

GET csrf, POST register/login/logout, GET me theo bảng thiết kế đã hoạt động trong backend. UserPrivate: user_id string,email,full_name,phone,user_role,user_status,owned_shop nullable {shop_id string,shop_status}. Register201 chưa login, login200 cookie không token JSON; logout204. Mã lỗi thêm401 INVALID_CREDENTIALS và503 AUTH_NOT_CONFIGURED khi thiếu khóa/origin. JWT TTL900s HS256, mandatory exp/iat/sub/iss/aud, max-TTL/BIGINT validation. Role/status từ DB hiện tại trên me, không role JWT. CSRF TTL3600s ký với session-cookie binding, exact Origin/Referer + cookie/header double-submit cho3 POST, login rotate CSRF. Logout expired JWT vẫn cho phép nếu CSRF hợp lệ; clear2 cookies không revoke copied JWT. Env secret blank vô hiệu auth; không hardcode. Frontend proxy/auth UI còn P4-03, policies P4-02 còn TODO. Hướng dẫn docs/auth-development.md.


## P4-02 — Policy và ownership

Không thêm endpoint nghiệp vụ. Auth/me dùng AccessPolicy chung; user role/status và owned shop đọc từ DB mỗi request. Policy thiếu/sai JWT hoặc missing user401; locked user403 USER_LOCKED; role/no-shop403 FORBIDDEN; shop không đủ quyền bán403 SHOP_NOT_APPROVED; owner sai/resource missing404 NOT_FOUND cùng response. Admin không bypass Buyer/Seller. Shop APPROVED được bán; LOCKED chỉ xử lý đơn cũ khi owner ACTIVE. Bộ guard được kiểm bằng test-only HTTP probes trên PostgreSQL riêng; probes không nằm trong production OpenAPI. Các API mutation sau phải dùng WriteAccess/JWT+CSRF/function-scope transaction cùng session với thao tác, không dùng GET guard làm bảo vệ duy nhất. Chi tiết docs/authorization.md. Dashboard/state transition/checkout chưa triển khai trong P4-02.


## P4-03 — Frontend auth đã nối

Browser gọi cùng-origin /api/v1/auth/{csrf,register,login,logout,me}, Next Route Handler forward tới backend cố định. Không thêm endpoint FastAPI hoặc đổi payload. Preserve cookie attributes/multiple Set-Cookie, auth cookies only, no Bearer bypass; unsafe requests cần public Origin/Referer và X-CSRF-Token, backend verify chữ ký. Frontend pages /dang-ky,/dang-nhap,/tai-khoan, đăng xuất header. Account từ me là dữ liệu riêng no-store; returnTo internal allowlist. Cấu hình/public activation hướng dẫn docs/auth-ui.md.

## P5-04 — lịch sử và chi tiết đơn Buyer đã triển khai

GET /api/v1/orders nhận page1..2147483647, page_size1..100 mặc định24, unknown query422; trả OrderSummary list theo created_at DESC/order_id DESC, quá cuối items rỗng và total đúng. GET /api/v1/orders/{id} trả OrderDetail snapshots dùng chung checkout; owned SQL predicate buyer_user_id từ JWT principal/user ACTIVE hiện tại, ADMIN không bypass. Foreign/missing404, guest401, user khóa403. READ ONLY/no-store, ID/Decimal string/UTC, list/detail query batch không N+1. Shop name hiện tại, product/price/address snapshot khi mua; không trả trạng thái tổng giả hoặc private order fields trong list. Next proxy chỉ GET với ID/query allowlist, invalid/duplicate query400; frontend /tai-khoan/don-hang dùng12 đơn/trang, detail /tai-khoan/don-hang/{id}. Hủy Buyer chưa triển khai trong P5-04, sẽ làm cùng state machine/hoàn tồn ở P6-05. Chi tiết [buyer-orders.md](buyer-orders.md).

## P6-01 — hồ sơ gian hàng Seller đã triển khai

POST/GET/PATCH /api/v1/seller/shop và frontend /kenh-nguoi-ban dùng API thật. GET chưa có shop404; POST luôn PENDING với owner từ principal, đã có shop409 SHOP_EXISTS, slug trùng409 SLUG_EXISTS; PATCH chỉ shop_name/description/contact_email, ít nhất một field, không null tên. Tên trim1..150; slug lowercase ASCII alnum chia bằng dấu gạch nối đơn1..160 và cố định sau đăng ký; description nullable tối đa5000; EmailStr nullable tối đa255. Unknown fields422. ShopPrivate IDs string/UTC/logo_url null, không logo_key; contact/owner private không đổi public projection. USER/ADMIN ACTIVE thao tác shop mình ở mọi status, không bypass Admin hoặc tự approve/resubmit/unlock. GET READ ONLY; writes CSRF/Origin, user→shop lock xuyên COMMIT, unique owner/slug có sẵn bảo vệ concurrent requests. POST/PATCH DB lỗi503 sanitized/rollback. Next proxy fixed path/method, không query, body32KiB cho seller; không đổi giới hạn8KiB route khác. Xem [seller-shop.md](seller-shop.md); catalog/tồn/đơn Seller/Admin chưa triển khai trong P6-01.

## P6-02 — Sản phẩm Seller đã triển khai

GET /seller/products nhận q,is_active,page,page_size; GET /seller/products/{id} đọc chi tiết riêng; POST tạo cùng inventory; PATCH chỉ sku/category_id/product_name/description/price; POST /seller/products/{id}/hide ẩn và lặp lại no-op. Tất cả yêu cầu ACTIVE owner/shop APPROVED, không Admin bypass ownership. SKU1–64/tên1–200 trim, description nullable≤5000, price Decimal string NUMERIC(14,2) không âm, initial_quantity integer0..2147483647; PATCH nonempty và chỉ description được null, extra fields422. SKU trùng409 SKU_EXISTS; category mới/đổi có ancestor inactive hoặc không nối root422 INVALID_CATEGORY. SellerProduct là ProductDetail thêm is_active/created_at/updated_at, ID/price string/UTC/URL ảnh null đến P6-03; không raw key/PII. READ ONLY list/detail; writes khóa user→shared category→shop→product tới COMMIT, atomic rollback product/inventory. Không reactivation hoặc thay tồn qua PATCH. Next proxy fixed routes/query/method/ID/32KiB/CSRF/Origin/no-store. Chi tiết [seller-products.md](seller-products.md).

## P6-03 — Image API code đã chuẩn bị, chưa xác minh bucket thật

Các POST upload-url/images, PATCH/DELETE images/{image_id} theo bảng Seller đã có code. MIME chỉ JPEG/PNG/WebP, size1..5MiB, ảnh tĩnh≤4096px mỗi chiều và≤16MP; presigned POST5 phút chính xác key/type/size, ký grant metadata riêng. Create chỉ nhận staging key đúng shop/product, xác minh object/ETag/bytes và ghi immutable final key trước transaction liên kết. Duplicate final key409 IMAGE_EXISTS, nội dung thay đổi409 IMAGE_CONFLICT, ảnh không hợp lệ422 INVALID_IMAGE; thiếu bucket503 STORAGE_NOT_CONFIGURED và image_upload_enabled=false trong Seller list. Delete204 chỉ reference; primary đổi nguyên tử. Public không raw key; URL từ key final đã xác minh, GET signed15 phút/CDN; không bucket giữ null. P6-03 IN_PROGRESS, real S3/CORS/IAM/delivery NOT RUN; xem [s3-images.md](s3-images.md).

## FIX-AUTH-02 — Nguồn request xác thực

CSRF chấp nhận exact MARKETPLACE_PUBLIC_ORIGIN cùng JSON list MARKETPLACE_ADDITIONAL_ORIGINS đã cấu hình cho cả frontend/backend. Compose local thêm http://localhost:3001 để dùng cùng LAN origin, không thay/xóa Origin header, không trust Host/Forwarded hoặc wildcard. Token/header/cookie/session binding giữ nguyên. Default Settings ngoài Compose vẫn additional_origins=[]; production aliases chỉ HTTPS. Hai host giữ cookie riêng. Xem [mobile-local.md](mobile-local.md).


## OTP — phần mở rộng chuẩn bị, chưa bật trên runtime

Xem [OTP setup](otp-setup.md). Chỉ EMAIL qua Brevo SMTP, không đổi 25 bảng. GET `/api/v1/auth/otp-options` trả `{enabled,email,sms:false}`, no-store. Mọi POST yêu cầu Origin/CSRF và không tự retry.

- POST `/auth/otp-request`: `{purpose:REGISTER|RESET_PASSWORD,channel:EMAIL,target:email}`. Không nhận mật khẩu/họ tên; SMS hoặc extra fields bị từ chối 422. Trả 202 `{data:{challenge_id,expires_in:60,resend_after:60}}`, không trả code/khẳng định email tồn tại.
- POST `/auth/otp-verify`: `{challenge_id,code}`. Không nhận new_password; chỉ xác minh email, chưa tạo user/chưa đổi mật khẩu. Trả `{data:{purpose,verification_token,expires_in:300}}` khi hợp lệ. Token 256 bit một lần, private/no-store, chỉ trong memory form, không URL/browser storage. Mã sai/hết hạn không cấp token.
- POST `/auth/otp-register`: `{verification_token,full_name,password}`. Chỉ chấp nhận token REGISTER; trả `{data:{purpose:REGISTER,user}}`. Server cố định role USER; email lấy từ proof, không nhận email/role từ client.
- POST `/auth/password-reset`: `{verification_token,new_password}`. Chỉ chấp nhận token RESET_PASSWORD, còn hạn và chưa dùng; kiểm lại ACTIVE/email/password credential stamp trong transaction rồi cập nhật Argon2id và xóa cookie trình duyệt. Trả `{data:{purpose:RESET_PASSWORD}}`. JWT mang stamp cũ mất quyền; không mở khóa account.
- `/auth/login` dùng email; `/auth/otp-login` alias identifier chỉ email. Khi OTP bật, legacy `/register` bị chặn 403 OTP_REQUIRED.

Email vẫn NOT NULL; Redis giữ OTP 60s/rate 1h/proof 300s. Consume proof trước SQL mutation để ngăn replay, lỗi DB có thể làm mất proof. OTP_INVALID400/RATE_LIMITED429/OTP_NOT_CONFIGURED hoặc OTP_UNAVAILABLE503. Phải cấu hình SMTP/Redis đúng; không chạy SQL OTP cũ đã rút lại.
