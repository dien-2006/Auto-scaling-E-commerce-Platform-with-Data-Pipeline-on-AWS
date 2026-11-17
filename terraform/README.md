# Chạy hạ tầng Terraform

## Chọn môi trường

| | Dev | Prod |
| --- | --- | --- |
| Thư mục chạy | `environments/dev` | `environments/prod` |
| VPC | `10.10.0.0/16` | `10.20.0.0/16` |
| NAT Gateway | Một NAT dùng chung | Hai NAT, mỗi AZ một NAT |
| Kubernetes EC2 | `t3.medium`, 1 control plane + 2 worker ban đầu | Như dev |
| Worker ASG | Min 1, ban đầu 2, max 4 | Min 1, ban đầu 2, max 4 |
| RDS | `db.t4g.small`, Single-AZ, 20 GiB ban đầu | `db.t4g.small`, Multi-AZ, 20 GiB ban đầu |
| ALB | HTTP | HTTPS, cần ACM certificate ARN |

Hướng dẫn riêng: [dev](environments/dev/README.md), [prod](environments/prod/README.md). Danh mục module: [modules](modules/README.md).

## Điều kiện

- Terraform >= 1.6; các bài kiểm tra `terraform test` cần >= 1.7.
- AWS CLI có credential/profile cho đúng account; quyền tạo các tài nguyên được khai báo.
- Region mặc định `ap-southeast-1`.
- Prod cần certificate ACM hợp lệ trong cùng region với ALB. Terraform không tự cấp certificate này.

Chạy từ **gốc repo**:

```sh
aws sts get-caller-identity
terraform version
```

Nếu dùng profile, thiết lập `AWS_PROFILE` phù hợp trong shell trước khi chạy. Không đặt access key vào file Terraform.

## Kiểm tra cục bộ

```sh
terraform fmt -check -recursive terraform
terraform -chdir=terraform/environments/dev init -backend=false
terraform -chdir=terraform/environments/dev validate
terraform -chdir=terraform/environments/dev test
terraform -chdir=terraform/environments/prod init -backend=false
terraform -chdir=terraform/environments/prod validate
terraform -chdir=terraform/environments/prod test
```

Các test dùng mock provider, không tạo tài nguyên AWS. `init` cần tải provider nếu máy chưa có. Test prod dùng certificate ARN giả; ARN đó không dùng được cho triển khai thật.

## Triển khai dev

Nếu chưa có `terraform/environments/dev/terraform.tfvars`, sao chép file `terraform.tfvars.example` cùng thư mục rồi chỉnh giá trị. Không ghi đè file biến đang dùng.

```sh
terraform -chdir=terraform/environments/dev init
terraform -chdir=terraform/environments/dev validate
terraform -chdir=terraform/environments/dev plan -out=dev.tfplan
terraform -chdir=terraform/environments/dev show dev.tfplan
```

Kiểm tra đúng account, region, số EC2, RDS và mọi thao tác thay thế/xóa trong plan. Chỉ sau khi đã chấp nhận nội dung plan mới chạy bước **tạo/cập nhật tài nguyên có phí**:

```sh
terraform -chdir=terraform/environments/dev apply dev.tfplan
terraform -chdir=terraform/environments/dev output
```

Với prod, làm theo [hướng dẫn prod](environments/prod/README.md), dùng file plan riêng. Không chạy đồng thời hai môi trường nếu chỉ cần demo một môi trường.

## Lấy thông tin cho các bước tiếp theo

```sh
terraform -chdir=terraform/environments/dev output -raw ecr_frontend_url
terraform -chdir=terraform/environments/dev output -raw ecr_backend_url
terraform -chdir=terraform/environments/dev output -raw etl_bucket_name
terraform -chdir=terraform/environments/dev output -raw rds_endpoint
terraform -chdir=terraform/environments/dev output -raw rds_master_secret_arn
```

Các giá trị ARN ở trên là định danh tài nguyên, không phải mật khẩu. Dùng output để điền image URI cho `k8s/` và biến môi trường cho `etl/`.

## State và giới hạn hiện tại

Chưa có remote backend; state mặc định được lưu cục bộ trong từng thư mục môi trường. Giữ state và lock file an toàn, không commit state, không dùng state dev cho prod.

Terraform chưa tự hoàn thiện CNI, credential provider ECR, IAM/provider ID cho Cluster Autoscaler hoặc kubelet serving certificate dùng cho Metrics Server prod. Thực hiện các điều kiện đó trước khi coi Kubernetes đã hoạt động đầy đủ. Xem [k8s/README](../k8s/README.md).

Terraform tạo Glue job nhưng không upload script ETL hay chạy workflow. Thực hiện bằng [các lệnh ETL](../etl/README.md). Thay đổi user data không tự chạy lại trên control plane đã tồn tại (`user_data_replace_on_change = false`).

## Kết thúc buổi demo

Chỉ dừng EC2 không dừng toàn bộ chi phí: NAT, ALB, RDS và storage có vòng đời riêng. Việc dọn tài nguyên cần một plan riêng được kiểm tra trước. Prod có deletion protection, final snapshot và các bucket/repository không cho xóa khi còn dữ liệu; không vô hiệu hóa các bảo vệ này chỉ để ép lệnh dọn chạy qua.
