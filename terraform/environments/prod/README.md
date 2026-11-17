# Terraform prod

Chạy các lệnh dưới đây từ **gốc repo**. Xem [hướng dẫn chung](../../README.md) trước khi triển khai.

Điền `acm_certificate_arn` bằng certificate ACM thật trong `ap-southeast-1`, đã được xác thực. ALB prod bật HTTPS và deletion protection; RDS bật Multi-AZ, deletion protection và final snapshot.

Nếu chưa có `terraform/environments/prod/terraform.tfvars`, sao chép `terraform.tfvars.example` cùng thư mục và chỉnh giá trị. Không ghi đè file biến hiện có.

```sh
aws sts get-caller-identity
terraform -chdir=terraform/environments/prod init
terraform -chdir=terraform/environments/prod validate
terraform -chdir=terraform/environments/prod plan -out=prod.tfplan
terraform -chdir=terraform/environments/prod show prod.tfplan
```

Chỉ khi plan đúng với ý định của bạn, chạy bước tạo/cập nhật tài nguyên AWS có phí:

```sh
terraform -chdir=terraform/environments/prod apply prod.tfplan
terraform -chdir=terraform/environments/prod output
```

Cấu hình Kubernetes: 1 control plane + 2 worker `t3.medium` ban đầu; worker min 1/max 4. RDS `db.t4g.small`. Không đổi số lượng máy để chạy các bước hướng dẫn này.

Prod hiện không export endpoint/secret RDS ở root output. Lấy thông tin instance `ecommerce-prod-postgresql` qua RDS/Secrets Manager Console và bucket data lake qua S3 Console. Không dùng output RDS/bucket của dev cho ETL prod.

Kiểm tra offline sau khi init:

```sh
terraform -chdir=terraform/environments/prod test
```

Test dùng mock provider, cần Terraform >= 1.7. Bước tiếp theo: [Kubernetes](../../../k8s/README.md) và [ETL](../../../etl/README.md). Giữ file state của môi trường này riêng biệt.
