# P6-03 — Chuẩn bị ảnh S3

**Cấu hình hiện tại:** chỉ dùng `.env` ở thư mục gốc; xem [hướng dẫn gộp env và Docker release](docker-release.md). Các tên env theo service trong phần lịch sử không còn được Compose đọc.

Ngày 10/11/2026. Người dùng xác nhận **chưa có bucket**, yêu cầu chuẩn bị code và hướng dẫn cấu hình. Code/API/UI và kiểm thử cục bộ đã được bổ sung; P6-03 vẫn **IN_PROGRESS** tới khi cấu hình và kiểm thử bucket/CORS/IAM thật. Không tạo bucket, không upload AWS, không thêm MinIO, không sửa dữ liệu nghiệp vụ.

## Luồng đã chuẩn bị

1. Seller ACTIVE sở hữu shop APPROVED mở **Sản phẩm của tôi → Quản lý ảnh**. Backend kiểm quyền theo product/shop hiện tại; Admin không bỏ qua ownership.
2. POST `/api/v1/seller/products/{id}/images/upload-url` với `content_type`, `size_bytes` cấp presigned POST5 phút: key ngẫu nhiên trong `uploads/{shop}/{product}/`, Content-Type chính xác và content-length-range bằng kích thước khai báo. Chấp nhận JPEG/PNG/WebP,1 byte–5MiB. Grant ký riêng bằng khóa dẫn xuất từ JWT secret, không dùng access token làm upload grant. Chính sách POST dựa trên [Boto3 generate_presigned_post](https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/generate_presigned_post.html).
3. Browser gửi multipart trực tiếp tới storage HTTPS bằng `credentials: omit`, không cookie/JWT/CSRF của ứng dụng. Không đưa AWS access key/secret vào client bundle hoặc localStorage. Các trường ký tạm chỉ nằm trong bộ nhớ phiên upload.
4. POST `/images` với image_key staging,is_primary?,sort_order? kiểm prefix đúng shop/product, HEAD MIME/size/grant/expiry, đọc có điều kiện ETag và tối đa5MiB+1. Pillow verify/decode kiểm nội dung thật, định dạng, ảnh tĩnh, mỗi chiều≤4096px và tổng≤16 triệu pixel. Không nhận SVG/HTML hoặc tin filename/MIME client.
5. Server ghi byte đã xác minh vào key riêng `product-images/{shop}/{product}/{uuid}.{ext}` với If-None-Match:*; URL upload chỉ cho phép key staging, không ghi đè ảnh đã liên kết. Nếu final object đã tồn tại, SHA256 phải giống trước khi tiếp tục. Hành vi conditional GET/PUT theo [GetObject](https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/get_object.html) và [PutObject](https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/put_object.html); provider tương thích S3 phải hỗ trợ các điều kiện này, không fallback sang ghi đè.
6. Transaction DB lưu key, không lưu file. PATCH `/images/{image_id}` chỉ is_primary/sort_order; DELETE bỏ reference và trả204, không xóa object. Key/id shop khác không được liên kết hoặc sửa. Đổi primary serialize qua user→shared category→shop→product, unset/flush/set cùng COMMIT và partial unique index hiện hữu; rollback phục hồi primary cũ.

Public list/detail, Seller detail/list và cart sinh URL từ key đã xác minh, không trả raw key trong public response. Primary URL chọn primary trước rồi sort_order/image ID; khi không có primary dùng ảnh đầu còn lại. Seller image mutation response riêng có image_key theo contract. URL mặc định là presigned GET15 phút hoặc HTTPS CDN base được cấu hình. Không cấu hình bucket thì URL null, không truy tìm credential/khởi tạo SDK client; list Seller trả `image_upload_enabled:false`, upload503 STORAGE_NOT_CONFIGURED và UI disabled kèm giải thích thật. Shop logo upload/delivery vẫn ngoài luồng sản phẩm này.

## Cấu hình khi đã có storage

Cập nhật đường dẫn 15/11/2026: catalog import còn hỗ trợ `ProductImages/{shop}/{product_id}/{product_id}_{index}.jpg` với đúng ba tên shop đã nêu dưới đây, bên cạnh bố cục cũ `{shop}/product_image/...`. Key DB phải khớp chính xác S3 (phân biệt hoa/thường, giữ dấu cách), không lưu URL đầy đủ hoặc tự đổi khoảng trắng thành dấu+. Delivery ký GET trực tiếp; thay đường dẫn trong S3 cần cập nhật reference tương ứng bằng quy trình dữ liệu riêng. API upload/finalize mới không nhận key import.

Cập nhật 15/11/2026: delivery hỗ trợ thêm các reference ảnh catalog cũ thuộc ba thư mục `1-Lumi Beauty`, `2-Miora Lifestyle`, `3-Nuvia Care Store`, theo dạng `product_image/{id}/{id}_{index}.jpg`. Chỉ cấp presigned GET15 phút cho key đã lưu trong DB; giữ nguyên dấu cách trong key. CDN base chỉ dùng cho ảnh `product-images/` mới. Luồng upload/finalize không nhận key cũ và vẫn kiểm tra nội dung như trên. Không cần đổi DB hoặc công khai bucket. Đã kiểm ảnh mẫu và homepage local, chưa kiểm hết objects hoặc luồng upload S3 thật.

Đặt cấu hình storage trong `.env` gốc. Backend đọc file này; PostgreSQL và frontend không dùng env_file nên không nhận khóa S3/Brevo/JWT. File private bị Git/Docker build context bỏ qua. Template không chứa secret tại [storage.env.example](../.env.example).

```powershell
Copy-Item .env.example .env
```

Chỉ chạy lệnh copy khi file private chưa tồn tại; nếu đã có thì sửa các trường cần thiết, không ghi đè cấu hình cũ. Cấu hình riêng trong file:

| Biến | Giá trị |
| --- | --- |
| MARKETPLACE_S3_BUCKET | Bucket dành riêng cho dự án, do chủ dự án cung cấp |
| MARKETPLACE_S3_REGION | Region đúng của bucket, mặc định ap-southeast-1 |
| MARKETPLACE_S3_ENDPOINT_URL | Để trống cho AWS S3; provider khác dùng HTTPS endpoint có thể truy cập từ backend và browser |
| MARKETPLACE_S3_PATH_STYLE | false mặc định; chỉ true nếu provider yêu cầu |
| MARKETPLACE_S3_PUBLIC_BASE_URL | Tùy chọn HTTPS CDN base phục vụ product-images/; trống dùng private presigned GET |

Boto3 dùng credential chain chuẩn. Ưu tiên IAM workload role khi triển khai; máy local có thể đặt AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY/AWS_SESSION_TOKEN riêng trong .env. Không gửi credential qua chat, đưa lên Git hoặc NEXT_PUBLIC_*. Auth JWT secret hiện có là điều kiện cần cho grant ký riêng; không thay auth secret chỉ để bật storage.

Chủ bucket cấu hình tối thiểu IAM/CORS sau; đây là mẫu tham khảo, **chưa được áp dụng**. Thay YOUR_BUCKET bằng bucket thật. Không cần quyền CreateBucket, DeleteObject, ListAllMyBuckets hoặc ACL public-read cho luồng này.

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:PutObject"],
    "Resource": [
      "arn:aws:s3:::YOUR_BUCKET/uploads/*",
      "arn:aws:s3:::YOUR_BUCKET/product-images/*"
    ]
  }]
}
```

Mẫu bucket CORS cho local hiện tại (chỉnh origin nếu IP thay đổi):

```json
[{
  "AllowedOrigins": ["http://localhost:3001", "http://192.168.110.101:3001"],
  "AllowedMethods": ["POST", "GET", "HEAD"],
  "AllowedHeaders": ["*"],
  "ExposeHeaders": ["ETag"],
  "MaxAgeSeconds": 300
}]
```

Giữ bucket private/Block Public Access khi dùng presigned GET. Nếu dùng CDN, chỉ phân phối product-images/, không phân phối uploads/. Upload staging và orphan sau DB rollback hiện được giữ, không có worker/lifecycle/delete tự động trong task này; cleanup cần quyết định và task riêng. Không đưa test fixtures vào bucket nghiệp vụ.

Sau khi tự cấu hình storage đúng, cập nhật riêng app và giữ LAN origin:

```powershell
$env:MARKETPLACE_PUBLIC_ORIGIN='http://192.168.110.101:3001'
docker compose build backend frontend
docker compose up -d --no-deps --wait backend frontend
```

## Kiểm chứng và phần còn chờ

- PASS315 backend tests với PostgreSQL16 tmpfs marketplace_test riêng và audit metadata hiện hữu READ ONLY. Thêm21 SDK/validation tests và7 integration tests: exact POST policy, PNG thật/metadata giả/expired grant/cross-key, missing config, SDK lỗi sanitized, ownership/status/CSRF, primary race hai app, rollback COMMIT và delete chỉ reference.
- PASS52 frontend tests (4 nhóm ảnh mới), lint/typecheck/production build. Client kiểm projection/URL HTTPS/ID, Origin/CSRF proxy, file/MIME/size, upload không credential và không tự retry write khi mất phản hồi.
- SDK double MemoryS3 chỉ phục vụ test; không phải bằng chứng AWS/S3-compatible integration. Real bucket upload/HEAD/GET/conditional PUT/presigned delivery/CORS/IAM/expiry và CDN chưa chạy. Không đánh dấu P6-03 DONE khi các checks này chưa có.

Trong môi trường storage riêng được chủ dự án chỉ định, cần chạy thêm: JPEG/PNG/WebP lên→liên kết→xem public/cart→đổi primary/sort→bỏ reference; MIME giả/quá5MiB/ảnh động/kích thước lớn; grant hết hạn/cross-shop key; hai primary requests; mất response sau object PUT/DB COMMIT→đọc lại; conditional write đúng; CORS qua localhost/LAN; SDK403/timeout; URL GET hết15 phút và tải lại nhận URL mới. Không chỉ HTTP smoke rồi gọi là kiểm thử S3 thật.

Giới hạn delivery: ẩn sản phẩm hoặc bỏ reference ngăn API cấp URL mới, nhưng URL GET đã ký còn dùng được tới hạn15 phút; không hứa thu hồi tức thì ảnh đã tải hoặc URL đã cấp. CDN có chính sách cache/quyền riêng cần kiểm riêng. S3 network calls trong finalize hiện có timeout/retry giới hạn và chạy khi giữ khóa transaction; latency/load trên storage thật chưa đo.
