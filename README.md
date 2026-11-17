# E-commerce Platform và Data Pipeline trên AWS

Repo chứa hạ tầng Terraform, cấu hình Kubernetes và pipeline ETL PostgreSQL → S3 → Athena. Kubernetes chạy bằng kubeadm trên EC2.

## Bắt đầu từ đâu?

| Thư mục | Chức năng | Hướng dẫn chạy |
| --- | --- | --- |
| `terraform/` | VPC, EC2/ASG, ALB, RDS, S3, ECR, CloudFront, Glue, CloudWatch | [Terraform](terraform/README.md) |
| `k8s/` | Frontend/backend, HPA, Metrics Server, Autoscaler, monitoring | [Kubernetes](k8s/README.md) |
| `sql/` | Schema nguồn PostgreSQL | [Khởi tạo database](sql/README.md) |
| `etl/` | Extract, transform, workflow và báo cáo Athena | [ETL](etl/README.md) |

Các lệnh trong README mặc định được chạy từ **thư mục gốc repo**, trừ khi một bước ghi rõ thư mục khác. `infra/` và `etl/glue_test/` không nằm trong luồng triển khai chính này.

## Công cụ cần có

- Terraform >= 1.6; dùng >= 1.7 nếu chạy bộ kiểm tra mock provider.
- AWS CLI đã có credential/profile cho đúng account.
- `kubectl`, Helm; kubeconfig và đường mạng tới từng cụm private.
- Python >= 3.11 và `venv` cho các script ETL cục bộ.
- `psql` trên host có thể truy cập RDS và được Security Group cho phép.
- Docker/image build tool nếu bạn cần build image ứng dụng bên ngoài repo.

## Thứ tự triển khai

1. Đọc [Terraform](terraform/README.md), chọn **dev hoặc prod**, chạy init → validate → plan. Kiểm tra plan trước khi apply.
2. Hoàn thiện bootstrap Kubernetes: CNI, xác thực ECR và các điều kiện truy cập cụm. Terraform hiện chưa tự cài các phần này.
3. Build/push frontend/backend lên đúng repository ECR. Repo hiện chưa chứa Dockerfile/source ứng dụng để thực hiện bước build này.
4. Khởi tạo [schema PostgreSQL](sql/README.md) và dữ liệu demo trong database `coco_marketplace`.
5. Theo [Kubernetes](k8s/README.md): cài Metrics Server, tạo Secret, triển khai overlay ứng dụng, rồi cấu hình Autoscaler/monitoring khi đủ điều kiện.
6. Theo [ETL](etl/README.md): cấu hình `.env`, kiểm tra tài nguyên, upload script, cấu hình workflow, chạy pipeline, tạo bảng Athena và query.

Mỗi môi trường có một control plane và hai worker EC2 `t3.medium` ban đầu, ASG tối đa bốn worker. RDS dùng `db.t4g.small`; prod vẫn bật Multi-AZ. Frontend HPA 2–4 Pod, backend 2–10 Pod.

## Kiểm tra cục bộ trước khi triển khai

Các lệnh sau không tạo tài nguyên AWS:

```sh
terraform fmt -check -recursive terraform
terraform -chdir=terraform/environments/dev init -backend=false
terraform -chdir=terraform/environments/dev validate
terraform -chdir=terraform/environments/dev test
kubectl kustomize k8s/overlays/dev
kubectl kustomize k8s/overlays/prod
kubectl kustomize k8s/metrics-server/dev
kubectl kustomize k8s/metrics-server/prod
```

`init` có thể tải provider. Các bài kiểm tra Terraform dùng mock provider; hướng dẫn kiểm tra ETL nằm trong [etl/tests](etl/tests/README.md).

`terraform apply`, `kubectl apply`, `helm upgrade --install` và các script ETL thao tác lên AWS/cluster thật, có thể phát sinh phí. Các giá trị `ACCOUNT_ID`, ARN, endpoint, Secret và tag image phải được điền trước. Việc render/validate đạt không thay thế việc chạy thử trên dev.
