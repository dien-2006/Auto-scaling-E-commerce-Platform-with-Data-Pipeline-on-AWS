# Chạy web dev từ local lên EC2/Kubernetes qua SSM

Tất cả lệnh trong hướng dẫn này chạy **trên máy local, tại gốc repo**. Không cần
kubeconfig admin trên local hoặc mở cổng Kubernetes API public. Script gửi task qua
SSM đến đúng worker/control plane theo tag và region `ap-southeast-1`.
Các tệp đã được chuẩn bị bằng cách đọc mã; agent chưa chạy kiểm tra/build/deploy.
Không coi đây là kết quả triển khai đã được xác minh.

## Điều kiện trước khi triển khai

- Account `858525799322`, đúng state dev hiện hữu; control plane và hai worker Ready,
  Flannel/CoreDNS khỏe. Không destroy hạ tầng đang chạy để áp dụng các bước này.
- Local có Bash, Python 3, Node.js 24, uv, Terraform >=1.7, kubectl, AWS CLI và Docker.
- Credential deploy được phép ECR push, SSM SendCommand/PutParameter, đọc RDS master
  secret và sử dụng key KMS của deployment. Không gửi credential/mật khẩu vào chat.
- **RDS đích phải có schema/bảng tương thích do chủ dự án chuẩn bị thủ công.** RDS mới
  không tự chứa dữ liệu DB local. Hướng dẫn không chạy SQL, migration, seed hoặc restore.
  Nếu chưa chuẩn bị bảng, dừng trước bước deploy; đừng tự tạo bảng để chữa readiness.
- `.env` local có các trường SMTP thật `MARKETPLACE_SMTP_HOST`,
  `MARKETPLACE_SMTP_USERNAME`, `MARKETPLACE_SMTP_PASSWORD`, `MARKETPLACE_OTP_FROM_EMAIL`;
  tùy chọn PORT/SECURITY. Không thay `.env` đang dùng để trỏ DB local sang AWS.
- Đây là **dev HTTP**, backend chạy chế độ `local` hợp lệ và origin lấy từ ALB.
  Production cần domain/ACM/HTTPS và cấu hình riêng, không dùng nguyên quy trình này.
- Deployment mới quản lý image/config bằng bản render từ output thật; không apply trực
  tiếp overlay còn `ACCOUNT_ID`/`REPLACE_*`. S3 ảnh cũ phải có key đúng DB, giữ nguyên
  `ProductImages/...` và `logo/...`. Logo được ký GET, không cập nhật key hoặc row DB.

## 1. Chạy kiểm tra cục bộ trước khi build

```sh
bash scripts/check-release.sh
```

Script chạy unit test không DB, kiểm tra frontend, Terraform mock test và shell syntax.
Không gọi AWS, build Docker hoặc chạy bài test PostgreSQL có tạo schema. Có lỗi thì
dừng, sửa đúng lỗi rồi chạy lại phần liên quan; không bỏ qua để tiếp tục deploy.

## 2. Xem plan sửa hạ tầng web hiện hữu

```sh
bash scripts/aws/plan-web-dev.sh
```

Plan giới hạn sửa routing ALB → Next.js, S3 CORS/quyền ảnh, target của hai alarm web
và key mã hóa Secret dev.
Việc target nhằm sửa môi trường hiện hữu, không phải quy trình apply định kỳ toàn bộ.
Review mọi dependency; dừng nếu có thay đổi RDS, xóa tài nguyên hoặc thay thế EC2.
Plan có thể thêm key/alias KMS và policy; **key KMS có phí AWS**. Không tạo bảng DB.
CloudFront chỉ đọc prefix ảnh mới; ảnh import dùng presigned GET qua backend.

Chỉ sau khi đã chấp nhận plan, tự chạy lệnh áp dụng saved plan (không hỏi lại `yes`):

```sh
terraform -chdir=terraform/environments/dev apply web-dev.tfplan
```

Không apply `dev.tfplan` cũ hoặc apply toàn bộ dev chỉ để sửa web: còn các thay đổi
bootstrap/AMI chưa đối chiếu với máy hiện hữu. Targeted plan không cập nhật tất cả
thay đổi hạ tầng. CORS dev tự thêm origin ALB, không thêm trùng URL ALB vào tfvars.
Đổi health check frontend sang `/health/live` cần image mới; target có thể tạm
unhealthy cho đến khi rollout image mới xong.

## 3. Build và push hai image lên ECR

```sh
COCO_IMAGE_TAG="dev-$(date -u +%Y%m%d%H%M%S)"
bash scripts/aws/build-push-dev.sh "$COCO_IMAGE_TAG"
```

Script build `linux/amd64`, đăng nhập ECR bằng credential tạm, push rồi đọc digest xác
nhận. Hai repository lấy từ Terraform output, không hardcode `ACCOUNT_ID`.
Push chọn rõ `--platform linux/amd64` (Docker API >=1.46) để chỉ xuất manifest chạy
trên worker hiện tại, không đẩy image index/attestation. Điều này tránh luồng push
nhiều manifest vào cùng tag immutable trên Docker dùng containerd image store.
ECR immutable: mỗi bản sửa dùng tag mới, không dùng lại tag đã push một phần.
Giữ giá trị `COCO_IMAGE_TAG` cho bước kế tiếp; đổi terminal phải đặt lại đúng tag đó.

Nếu đã build đủ hai image nhưng push lỗi manifest, có thể giữ bản build local,
đổi sang tag mới và push riêng platform thay vì build lại:

```sh
COCO_IMAGE_TAG="dev-$(date -u +%Y%m%d%H%M%S)"
bash scripts/aws/build-push-dev.sh --push-built-from OLD_LOCAL_TAG "$COCO_IMAGE_TAG"
```

Thay `OLD_LOCAL_TAG` bằng tag của lần build thành công trên máy local. Chế độ này
không lấy image từ tag lỗi trên ECR. Nếu đã sửa code sau lần build đó, phải build
mới thay vì dùng chế độ tái sử dụng. Không xóa tag cũ hoặc đổi ECR sang mutable.

## 4. Chuẩn bị manifest và Secret mà không in mật khẩu

```sh
python3 scripts/aws/prepare-dev-release.py --tag "$COCO_IMAGE_TAG"
```

Script lấy RDS endpoint/database và ECR/CDN/ALB từ output; đọc password bằng Secrets
Manager vào file local mode 600, không in nội dung. SMTP lấy từ `.env` nhưng không
sửa file gốc. JWT/OTP/proxy secret dev riêng được tạo một lần, giữ lại khi chuẩn bị
lại release. Không xóa file secret rồi chuẩn bị lại nếu muốn giữ phiên đăng nhập.
Checksum runtime trong Pod template giúp đổi Secret/origin kích hoạt rollout ngay
cả khi dùng lại cùng image tag; không cần in hoặc đưa password vào annotation.
File env không hỗ trợ secret nhiều dòng; nếu dùng cú pháp dotenv phức tạp, chuẩn bị
một env SMTP riêng và truyền `--smtp-env /DUONG_DAN/smtp.env`.

Các file nằm trong `artifacts/deploy/dev/`, đã gitignore:

- `application.yaml`: manifest có image/tag, origin và S3 thật; không có password.
- `metrics-server.yaml`: dev Metrics Server đã render.
- `backend-secret.env`: file private, không đưa lên Git/chat.
- `release.json`: tag và địa chỉ web của release.

Review manifest `application.yaml` trong IDE. Không thay nhầm DB/user/password vào
ConfigMap. Đưa file Secret vào SSM SecureString bằng key KMS vừa tạo:

```sh
COCO_DEPLOY_KEY="$(terraform -chdir=terraform/environments/dev output -raw deployment_secret_kms_key_arn)"
aws ssm put-parameter \
  --region ap-southeast-1 \
  --name /ecommerce/dev/application/backend-env \
  --type SecureString --tier Standard \
  --key-id "$COCO_DEPLOY_KEY" \
  --value file://artifacts/deploy/dev/backend-secret.env \
  --overwrite --query Version --output text --no-cli-pager
```

Secret được mã hóa bằng CMK; policy chỉ cho control plane decrypt parameter này qua
SSM, không cấp decrypt cho worker. Không dùng key SSM mặc định để chứa DB password
trong quy trình này. Parameter được chủ dự án quản lý riêng, không bị script destroy.

## 5. Cấu hình pull ECR cho worker đang chạy

```sh
python3 scripts/aws/run-dev-task.py ecr
```

Task tìm worker theo tag, đặt IMDSv2 required/hop limit 2 cho dev hiện hữu, cài
adapter kubelet credentialprovider/v1 trong repo và restart kubelet lần lượt.
Adapter dùng AWS CLI/node role lấy token ECR tạm và trả đúng giao thức kubelet;
không lưu token vào file imagePullSecret hoặc log. Quyền ứng dụng dev vẫn dùng
shared node role, chưa phải IAM identity tách theo Pod; không bật tương tự ở prod.

Lưu Command ID được in ra và kiểm tra (thay `COMMAND_ID` bằng giá trị thật):

```sh
python3 scripts/aws/run-dev-task.py status COMMAND_ID
```

Chỉ tiếp tục khi **cả hai worker Success**. `[]` là chưa có invocation hiển thị,
không phải thành công; `InProgress` thì đợi và chỉ chạy lại status, không gửi lại task.
Nếu Failed, kiểm tra stderr của invocation trước khi thay đổi gì tiếp.

## 6. Triển khai web

```sh
python3 scripts/aws/run-dev-task.py deploy
```

Task trên control plane đọc SecureString vào file tạm mode 600, tạo/cập nhật Secret
Kubernetes, áp dụng Metrics Server và app/Redis, rồi chờ rollout. Mật khẩu không nằm
trong SSM command payload hoặc output. File env tạm được gỡ sau task, Secret K8s và
SSM parameter được giữ để chạy ứng dụng. Task không gọi SQL hoặc tự sửa schema.

Kiểm tra Command ID như bước 5. Chỉ khi Success mới kiểm tra web. Nếu backend không
Ready, có thể thiếu schema RDS, sai config hoặc Redis chưa sẵn sàng; đọc lỗi trước,
không chạy migration/seed hoặc nới probe để ép thành công.

## 7. Xác nhận bằng request đọc

```sh
COCO_WEB_ORIGIN="http://$(terraform -chdir=terraform/environments/dev output -raw alb_dns_name)"
curl --fail --silent --show-error "$COCO_WEB_ORIGIN/health/live"
curl --fail --silent --show-error --output /dev/null "$COCO_WEB_ORIGIN/api/v1/categories"
curl --fail --silent --show-error --output /dev/null "$COCO_WEB_ORIGIN/api/v1/auth/csrf"
printf '\nWeb: %s\n' "$COCO_WEB_ORIGIN"
```

Trang chủ HTTP 200 chưa chứng minh API/ảnh/OTP hoạt động. Mở catalog và shop đã có
trong DB, kiểm tra ảnh sản phẩm/logo, không gửi URL có chữ ký vào chat. Test OTP chỉ
với tài khoản thử và thao tác do chủ dự án chủ động thực hiện; script không tạo user/
đơn hàng. Các API ghi/OTP có tác động nghiệp vụ bình thường khi người dùng gọi.

Frontend HPA 2–4 Pod, backend 2–10 Pod; Metrics Server phục vụ CPU HPA. Node Autoscaler,
EBS CSI và [monitoring có PVC](../../monitoring/README.md) vẫn có điều kiện riêng,
không được cài hoặc tuyên bố hoạt động bởi task web này.

Nếu cần debug, dùng SSM vào control plane rồi đọc `kubectl -n coco get pods`,
`kubectl -n coco describe pod TEN_POD` và log backend; không đưa Secret/kubeconfig/
URL có chữ ký vào báo cáo. `scripts/k8s/check-cluster.sh` kiểm tra node/CNI/CoreDNS.
