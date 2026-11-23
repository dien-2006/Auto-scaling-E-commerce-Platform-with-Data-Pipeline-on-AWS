# Triển khai và nghiệm thu autoscaling dev

Quy trình hiện tại dùng Cluster Autoscaler v1.34.6 cho kubeadm Kubernetes 1.34,
giữ ASG dev 2–4 worker, một control plane. Không cài thêm Helm Autoscaler từ
values-dev.yaml hoặc ASG CPU target-tracking policy song song.

Chạy mọi lệnh dưới đây từ **gốc repo trên máy local**. Các lệnh Kubernetes được
script gửi qua SSM; không dùng admin.conf của EC2 trên WSL. Tác giả chưa chạy các
test hay lệnh AWS trong lúc sửa; người sở hữu chạy và kiểm tra từng bước.

## 1. Kiểm tra code

```sh
python3 -m unittest discover -s scripts/tests -p 'test_autoscaling.py' -v
python3 -m unittest discover -s scripts/tests -p 'test_check_autoscaling.py' -v
bash -n scripts/aws/plan-autoscaling-dev.sh
bash -n scripts/k8s/install-autoscaling-dev.sh
terraform -chdir=terraform/environments/dev validate
terraform -chdir=terraform/environments/dev test -filter=tests/environment.tftest.hcl
```

Nếu báo module not installed, init lại trong dev rồi validate/test. Chỉ tiếp tục
khi kiểm tra qua; mock tests không chứng minh AWS live hoạt động.

## 2. Plan và apply quyền riêng cho Autoscaler

```sh
bash scripts/aws/plan-autoscaling-dev.sh
bash scripts/aws/check-autoscaling-iam.sh
```

Plan gate chỉ cho phép create/update ba resource: role Autoscaler, runtime policy
của role và quyền AssumeRole của control plane. Nếu có mutation EC2/ASG/RDS hay
delete/replacement hoặc resource ngoài danh sách: **không apply**. Targeted plan
không reconcile những thay đổi khác của môi trường.

Runtime policy theo danh sách quyền upstream AWS Autoscaler v1.34 (bỏ EKS vì đây
là kubeadm); quyền thay capacity/terminate chỉ cho ASG dev với ownership tags.
Worker/web role không có quyền scaling. Controller chạy hostNetwork trên control
plane và AssumeRole qua IMDSv2, không dùng access key. Đây là trust boundary theo
node, không phải IRSA/Pod Identity.

check-autoscaling-iam.sh dùng IAM Policy Autopilot sinh baseline quyền **operator
apply Terraform**, không phải runtime policy. Nó không upload/apply policy.
Plan JSON tạo riêng tư có thể chứa dữ liệu nhạy cảm: không commit/gửi lên chat.

Sau khi review plan:

```sh
terraform -chdir=terraform/environments/dev apply autoscaling-dev.tfplan
```

## 3. Bootstrap đúng cho worker tạo sau này

```sh
python3 scripts/aws/prepare-autoscaling-dev.py bootstrap
```

Mặc định chỉ preview. Nó dùng terraform console đánh giá bootstrap từ **source
local hiện tại**, không lấy user-data cũ trong state. Đối chiếu template ID, IP
control plane, installer AWS CLI, ECR/provider ID, Kubernetes minor, IMDS và join
command. User-data không chứa join token: worker mới đọc SSM khi boot.

Nếu preview đúng ASG dev, min 2/max 4 và desired giữ nguyên:

```sh
python3 scripts/aws/prepare-autoscaling-dev.py bootstrap --submit
python3 scripts/aws/check-autoscaling-dev.py
```

Submit tạo version kế thừa template đang dùng, chỉ cập nhật user-data/IMDS, ghim
ASG vào version số và min/max 2/4. Giữ AMI, instance type, SG, subnet, desired và
instance đang chạy; không gọi instance refresh/terminate hay sửa control plane.
Nếu update ASG fail sau khi đã tạo version, xem preview lại trước khi submit;
create-launch-template-version có client token để tiếp tục cùng yêu cầu.

Terraform source cũng giữ min 2, bootstrap chung và version số để triển khai mới
nhất quán. **Không full apply để chữa cluster hiện hữu**: thay đổi control-plane
user-data/AMI pending khác có thể stop/start hoặc replace máy. Reconcile full plan
là bước riêng sau này; không destroy/apply lại DB hoặc bucket.

## 4. Cài controller qua SSM

```sh
python3 scripts/aws/prepare-autoscaling-dev.py render
python3 scripts/aws/run-dev-task.py autoscaling
```

Lệnh cuối in Command ID và lệnh status. Chỉ tiếp tục khi status **Success**.
Nếu fail, đọc output của chính command đó, không submit lặp liên tục:

```sh
python3 scripts/aws/run-dev-task.py status COMMAND_ID_THAT
aws ssm get-command-invocation --region ap-southeast-1 \
  --command-id COMMAND_ID_THAT --instance-id CONTROL_PLANE_INSTANCE_ID_HIEN_TAI \
  --query '{Status:Status,Output:StandardOutputContent,Error:StandardErrorContent}' \
  --output json --no-cli-pager
```

run-dev-task.py tự tìm control plane đang chạy theo tag, không hardcode ID cũ.
Installer kiểm tra Kubernetes 1.34, tránh controller cạnh tranh, kiểm tra role thực
sự AssumeRole và đọc ASG. Nó kiểm tra timer xuất bản join token, thêm retry mạng
cho publisher và refresh token trước khi cài. Không in token/credential.

Trước khi bật controller, nó đối chiếu node provider ID với ASG, bảo vệ một worker
Ready mỗi AZ bằng scale-down-disabled=true, bảo vệ thêm mọi worker đang giữ PVC,
giữ annotation bảo vệ có sẵn. Redis OTP hiện hữu được đánh safe-to-evict=false
mà không restart. Source Redis/monitoring cũng có annotation cho lần triển khai sau.

## 5. Kiểm thử hai chiều

```sh
python3 scripts/aws/run-dev-task.py scaling-status
```

Lấy output command như trên: controller Running, ConfigMap cluster-autoscaler-status
nhận đúng node group và không có lỗi AccessDenied, missing credentials/provider ID
hoặc No node group config. Success của SSM chưa chứng minh đã scale EC2.

Khi controller ổn, chủ động tạo workload demo (có phí EC2/EBS trong khung max 4):

```sh
python3 scripts/aws/run-dev-task.py scaling-demo
```

Demo tạo riêng namespace scaling-demo, bốn pause Pods request 1 CPU/64 MiB mỗi Pod,
chỉ lên worker. Nó tạo thiếu chỗ scheduler bằng request, không đốt CPU, không gọi
web/DB và không mount PVC/Secret. Chờ command hoàn thành rồi kiểm tra worker tăng
từ 2 lên 3 hoặc 4, node mới Ready, Pods từng Pending nay Running:

```sh
python3 scripts/aws/check-autoscaling-dev.py
```

Nếu ứng dụng đang request nhiều tài nguyên, có thể một số demo Pods vẫn Pending
ở max 4. Đọc events/log; không tự tăng max hay giảm request ứng dụng. Timeout theo
dõi không hủy workload hoặc EC2; demo vẫn tồn tại cho đến khi chủ dự án dừng.

```sh
python3 scripts/aws/run-dev-task.py scaling-demo-stop
```

Lệnh chỉ scale Deployment demo về 0, không xóa namespace/app/dữ liệu. Chờ khoảng
10–20 phút hoặc lâu hơn nếu có Pod/PDB chặn, rồi chạy scaling-status và script
check để xác nhận worker dư tự rút. Không dùng Terraform apply/set desired=2 làm
bằng chứng scale-in. HPA cần thử tải HTTP riêng; pause demo chỉ nghiệm thu nhánh
scheduler → Autoscaler → ASG → bootstrap/join và chiều thu hẹp.

## Giới hạn dev

Hai worker nền được bảo vệ; CA chỉ rút worker tăng thêm đủ điều kiện. Node giữ
PVC, singleton OTP, kube-system Pod hoặc PDB có thể chặn scale-in. Không gỡ bảo vệ
hay ép xóa chỉ để demo xuống được hai node.

Một ASG trải hai AZ và annotation giữ bố trí hiện tại khi CA scale-down, không
bảo đảm replacement đúng AZ EBS khi instance/AZ hỏng. Không tự tách/destroy ASG
hoặc chuyển volume. Production cần nhóm theo AZ và kế hoạch di chuyển riêng.
Sau khi worker nền được thay do lỗi, chạy lại bước cài/bảo vệ để đối chiếu baseline
mới. Control plane một máy, RDS Single-AZ và singleton Redis vẫn là giới hạn dev.

Chỉ nghiệm thu khi worker tăng Ready, demo chạy được và worker dư tự giảm sau khi
dừng demo; HPA có metrics hay ASG tồn tại chưa đủ để kết luận.

Tham khảo: [AWS Autoscaler v1.34](https://github.com/kubernetes/autoscaler/blob/cluster-autoscaler-1.34.6/cluster-autoscaler/cloudprovider/aws/README.md),
[CA FAQ](https://github.com/kubernetes/autoscaler/blob/cluster-autoscaler-1.34.6/cluster-autoscaler/FAQ.md).

Image được ghim theo [release v1.34.6](https://github.com/kubernetes/autoscaler/releases/tag/cluster-autoscaler-1.34.6),
bao gồm các bản vá upstream và scheduler dependencies Kubernetes v1.34.13.
