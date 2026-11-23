# Terraform dev

## Bước hiện tại: chuẩn bị S3 ảnh, chưa triển khai web

Thực hiện từng bước trên môi trường dev hiện có. Agent chỉ chuẩn bị mã hạ tầng;
người dùng tự chạy lệnh. Chưa chạy Terraform, chưa gọi AWS CLI, chưa tạo tài nguyên,
chưa sửa database hoặc sao chép/xóa ảnh. Các giá trị region trong mã và cấu hình
đã được đồng bộ về `ap-southeast-1` (Singapore) theo yêu cầu; tên bucket ảnh ứng dụng giữ nguyên.

Ứng dụng local cấu hình bucket `coco-marketplace`; thông tin trước đây ghi nhận bucket ở
`us-east-1`, cần kiểm tra lại region thực tế trước khi dùng. Terraform dev và cấu hình
ứng dụng hiện mặc định `ap-southeast-1`, đặt tên bucket Terraform riêng theo
project/environment/account. Việc đổi region trong cấu hình không di chuyển bucket
hoặc tài nguyên AWS đã tồn tại. Không sửa state hoặc
import bucket chỉ để làm các tên trùng nhau. Trước khi lên plan cần xác nhận bucket
hiện hữu được quản lý bởi state nào và ảnh nào đang được DB tham chiếu.

Phần đã chuẩn bị trong module dùng chung:

- Bucket ảnh vẫn private, chặn public access, dùng mã hóa SSE-S3 và versioning.
- CORS cho presigned POST chỉ nhận origin được liệt kê ở `image_upload_origins`.
  Mặc định dev là `http://localhost:3001`; thêm domain HTTPS dev khi có domain thật.
  CORS không cấp quyền upload. Backend vẫn cần IAM role có quyền tương ứng.
- CloudFront OAC chỉ được đọc `product-images/*` và `shop-logos/*` của bucket ảnh,
  giới hạn theo ARN distribution. Không cấp quyền đọc `uploads/*` cho CDN.
- Bucket policy yêu cầu HTTPS với client thông thường; CDN có security headers.
- Các prefix là quy ước key, không tạo folder/object hoặc thay dữ liệu sẵn có.

Quy ước key cho bước web sau này:

| Loại | Key |
| --- | --- |
| Sản phẩm đang chờ xác minh | `uploads/{shop_id}/{product_id}/{uuid}.{ext}` |
| Sản phẩm đã xác minh | `product-images/{shop_id}/{product_id}/{uuid}.{ext}` |
| Logo đang chờ xác minh | `uploads/shop-logos/{shop_id}/{uuid}.{ext}` |
| Logo đã xác minh | `shop-logos/{shop_id}/{uuid}.{ext}` |

Luồng upload sản phẩm hiện có dùng prefix tương ứng ở trên. **Upload logo qua API
chưa được triển khai**; logo import hiện đã có luồng ký URL để đọc key sẵn có.
Không thay `shops.logo_key` hoặc `product_images.image_key` trong database ở bước này.
Ảnh legacy ở các prefix cũ tiếp tục theo cấu hình hiện tại; không tự chuyển chúng
sang CDN mới hoặc công khai thêm prefix để tránh mất ảnh.

### 1. Người dùng kiểm tra account và bucket đang dùng, chỉ đọc

Chạy từ gốc repo bằng profile AWS phù hợp:

```sh
aws sts get-caller-identity
aws s3api head-bucket --bucket coco-marketplace --region ap-southeast-1
aws s3api get-bucket-location --bucket coco-marketplace
aws s3api get-bucket-versioning --bucket coco-marketplace
aws s3api get-public-access-block --bucket coco-marketplace
aws s3api get-bucket-cors --bucket coco-marketplace
aws s3api get-bucket-policy --bucket coco-marketplace --query Policy --output text
terraform -chdir=terraform/environments/dev state list
```

AWS khuyến nghị HeadBucket để phát hiện region; GetBucketLocation là bước đối chiếu
tương thích: `ap-southeast-1` là Singapore; `LocationConstraint: null` vẫn có nghĩa
là bucket ở `us-east-1`, không phải Singapore. Nếu bucket vẫn ở region cũ, cần giữ
region S3 riêng đúng với bucket hoặc lập kế hoạch chuyển ảnh riêng; chưa tự sao chép ảnh
hay đổi tham chiếu trong DB.
Nếu chưa có CORS,
lệnh CORS có thể trả `NoSuchCORSConfiguration`; ghi nhận kết quả để xử lý sau.
Nếu chưa có state/credentials thì dừng ở thông báo đó; không tự tạo state khác,
không import bucket hoặc apply toàn bộ môi trường. Chỉ gửi lại kết quả cần thiết;
không gửi access key, secret key, session token hoặc mật khẩu.

### 2. Người dùng kiểm tra mã Terraform, chưa tạo tài nguyên AWS

```sh
terraform version
terraform -chdir=terraform/environments/dev init -backend=false
terraform -chdir=terraform/environments/dev validate
terraform fmt -check -recursive terraform
terraform -chdir=terraform/environments/dev test -filter=tests/images.tftest.hcl
```

`init` tải provider/module và ghi cache/lock cục bộ. Bộ test yêu cầu Terraform >=1.7,
dùng mock provider, không kết nối DB hoặc tạo tài nguyên AWS. Agent chưa chạy các
kiểm tra này; cần kết quả thực tế trước khi nói cấu hình đã được xác minh.

Các module storage/cloudfront là module dùng chung nên trước khi triển khai cuối
cùng còn cần kiểm tra cả môi trường prod. Chưa apply dev/prod ở bước này.

### 3. Chuẩn bị quyền runtime S3 sau khi biết bucket và state đúng

Đã chuẩn bị policy upload ảnh giới hạn bucket/prefix từ baseline Autopilot do chủ
dự án cung cấp; xem [IAM image policy](../../modules/iam/README.md). Chưa gắn policy
hoặc đổi role trên AWS thay người dùng. Dev chủ động dùng shared worker role,
không phải quyền riêng theo Pod. Không đưa access key vào image. Quyền Terraform
triển khai và quyền backend upload là hai loại khác nhau.

Sinh baseline quyền từ mã boto3 bằng IAM Policy Autopilot, để người dùng tự chạy.
Kiểm tra công cụ trước; nếu `uvx` chưa có, cần cài uv theo môi trường của người dùng.

```sh
uvx iam-policy-autopilot@latest --version
uvx iam-policy-autopilot@latest generate-policies --help
```

Ví dụ cho vị trí workspace hiện tại, chỉ phân tích luồng ảnh S3:

```sh
uvx iam-policy-autopilot@latest generate-policies \
  /home/ngocdien2006/projects/github/Auto_scaling_E-commerce_Platform_with_Data_Pipeline_on_AWS/backend/app/services/storage.py \
  --tf-dir /home/ngocdien2006/projects/github/Auto_scaling_E-commerce_Platform_with_Data_Pipeline_on_AWS/terraform/environments/dev \
  --region ap-southeast-1 \
  --service-hints s3 \
  --pretty
```

Nếu đường dẫn máy khác thì thay bằng đường dẫn tuyệt đối thực tế. Bổ sung
`--account` bằng account ID đã xác nhận ở bước 1. Không dùng `--upload-policies`.
Baseline phải được xem lại ARN/prefix và giới hạn quyền trước khi gắn vào role;
đây chưa phải policy đã duyệt hoặc đã được áp dụng. Khi bước logo có mã boto3,
cần sinh/đối chiếu lại baseline trước khi cập nhật quyền.

Nên bật access logs, CloudTrail S3 data events và theo dõi CloudWatch khi vận hành;
nơi nhận log phải mã hóa và hạn chế người đọc. Bước này chưa tạo thêm hệ thống log.
S3 tính phí lưu trữ, request và truyền dữ liệu; versioning lưu thêm bản cũ, CDN
và các loại log cũng có thể phát sinh phí. Chưa có dự toán khi chưa biết dung lượng
và lưu lượng. Tham khảo [S3 pricing](https://aws.amazon.com/s3/pricing/),
[CloudFront pricing](https://aws.amazon.com/cloudfront/pricing/).

**Điểm dừng:** gửi kết quả inventory và kiểm tra mã trước. Sau đó mới chốt kế hoạch
quản lý bucket cũ/mới và quyền runtime, rồi xem plan giới hạn đúng tài nguyên ảnh.
Không chạy phần apply toàn bộ môi trường bên dưới trong bước kiểm tra S3 này.

Tham khảo: [S3 CORS](https://docs.aws.amazon.com/AmazonS3/latest/userguide/enabling-cors-examples.html),
[CloudFront OAC](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html),
[S3 HTTPS policy](https://docs.aws.amazon.com/AmazonS3/latest/userguide/amazon-s3-policy-keys.html),
[IAM Policy Autopilot](https://github.com/awslabs/iam-policy-autopilot).

## Quy trình toàn bộ môi trường — thực hiện ở các bước sau

Chạy các lệnh dưới đây từ **gốc repo**. Xem [hướng dẫn chung](../../README.md) trước khi triển khai.

Region mặc định `ap-southeast-1`. ALB dev dùng HTTP; RDS Single-AZ. Môi trường này có chi phí ngay khi tài nguyên bắt đầu được tạo.

Nếu chưa có `terraform/environments/dev/terraform.tfvars`, sao chép `terraform.tfvars.example` cùng thư mục và chỉnh giá trị. Không ghi đè file biến hiện có.

```sh
aws sts get-caller-identity
terraform -chdir=terraform/environments/dev init
terraform -chdir=terraform/environments/dev validate
terraform -chdir=terraform/environments/dev plan -out=dev.tfplan
terraform -chdir=terraform/environments/dev show dev.tfplan
```

Chỉ khi plan đúng với ý định của bạn, chạy bước tạo/cập nhật tài nguyên AWS có phí:

```sh
terraform -chdir=terraform/environments/dev apply dev.tfplan
terraform -chdir=terraform/environments/dev output
```

Cấu hình Kubernetes: 1 control plane + 2 worker `t3.medium` ban đầu; worker min 2/max 4. RDS `db.t4g.small`. Xem [quy trình autoscaling dev](../../../k8s/autoscaling/RUNBOOK-dev.md) để cài role/controller và kiểm tra bootstrap mà không full apply lên cluster hiện hữu.

Output có `rds_endpoint`, `rds_database_name`, `rds_master_secret_arn`, `etl_bucket_name`, `alb_dns_name` và hai ECR URL.

Kiểm tra offline sau khi init:

```sh
terraform -chdir=terraform/environments/dev test
```

Test dùng mock provider, cần Terraform >= 1.7. Bước tiếp theo: [Kubernetes](../../../k8s/README.md) và [ETL](../../../etl/README.md). Giữ file state của môi trường này riêng biệt.
