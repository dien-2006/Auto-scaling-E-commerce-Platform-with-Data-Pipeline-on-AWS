# Các module Terraform dùng chung

Không chạy `apply` trực tiếp trong từng module. Entry point là [dev](../environments/dev/README.md) hoặc [prod](../environments/prod/README.md); các môi trường truyền biến và nối output giữa module.

| Module | Tài nguyên/chức năng |
| --- | --- |
| `network` | VPC, subnet, NAT, route |
| `security` | Security Group và rule |
| `iam` | EC2 role, instance profile, SSM/ECR permissions |
| `kubernetes` | EC2 control plane, worker launch template/ASG, bootstrap kubeadm |
| `alb` | ALB, target group, listener, ASG attachment |
| `database` | RDS PostgreSQL và subnet group |
| `storage` | S3 ảnh/data lake, versioning, encryption, lifecycle |
| `ecr` | Repository frontend/backend và lifecycle image |
| `cloudfront` | Phân phối ảnh S3 qua OAC |
| `etl` | Glue jobs/connection/roles, Catalog database, Athena workgroup |
| `monitoring` | CloudWatch dashboard, alarms, log group |

Sau khi sửa module, chạy validate và mock test tại cả hai môi trường theo [README Terraform](../README.md). Module Kubernetes không triển khai ứng dụng frontend/backend; phần đó thuộc `k8s/`.
