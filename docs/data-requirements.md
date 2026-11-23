# Dữ liệu cần chuẩn bị cho Marketplace

Website vẫn tiếp tục được xây dựng khi database chưa có dữ liệu. APIs trả danh sách rỗng hoặc 404 phù hợp, giao diện dùng empty state thật. Có schema không có nghĩa đã có danh mục/sản phẩm; tài liệu này không khẳng định số hàng hiện tại vì lần này không truy vấn DB.

Schema mới có25bảng, nhưng không cần điền sẵn tất cả. Cần chuẩn bị catalog và thông tin shop trước; giỏ/địa chỉ/đơn được tạo qua chức năng web. Các bảng history/audit/coupon/review/payment/shipping không được tự bịa dữ liệu hoặc coi là đã có API chỉ vì bảng tồn tại. Tài liệu này chưa cấp quyền import hoặc seed. Xem [schema25/CRUD/k6](schema25-crud-k6.md).

## Bộ thông tin tối thiểu

| Nhóm | Bạn chuẩn bị | Website sử dụng |
| --- | --- | --- |
| Danh mục | Tên, slug hoặc mã tham chiếu, danh mục cha nếu có | categories; cây không chu kỳ |
| Người bán và shop | Tên shop, slug, mô tả, email liên hệ nếu muốn, tham chiếu người sở hữu | users rồi shops; một owner tối đa một shop |
| Sản phẩm | Tên, SKU, tham chiếu shop/danh mục, mô tả, giá VND | products; SKU unique trong shop |
| Tồn kho | Số lượng nguyên không âm cho từng SKU/shop | inventory; tạo cùng transaction với product |
| Ảnh sản phẩm | File JPEG/PNG/WebP có quyền dùng; SKU/shop liên quan, ảnh chính/thứ tự | Upload S3 sau khi có storage, product_images chỉ giữ key |

Giá/tồn cần có nguồn hoặc do bạn xác định cho môi trường demo, không suy ra từ review. Giá dùng chuỗi decimal tối đa 2 chữ số thập phân, không dấu phân cách hàng nghìn/ký hiệu tiền tệ trong dữ liệu nhập. Không gửi mật khẩu người bán/Admin qua chat hoặc ghi vào bảng dữ liệu.

## Cần bao nhiêu để kiểm tra luồng

Đây là gợi ý phục vụ kiểm tra, không phải giới hạn hệ thống:

- Để hiển thị catalog: một danh mục active, một shop APPROVED, một product active và inventory là đủ.
- Để demo marketplace nhiều shop: khoảng 3–5 danh mục, ít nhất 2 shop thuộc 2 owner khác nhau, 10–20 sản phẩm có giá/tồn được xác định và ảnh nếu có.
- Để thử checkout nhiều shop: ít nhất 1 sản phẩm còn tồn ở mỗi shop, cùng một Buyer độc lập không sở hữu hai shop đó; địa chỉ do Buyer nhập qua giao diện sau này.
- Có thể xây API/UI trước khi có ảnh. Khi chưa có object storage, dùng placeholder ảnh ở UI; không tạo URL ảnh giả hoặc ghi key tùy ý vào DB.

## Các trường có thể chuẩn bị trong bảng tính hoặc JSON

Không cần tự điền ID database; IDs identity được PostgreSQL sinh. Các mã tham chiếu sau chỉ là đầu vào mapping, không thêm cột vào schema.

| Tập thông tin | Trường chuẩn bị | Ghi chú |
| --- | --- | --- |
| Danh mục | category_ref, category_name, category_slug, parent_ref | parent_ref rỗng cho root; slug unique |
| Shop | shop_ref, owner_ref, shop_name, shop_slug, description, contact_email | owner_ref liên kết quy trình tạo tài khoản hợp lệ; không password/plaintext hash tự bịa |
| Sản phẩm | shop_ref, category_ref, sku, product_name, description, price_vnd, quantity | Cặp shop_ref/sku unique, quantity nguyên không âm |
| Ảnh | shop_ref, sku, file_name, is_primary, sort_order | Tối đa một primary; filename không phải S3 key đã upload |

Có thể bắt đầu chỉ bằng tên shop, danh mục và danh sách sản phẩm/giá/tồn bạn muốn bán. Tôi sẽ chuyển thành mapping có kiểm tra khi bạn yêu cầu task dữ liệu riêng. Không tự tạo schema, reset DB hoặc chạy file SQL khởi tạo để nhập catalog.

## Dữ liệu ứng dụng tự tạo sau này

| Bảng | Được tạo bởi |
| --- | --- |
| users | Đăng ký/login workflow hoặc bootstrap Admin được yêu cầu riêng; hash mật khẩu tại backend |
| shops | Seller đăng ký, Admin duyệt; bản đầu chưa có các API này |
| addresses | Buyer nhập địa chỉ giao hàng; không cần thu thập trước |
| carts, cart_items | Buyer thêm/sửa giỏ |
| orders, shop_orders, order_items | Checkout thật qua API sau khi chức năng hoàn thành; không tạo sẵn đơn giả |

Tài khoản Admin ban đầu cần quy trình bootstrap riêng khi triển khai auth; không endpoint công khai tự cấp ADMIN. Hiện chưa có registration/Seller/Admin APIs để sử dụng ngay; không hướng dẫn gọi endpoint chưa tồn tại.

## Ảnh S3 còn thiếu gì

Trước task storage cần xác định bucket, region và endpoint nếu dùng S3-compatible local; cách cung cấp credentials qua env/provider; quyền upload/read và public origin truy cập ảnh. Không cần gửi access key/secret key trong chat hoặc tài liệu dự án.

Nếu chưa có AWS/S3, có thể yêu cầu task MinIO local riêng. Không tự thêm storage service vào Compose hoặc dùng MinIO của dự án khác. S3 bucket/credential cụ thể không phải điều kiện để tiếp tục API sản phẩm và UI trạng thái rỗng.

## Nếu chưa có dữ liệu thật

Có hai hướng: tiếp tục code và hiển thị trạng thái rỗng, hoặc chuẩn bị bộ dữ liệu demo được ghi nhãn rõ, chỉ đưa vào local/test sau khi bạn chỉ định task nhập dữ liệu. Không tạo mock response trong production hoặc tự seed vào database đang giữ dữ liệu.

Dữ liệu HealthBeauty đã xem ở workspace khác là dữ liệu review: tên/ID/ảnh có thể tham khảo sau khi kiểm tra quyền sử dụng, nhưng thiếu giá/tồn/SKU/owner hợp lệ; không biến người viết review thành tài khoản thật và không import trực tiếp.

Task nhập dữ liệu khi được yêu cầu cần: xác nhận môi trường đích, nguồn/giá/tồn/ownership, dry-run báo thiếu/trùng/mapping, xác nhận kế hoạch ghi rồi transaction có kiểm soát. Không có quyền truncate/drop, không ghi đè dữ liệu cũ hoặc bỏ qua constraints để import. File SQL Downloads có lệnh DROP nên không dùng làm importer.
# Cập nhật UI-01: xây giao diện trước

Theo yêu cầu mới, frontend hiện dùng taxonomy local gồm đúng `ChamSocDaMat`, `TrangDiem`, `DungCuPhuKienLamDep`, `VatTuYTe`, `DungCuMassageTriLieu`, `NuocHoa`. Mỗi danh mục có 2 sản phẩm minh họa để kiểm tra bố cục, tìm kiếm, lọc và trang chi tiết. Banner/footer ghi rõ bản xem trước, giá/nhãn hiệu/bao bì không phải dữ liệu bán hàng thực; không có nút đặt hàng giả. Không kết nối frontend với API hoặc ghi database trong UI-01.

Danh sách trên chỉ xác định phạm vi website, không khẳng định các category ID 1–6 đã tồn tại trong PostgreSQL. Khi tích hợp dữ liệu sau này, cần đối chiếu mapping với DB hiện hữu; không tự tạo lại schema, seed hoặc ghi đè ID. Các yêu cầu dữ liệu thực bên dưới vẫn áp dụng cho giai đoạn tích hợp.

## Cập nhật P3-03: homepage đã lấy API thật

Trang `/` không dùng mẫu UI-01 nữa. Sáu ô danh mục là taxonomy hiển thị, được đối chiếu tên/slug với cây active từ API để lấy ID thật. Chưa có danh mục tương ứng thì ô hiển thị “Sắp cập nhật”; chưa có sản phẩm public thì hiển thị trạng thái rỗng. Không ghi hoặc tự tạo dữ liệu để lấp grid. Các trang `/san-pham` vẫn preview có banner riêng, chờ task P3-04/05. Hướng dẫn API/terminal trong frontend/README.md.

## Cập nhật P3-04

`/san-pham` cũng đã dùng API thật; chỉ `/san-pham/[slug]` còn preview chờ P3-05. Catalog có thể hiển thị rỗng khi không có sản phẩm public, danh mục chưa có mapping hiển thị chưa sẵn sàng; không tự seed để thử phân trang. Kịch bản nhiều sản phẩm được kiểm tra bằng fixture HTTP server riêng, không ghi PostgreSQL. Ảnh thật của UI-04 vẫn cần nguồn/mapping người dùng cung cấp; không lấy ảnh campaign AI làm ảnh catalog.



## Trạng thái P3-05 / UI-08

Homepage/list/detail/shop đều dùng API thật; không còn preview route hoặc ảnh mẫu sản phẩm production. 6 mục điều hướng dùng taxonomy đã chốt, lấy ID từ API; không thêm danh mục trong ảnh tham khảo. Banner SVG là minh họa mua sắm. Public catalog hiện rỗng; không giả sale/countdown/ranking. UI-04 vẫn chờ nguồn ảnh thật và mapping sản phẩm/S3. Các mô tả preview ở mục lịch sử phía trên phản ánh thời điểm task cũ, được thay thế bởi cập nhật này.
