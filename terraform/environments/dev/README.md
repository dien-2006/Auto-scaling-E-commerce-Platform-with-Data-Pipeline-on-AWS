# Terraform dev

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

Cấu hình Kubernetes: 1 control plane + 2 worker `t3.medium` ban đầu; worker min 1/max 4. RDS `db.t4g.small`. Không đổi số lượng máy để chạy các bước hướng dẫn này.

Output có `rds_endpoint`, `rds_database_name`, `rds_master_secret_arn`, `etl_bucket_name`, `alb_dns_name` và hai ECR URL.

Kiểm tra offline sau khi init:

```sh
terraform -chdir=terraform/environments/dev test
```

Test dùng mock provider, cần Terraform >= 1.7. Bước tiếp theo: [Kubernetes](../../../k8s/README.md) và [ETL](../../../etl/README.md). Giữ file state của môi trường này riêng biệt.
