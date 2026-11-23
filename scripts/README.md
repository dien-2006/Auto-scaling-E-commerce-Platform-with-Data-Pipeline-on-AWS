# Script dùng lại cho dự án

Chạy bằng **Bash** từ bất kỳ thư mục nào. Các script tự xác định gốc repo.
Chưa có script nào được chạy trong lúc tạo các tệp này.

Xóa dev không backup và một lệnh dựng lại cả web/monitoring/ETL/autoscaling đã có
entry point `aws/dev-stack.sh`. Đây là **destroy thật**, không phải stop EC2.
Xem [hướng dẫn và điều kiện đầu vào](aws/DEV-STACK.md) trước khi chạy; lệnh up được
chủ dự án cho phép nhập schema/demo vào RDS mới, không chỉnh sửa SQL nguồn.

ETL dev có entry point `aws/etl-dev.sh` cho test/check/setup/upload/run/publish/report;
`aws/plan-etl-dev.sh` chỉ tạo plan Glue, `aws/prepare-etl-dev.py` lấy cấu hình từ
Terraform outputs, `aws/check-etl-iam.sh` sinh baseline IAM bằng Autopilot để review.
Các bước ghi AWS và chạy job đều do chủ dự án gọi riêng. Không chạy SQL trên RDS.
Xem [quy trình ETL dev](../etl/README.md).

```sh
# Xem account và trạng thái hạ tầng dev, không tạo tài nguyên:
bash scripts/aws/status-dev.sh

# Init, validate và lưu plan mới ở Terraform dev:
bash scripts/aws/plan-dev.sh

# Xem lại plan vừa tạo:
terraform -chdir=terraform/environments/dev show -no-color dev.tfplan

# Áp dụng plan đã lưu; tạo/cập nhật tài nguyên AWS có phí:
bash scripts/aws/apply-dev.sh
```

Nếu dùng profile riêng, đặt `AWS_PROFILE` trước khi chạy. Không đưa credential vào script.
Region được cố định là `ap-southeast-1` cho các script AWS hiện tại.
Yêu cầu AWS CLI, Terraform và credential phù hợp.

| Đường dẫn | Mục đích |
| --- | --- |
| `aws/lib/common.sh` | Xác định đường dẫn, region, kiểm tra công cụ/account |
| `aws/plan-dev.sh` | Khởi tạo Terraform, validate, tạo `dev.tfplan` |
| `aws/apply-dev.sh` | Áp dụng chính xác `dev.tfplan` đã xem |
| `aws/status-dev.sh` | Đọc output Terraform, trạng thái EC2 và SSM |
| `aws/upload-catalog-images.sh` | Xem trước/import ảnh trong data health vào bucket dev, bỏ qua object đã tồn tại |
| `check-release.sh` | Kiểm tra shell, unit test, frontend lint/typecheck và Terraform mock test; không deploy |
| `aws/plan-web-dev.sh` | Lập plan sửa web/IAM/CORS và key mã hóa Secret dev; chưa apply |
| `aws/build-push-dev.sh` | Build linux/amd64, push và xác nhận image trên ECR với tag mới |
| `aws/prepare-dev-release.py` | Render manifest từ output thật, lấy RDS secret vào file local riêng mode 600 |
| `aws/run-dev-task.py` | Owner chạy task SSM: cấu hình ECR trên worker hoặc triển khai bản render lên control plane |
| `k8s/ecr-credential-provider.py` | Adapter kubelet credentialprovider/v1 lấy token ECR tạm qua AWS CLI/node role |
| `aws/repair-bootstrap-awscli.sh` | Chỉ chạy trên EC2: sửa lỗi apt không có awscli trước kubeadm init/join |
| `k8s/check-cluster.sh` | Chỉ chạy trên control plane: chờ node Ready và kiểm tra Flannel/CoreDNS |
| `package-images.ps1` | Script đóng gói image đã có trước đó |

`plan-dev.sh` ghi lại `dev.tfplan`; xem bản mới trước mỗi lần apply.
`apply-dev.sh` không hỏi nhập `yes` vì sử dụng saved plan. Chỉ gọi script khi đã
chấp nhận nội dung plan. Terraform vẫn có thể sửa/xóa tài nguyên nếu plan yêu cầu;
script không tự xác định thay bạn rằng plan an toàn. Nếu plan cũ hoặc sai account/
region, tạo lại plan và kiểm tra trước khi apply.

Các script không chạy SQL, tạo bảng, migration, seed, reset DB hoặc xóa volume.
Root Terraform dev có khai báo **RDS mới**; apply có thể quản lý cả hạ tầng DB theo
plan, nên phải review các thao tác trên RDS nếu tài nguyên đã chứa dữ liệu.

`dev-stack.sh destroy --delete-data` xóa dev không backup; `dev-stack.sh up` dựng
generation mới từ source demo local. Không phải phục hồi dữ liệu cũ. Luồng dev cho web đã có script
build/push/render/deploy qua SSM; làm theo [hướng dẫn dev](../k8s/overlays/dev/README.md).
Monitoring có PVC vẫn cần EBS CSI/IAM riêng và chưa thuộc task deploy web.
Không coi script đã được xác minh trên AWS trước khi chủ dự án chạy và kiểm tra kết quả.

CSI dev có các entry point riêng: `aws/plan-monitoring-dev.sh` chỉ tạo plan IAM/rule
scrape; `aws/prepare-ebs-csi-dev.py` dùng Helm/kustomize local để render;
`aws/run-dev-task.py csi` gửi SSM cài CSI và StorageClass sau khi người dùng review.
Không tạo PVC/EBS hoặc cài Prometheus/Grafana trong CSI task. Hướng dẫn, giới hạn
IAM ở mức node và chi phí lưu trữ ở [monitoring README](../k8s/monitoring/README.md).

Sau CSI, `aws/prepare-monitoring-dev.py` render chart/resources và nhận mật khẩu
Grafana/SMTP bằng getpass; `--store` lưu bundle vào SSM SecureString riêng sau khi
review/apply quyền giải mã monitoring. `aws/run-dev-task.py monitoring` cài chart
qua SSM, tạo PVC EBS, không chạy SQL. Không gửi file monitoring-secrets.json lên chat.

## AWS identity của Kubernetes node

`k8s/configure-aws-node.sh` được Terraform nhúng vào bootstrap sau ECR provider,
trước kubeadm init/join. Nó lấy Instance ID, AZ, region và instance type từ IMDSv2,
ghi flags kubelet để node mới đăng ký provider ID và nhãn topology đúng môi trường.
Không thay đổi launch template đang dùng cho tới khi chủ dự án review/apply Terraform.

Node đang tồn tại được cập nhật qua script riêng, mặc định chỉ xem inventory:

```sh
python3 scripts/aws/repair-node-identity.py
python3 scripts/aws/repair-node-identity.py --submit
```

Script kiểm tra account/VPC, rồi gửi SSM command tới control plane để đối chiếu
InternalIP của toàn bộ node với EC2 trước khi patch. Dừng nếu ID/nhãn xung đột.
Không restart kubelet, thay instance, thay taint, tạo EBS hoặc chạy SQL.
Dùng lệnh status được in ra để kiểm tra SSM. Đây là prerequisite; chưa cài CSI,
Cluster Autoscaler hoặc Prometheus/Grafana/Alertmanager. Không chạy lại toàn bộ
Terraform apply trên hệ thống thật chỉ để áp dụng bản sửa node hiện hữu này.

## Import ảnh catalog có sẵn, không sửa DB

```sh
bash scripts/aws/upload-catalog-images.sh --dry-run
# Chỉ chạy sau khi đã kiểm tra key đích trong phần xem trước:
bash scripts/aws/upload-catalog-images.sh --upload
```

Script cố định bucket `ecommerce-dev-product-images-858525799322-ap-southeast-1`,
kiểm tra đúng owner, dùng tài khoản AWS local để upload (không dùng worker role).
Giữ key `ProductImages/{shop}/{product_id}/{file}.jpg` và `logo/1.png` đến `logo/3.png`;
không thêm prefix `data health/`. Giữ dấu cách và chữ hoa trong tên key.
`--no-overwrite` bỏ qua key đã có, không đảm bảo nội dung cũ giống file local.
Nếu CLI báo không hỗ trợ tùy chọn này, dừng và cập nhật AWS CLI trước;
không bỏ tùy chọn để chạy tiếp. Không có `--delete` hoặc ACL public-read.

Key đích phải trùng reference DB hiện hữu; chưa đọc DB để xác nhận trong bước này.
Backend hỗ trợ đọc key ảnh sản phẩm `ProductImages/...` theo ba shop đã định nghĩa;
key logo cũ `logo/*.png` đã có luồng sinh URL ký và frontend nhận URL HTTPS.
Cần triển khai image mới cùng cấu hình bucket/credential đúng để logo hiện trên UI.
Policy IAM đã bổ sung read-only cho ảnh import,
nhưng cần tạo plan mới và áp dụng riêng sau khi review; không dùng lại plan IAM cũ.
CloudFront hiện chỉ được thiết kế phục vụ prefix ảnh mới, không tự phân phối ảnh import.
Ảnh sản phẩm import dùng presigned GET qua backend khi đã cấu hình bucket/credential đúng.
Chưa upload hoặc chạy thử script trong lúc tạo tệp.

## Nghiệm thu ETL và kiểm tra autoscaling

Task `aws/run-dev-task.py dashboards` gửi riêng JSON `Coco - Application` lên
ConfigMap có nhãn grafana_dashboard=1. Dùng để cập nhật biểu đồ request/s, CPU Pod
và CPU worker mà không chạy lại Helm, đổi mật khẩu hoặc restart workload.

HTTP metrics frontend cần image mới: `aws/build-push-frontend-dev.sh NEW_TAG` chỉ
build/push frontend; `aws/run-dev-task.py frontend-image --tag NEW_TAG` rollout
riêng Deployment frontend qua SSM sau khi xác nhận image tồn tại. Đợi Success,
rồi task `http-metrics` kiểm tra exporter và đăng ký ServiceMonitor nội bộ 9091.
Task `dashboards` vẫn chỉ cập nhật ConfigMap. Hướng dẫn và giới hạn của P95,
Throughput, Error Rate ở [monitoring README](../k8s/monitoring/README.md).

`aws/demo-k6-dev.sh smoke|scale` chạy HTTP GET qua đúng ALB dev lấy từ Terraform,
bằng k6 local hoặc Docker image đã ghim digest. Mặc định smoke; chỉ `scale` mới
tăng tải dần để quan sát HPA/worker. Không chạy login/checkout hoặc sửa DB. Có phí
AWS nếu worker tăng. Xem [k6 demo và biểu đồ](../tests/k6/README.md).

Quy trình triển khai scaling đầy đủ ở [autoscaling dev runbook](../k8s/autoscaling/RUNBOOK-dev.md).
`aws/plan-autoscaling-dev.sh` có guard chỉ cho phép ba resource IAM.
`aws/prepare-autoscaling-dev.py bootstrap` mặc định preview; `--submit` chỉ cập nhật
template của worker tạo sau này và giới hạn ASG 2–4. `render` tạo manifest với role
đã apply. Task SSM `autoscaling` cài controller; `scaling-status`, `scaling-demo`,
`scaling-demo-stop` hỗ trợ nghiệm thu. Không cài thêm Helm Autoscaler song song.

`aws/etl-dev.sh finish` chạy/tiếp tục một batch, lưu Run ID cục bộ, đợi cả hai Glue
job, publish đúng batch Gold vào Catalog và kiểm tra cả ba báo cáo Athena. Chỉ chủ
dự án chạy lệnh này; có phí AWS, không chạy SQL hay sửa dữ liệu RDS. Dùng lại lệnh
để tiếp tục batch đã lưu, hoặc `finish --run-id RUN_ID_THAT` cho batch có sẵn.
`--new-run` là thao tác chủ động tạo một batch mới, không dùng để chữa timeout.

`aws/check-autoscaling-dev.py` chỉ đọc cấu hình ASG/launch template đang dùng trên
AWS và inventory worker/AZ để phát hiện bootstrap cũ. Không cài Autoscaler, không
thay IAM, không tăng/giảm worker. Trình tự đầy đủ ở [ETL README](../etl/README.md).

## Sửa bootstrap EC2 bị lỗi gói apt awscli

Terraform template đã chuyển sang bộ cài AWS CLI chính thức cho các máy tạo mới.
Sửa template không tự chạy lại user-data trên EC2 đang tồn tại; không cần destroy.

Với máy đã lỗi, mở `aws/repair-bootstrap-awscli.sh`, sao chép nội dung, rồi trong
**phiên SSM trên EC2** tạo tệp bằng `cat > /tmp/coco-repair-bootstrap.sh <<'SH'`,
dán nội dung script và kết thúc bằng dòng `SH`. Tiếp đó tự chạy:

```sh
sudo bash /tmp/coco-repair-bootstrap.sh
```

Script chỉ chấp nhận đúng lỗi apt đã xác định; dừng nếu có dấu hiệu kubeadm đã
init/join, hoặc cloud-init đang chạy. Nó cài AWS CLI, giữ bản user-data gốc rồi chạy
bản sao đã bỏ gói apt `awscli`. Có thay đổi hệ điều hành/Kubernetes và xuất bản join
token theo bootstrap, không chạy SQL. Không gửi join token hoặc kubeconfig vào chat.
Sửa control plane trước; chỉ sửa worker khi log worker xác nhận cùng lỗi.
`cloud-init status` có thể vẫn báo lỗi lịch sử sau khi sửa thủ công; kiểm tra log
repair, kubelet/containerd và trạng thái node để xác nhận. Chưa chạy thử script.
