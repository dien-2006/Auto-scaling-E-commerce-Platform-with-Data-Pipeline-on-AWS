# Chạy Cluster Autoscaler

Dev dùng [RUNBOOK-dev.md](RUNBOOK-dev.md), manifest ghim v1.34.6 và các task SSM
có kiểm tra bootstrap/IAM/baseline. Worker min 2/max 4; source có role riêng và
provider ID. Không cài thêm Helm controller từ values-dev.yaml.

HPA tăng/giảm Pod. Cluster Autoscaler tăng/giảm worker EC2 khi Pod không đủ chỗ chạy hoặc node dư tài nguyên. Control plane vẫn một máy.

Dev dùng `cluster-autoscaler-dev.yaml`; hai file values-dev.yaml/values-prod.yaml
giữ để tham khảo cho Helm/prod, không được quy trình dev hiện tại sử dụng.

## Điều kiện trước khi cài

- Worker ASG dev: min 2, ban đầu 2, max 4.
- Apply role riêng của Autoscaler theo IAM plan có guard, không gắn quyền scaling vào worker/web role.
- Node có AWS provider ID để liên kết với instance EC2. Source bootstrap đã có cấu hình này; cần kiểm tra launch template đang dùng trên AWS, vì sửa file local không tự cập nhật máy mới.
- Pod lấy được credential AWS; kiểm tra IMDSv2/identity thay vì mặc định cho rằng EC2 role luôn truy cập được từ Pod.
- Node/network, Metrics Server và HPA ứng dụng đã hoạt động.

Chạy theo thứ tự test → IAM plan/apply → bootstrap preview/submit → render → SSM
install → kiểm thử hai chiều trong [runbook](RUNBOOK-dev.md).

Sau khi nghiệm thu ETL, chạy từ gốc repo trên máy local:

```sh
python3 scripts/aws/check-autoscaling-dev.py
```

Script chỉ đọc account, ASG/EC2 và launch template thực tế; không thay IAM hay số
worker. Sửa các prerequisite fail trước khi cài. Kiểm tra này không xác nhận quyền
IAM, deployment Autoscaler hay worker mới đã join Ready; cần kiểm tra các bước đó
riêng khi triển khai. Task `run-dev-task.py autoscaling` cài controller qua SSM.

Hiện dev dùng một ASG trải hai AZ. EBS của monitoring thuộc một AZ cụ thể, nên
không thể coi worker ở AZ kia là nơi thay thế volume. Trước khi kiểm thử scale-down
cần xác định vị trí PVC/Pod và bảo đảm giữ capacity đúng AZ; hướng tách ASG theo AZ
cần plan di chuyển worker riêng, không tự destroy/recreate ASG hiện hữu.

## Kiểm tra

```sh
python3 scripts/aws/run-dev-task.py scaling-status
```

Đọc output SSM của command vừa gửi như hướng dẫn runbook. Quy trình này chỉ cho
dev; prod cần thiết kế/kiểm chứng IAM và topology riêng. Chỉ khi Pod Pending vì
thiếu tài nguyên, Autoscaler mới cần tăng worker; có request không đồng nghĩa
phải tăng ngay lên bốn máy.
