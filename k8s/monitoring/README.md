# Prometheus, Grafana và Alertmanager SMTP

Đây là cấu hình cho Kubernetes **kubeadm trên EC2** của repo, bắt đầu từ dev.
Các lệnh bên dưới để chủ dự án tự chạy từ gốc repo; chưa có lệnh nào được chạy thay bạn.
Không có bước migration, tạo bảng, seed, xóa volume hay sửa dữ liệu PostgreSQL.

## Phạm vi

- Backend `/metrics`: số request, mã HTTP, histogram thời gian; nhãn dùng route mẫu, không dùng ID cụ thể, query, email hay token. Health check và scrape không được tính vào lưu lượng API.
- ServiceMonitor scrape từng backend Pod qua Service ClusterIP riêng. Backend hiện chạy một Uvicorn process mỗi container; nếu đổi sang nhiều worker phải thiết kế lại multiprocess metrics trước.
- Blackbox probe trang `/` frontend và `/health/ready` backend qua Service nội bộ. Đây không phải kiểm thử checkout, upload S3 hoặc truy cập ALB từ Internet.
- Dashboard `Coco - Application`: request/s, tỷ lệ 5xx, p95, probe, CPU/RAM, restart và HPA. Node exporter, kube-state-metrics và dashboard cluster do chart cung cấp.
- Alertmanager gửi SMTP STARTTLS, gom nhóm và gửi thông báo khi đã phục hồi. Mật khẩu đọc từ Secret riêng.
- PVC dev: Prometheus 10Gi, Grafana 2Gi, Alertmanager 2Gi; gp3 mã hóa. Đây là tài nguyên EBS có phí khi bạn triển khai, độc lập volume DB.
- Đây là monitoring một replica, chưa HA/backup. PVC giữ dữ liệu qua Pod restart, không thay thế backup. Prometheus không thu thập nội dung log.

Metrics Server vẫn là [add-on riêng phục vụ HPA](../metrics-server/README.md).

## Quy trình dev qua SSM đang dùng

CSI có quy trình riêng cho kubeadm dev; không dùng EKS add-on hay IRSA:

```sh
# Local, gốc repo. Plan chỉ nhắm IAM CSI và rule scrape control plane.
bash scripts/aws/plan-monitoring-dev.sh
# Review: không RDS, không EC2 update/replacement, không delete. Sau đó tự apply:
terraform -chdir=terraform/environments/dev apply monitoring-dev.tfplan
python3 scripts/aws/prepare-ebs-csi-dev.py
# Review artifacts/deploy/dev/ebs-csi.yaml trước bước gửi SSM:
python3 scripts/aws/run-dev-task.py csi
```

Dùng lệnh status được script in ra và kiểm tra controller/DaemonSet Ready. CSI task
chưa tạo PVC, volume EBS hoặc cài bộ monitoring. Cần kiểm chứng provisioning/mount
thật khi tạo PVC tiếp theo; rollout CSI thành công chưa chứng minh toàn bộ IAM đúng.

Role riêng `ecommerce-dev-ebs-csi` gắn AWS managed `AmazonEBSCSIDriverPolicyV2`;
chỉ role control plane được assume role này. Controller một replica trên control
plane, host networking để dùng IMDSv2 hop limit 1; cấu hình profile chỉ chứa role
ARN, không có access key. Đây là ranh giới tin cậy ở mức node cho dev: tiến trình
có quyền dùng role control plane cũng có thể assume CSI role; chưa phải Pod identity.
Không gắn EBS policy vào role của worker web. Policy V2 giới hạn thao tác volume
theo tag CSI, chưa tách riêng mọi cluster trong cùng account. Không dùng cho prod
như một cơ chế cô lập theo Pod/cluster.

Node plugin dùng host networking trên worker, tránh trùng cổng với controller
trên control plane. Thông tin instance/AZ dùng IMDS và provider ID đã sửa. Chart
ghim `2.67.1`, image `v1.67.2`; renderer thêm `hostNetwork` cho controller vì chart
không có value `controller.hostNetwork`. Giữ taint control plane; chỉ controller
có toleration tương ứng. Không đặt workload dùng PVC lên control plane với cấu hình này.

Renderer dùng `--skip-tests` và `helmTester.enabled=false` để không mang Pod/RBAC
test Helm vào bản cài qua kubectl. Server dry-run không tạo ServiceAccount thật,
nên Pod test sẽ bị admission từ chối nếu vẫn còn trong manifest. Cấu hình dev chỉ
cài DaemonSet Linux và không dùng nhãn control-plane kiểu cũ `node-role.kubernetes.io/master`.

Sau CSI mới chuẩn bị Secret SMTP/Grafana và cài chart ở phần dưới. PVC dự kiến
tổng 14 GiB gp3 có phí; EBS bị ràng buộc AZ và `Retain` không tự xóa volume khi xóa
PVC/cluster. Không xem đây là backup hay HA. Nên theo dõi EC2/EBS API qua CloudTrail,
CloudWatch và log CSI khi điều tra cấp phát/gắn volume.

Các bước mới chưa được agent chạy test/render/apply hoặc kiểm chứng trên AWS.

### Cài monitoring qua SSM sau khi CSI đã Ready

Từ local, điền SMTP trong `artifacts/deploy/dev/alertmanager.yaml` (copy file mẫu),
không inline mật khẩu. Sau đó:

```sh
python3 scripts/aws/prepare-monitoring-dev.py
bash scripts/aws/plan-monitoring-dev.sh
# Review plan mới. Nếu chỉ thêm IAM giải mã monitoring và không thay EC2/RDS:
terraform -chdir=terraform/environments/dev apply monitoring-dev.tfplan
python3 scripts/aws/prepare-monitoring-dev.py --store
python3 scripts/aws/run-dev-task.py monitoring
```

Prepare render chart để review, hỏi username/password Grafana và SMTP qua terminal;
password dùng getpass. Gói secret local `monitoring-secrets.json` mode 0600 nằm trong
artifacts đã gitignore; không gửi file lên chat. `--store` là thao tác ghi AWS riêng:
SSM SecureString `/ecommerce/dev/monitoring/secrets`, dùng CMK deployment hiện có.
Terraform chỉ quản lý quyền giải mã đúng parameter cho control plane; không giữ
nội dung secret trong state và không đưa vào Secret của backend.

SSM task tải bundle đã mã hóa về thư mục tạm 0700, tạo ba Kubernetes Secret, cài Helm
3.22.1 nếu chưa có (bộ cài chính thức kiểm tra checksum), rồi Helm install/upgrade
chart 93.7.0, đợi PVC/Pod và áp dụng ServiceMonitor/Probe/dashboard/rule trong repo.
Bundle bí mật trên EC2 được xóa khi task kết thúc. Mật khẩu không có trong payload
SendCommand, Helm values hoặc log output. Không in nội dung secret khi chẩn đoán.

Task có timeout 90 phút nhưng thông thường kết thúc sớm hơn; status `Success` chưa
chứng minh backend targets UP hoặc email đã đến. Chỉ gửi email thử khi chủ dự án
chủ động chạy lệnh kiểm tra receiver. Alertmanager bắt đầu gửi alert theo rule khi
hoạt động. Không dùng prepare để reset mật khẩu Grafana đang có DB/PVC: admin
password của Grafana đã khởi tạo phải được đổi qua luồng quản trị Grafana.
Các target kubeadm etcd/controller-manager/scheduler/kube-proxy đang tắt vì endpoint thường chỉ bind loopback; dashboard tương ứng có thể không có số liệu. Không mở các cổng đó ra Internet.

## 1. Kiểm tra hạ tầng trước, chỉ đọc

```sh
kubectl --context coco-dev get nodes -o wide
kubectl --context coco-dev get csidriver
kubectl --context coco-dev -n kube-system get pods -o wide
kubectl --context coco-dev get storageclass
kubectl --context coco-dev get nodes -o 'custom-columns=NAME:.metadata.name,PROVIDER:.spec.providerID,ZONE:.metadata.labels.topology\.kubernetes\.io/zone'
kubectl --context coco-dev -n coco get deploy,svc,endpointslice,hpa
```

**Dừng trước bước cài nếu chưa có `ebs.csi.aws.com` hoạt động.** Terraform bootstrap hiện không tự cài EBS CSI. Cần controller/node plugin, quyền IAM đúng cho controller, EC2 provider ID/topology và khả năng gọi EC2 API. Hướng dẫn [EBS CSI cho cluster tự quản lý](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/blob/master/docs/install.md). Không dùng quy trình EKS/IRSA khi cluster này chưa có EKS/OIDC; không gắn quyền rộng cho toàn bộ worker để chữa tạm.

EBS gắn theo AZ: node thay thế phải có capacity trong AZ của PV. StorageClass dùng `WaitForFirstConsumer`, `Retain`; không xóa PVC/PV để xử lý Pending. Nếu Pending, đọc events của PVC/Pod và log CSI.

Cluster phải có CNI/DNS hoạt động và đủ RAM cho monitoring cùng ứng dụng. Terraform security module đã bổ sung quyền worker → control plane TCP 10250/9100 để scrape kubelet/node exporter; cần review Terraform plan trước khi áp dụng. Không chạy apply toàn bộ dev chỉ để cài monitoring vì root module còn quản lý RDS và các tài nguyên khác. Từ Pod phải truy cập được API server, kubelet, DNS, SMTP cổng 587 và registry; không mở cổng monitoring ra public.

Dev dùng kubelet certificate tự ký nên chart chỉ bỏ xác minh TLS ở đường scrape kubelet. Prod bật xác minh; cần CA-signed kubelet serving certificate có SAN phù hợp như hướng dẫn Metrics Server.

Ứng dụng phải dùng image có `/metrics`, Secret/ConfigMap thật và đúng endpoint PostgreSQL/Redis/S3. Overlay backend dùng các key `MARKETPLACE_*`; render qua quy trình [overlay dev](../overlays/dev/README.md). Không triển khai nguyên placeholder `ACCOUNT_ID` hoặc Secret mẫu.

## 2. Kiểm tra mã và render trước khi triển khai

Các test sau chỉ kiểm tra HTTP middleware/metrics bằng app test; không tạo bảng hay ghi DB:

```sh
cd backend
uv lock --check
uv sync --locked
uv run --locked pytest tests/test_metrics.py tests/test_app.py
uv run --locked ruff check app/core/metrics.py app/core/middleware.py app/main.py tests/test_metrics.py
cd ..
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm template monitoring prometheus-community/kube-prometheus-stack --version 93.7.0 --namespace monitoring -f k8s/monitoring/values-dev.yaml > /tmp/coco-monitoring-dev.yaml
kubectl kustomize k8s/monitoring/resources > /tmp/coco-monitoring-resources.yaml
```

Dependency và chart đã ghim phiên bản nhưng chưa chạy lock check, test, render hoặc triển khai trong phiên chỉnh sửa. Review hai bản render trước khi tiếp tục. Build/push image backend mới theo quy trình dự án và cập nhật tag trong overlay; render Helm không build ứng dụng.

## 3. Chuẩn bị Secret, không gửi mật khẩu vào chat

Tạo bản cấu hình cục bộ (đường dẫn đích đã được `.gitignore` bỏ qua):

```sh
cp -n k8s/monitoring/alertmanager/alertmanager.yaml.example k8s/monitoring/alertmanager/alertmanager.yaml
```

Mở file, sửa host SMTP, địa chỉ From, username, người nhận. Mẫu dùng STARTTLS cổng 587; chọn nhà cung cấp hỗ trợ và dùng app password nếu nhà cung cấp yêu cầu. Không dùng mật khẩu OTP của app theo mặc định; Secret monitoring độc lập.

Chuẩn bị ba file riêng bên ngoài repo: username Grafana, password Grafana, password SMTP (nội dung không có newline thừa). Thay đường dẫn bên dưới bằng đường dẫn thật. Lệnh `create secret` không ghi đè Secret đã tồn tại; nếu đã có, cập nhật theo quy trình Secret của bạn.

```sh
kubectl --context coco-dev create namespace monitoring --dry-run=client -o yaml | kubectl --context coco-dev apply -f -
kubectl --context coco-dev -n monitoring create secret generic grafana-admin --from-file=admin-user=/DUONG_DAN/USERNAME_GRAFANA --from-file=admin-password=/DUONG_DAN/PASSWORD_GRAFANA
kubectl --context coco-dev -n monitoring create secret generic alertmanager-smtp-auth --from-file=password=/DUONG_DAN/PASSWORD_SMTP
kubectl --context coco-dev -n monitoring create secret generic alertmanager-smtp --from-file=alertmanager.yaml=k8s/monitoring/alertmanager/alertmanager.yaml
```

## 4. Cài sau khi điều kiện ở bước 1 đã đạt

Lệnh Helm tạo PVC và có thể cấp phát EBS. Namespace `coco` phải tồn tại từ overlay ứng dụng.

```sh
kubectl --context coco-dev apply -f k8s/monitoring/storageclass.yaml
helm --kube-context coco-dev upgrade --install monitoring prometheus-community/kube-prometheus-stack --version 93.7.0 --namespace monitoring -f k8s/monitoring/values-dev.yaml --wait --timeout 10m
kubectl --context coco-dev wait --for=condition=Established crd/servicemonitors.monitoring.coreos.com crd/probes.monitoring.coreos.com crd/prometheusrules.monitoring.coreos.com --timeout=180s
kubectl --context coco-dev apply --dry-run=server -k k8s/monitoring/resources
kubectl --context coco-dev apply -k k8s/monitoring/resources
kubectl --context coco-dev -n monitoring get pods,pvc,svc
kubectl --context coco-dev -n monitoring get servicemonitor,probe,prometheusrule
```

Nếu PVC Pending: kiểm tra EBS CSI, IAM, AZ, events; không xóa volume DB. Nếu Pod unhealthy: đọc log và events, không đổi probe thành luôn thành công.

## 5. Xác nhận dashboard và email

Dashboard `Coco - Application` có ba biểu đồ đầu trang dành cho demo:

- Throughput frontend/backend: hai đường request/giây riêng từ metric ứng dụng,
  loại health/metrics; không phải số khách duy nhất hoặc tổng request ALB. Không
  cộng hai tầng vì frontend có thể gọi nhiều API backend cho một request.
- CPU từng Pod trong namespace coco: phần trăm CPU request của backend/frontend/
  Redis. Có thể vượt 100%; không phải % CPU cả node. HPA backend/frontend mục tiêu
  60% request, Redis không có HPA.
- CPU từng worker EC2: 100 trừ % idle trung bình các core, loại control plane
  kubeadm qua kube_pod_info của static Pod kube-apiserver. Ghép exporter Pod với
  tên node qua kube_pod_info, không hardcode IP và không phụ thuộc kube_node_role.

Panel **P95 latency frontend / backend** dùng histogram của từng tầng, cộng bucket
qua các Pod trước khi tính histogram_quantile; không lấy trung bình P95 từng Pod.
P95 frontend đo đến Node HTTP response finish, kể cả streaming và proxy, không phải
thời gian trình duyệt tải trang hoặc latency k6 qua Internet. Panel **Error Rate
frontend / backend** đo tỷ lệ HTTP 5xx, không gồm 4xx, browser JS errors, check k6
fail hay kết nối bị hủy trước finish. Metric bị thiếu không được biểu diễn thành
0 giả. Hai metric này và throughput cần đủ mẫu scrape/traffic để có giá trị.

### Bổ sung HTTP metrics frontend đang chạy trên AWS

Backend đã có `/metrics`. Frontend mới dùng Node preload tại
`frontend/observability/preload.cjs` trong Docker standalone để quan sát HTTP
request/response thực tế. Nó không đọc request body, cookie hoặc token; labels
chỉ gồm method/status có giới hạn. Histogram ghi response đã finish; response
bị hủy ghi riêng `marketplace_frontend_http_requests_aborted_total`, không gán
HTTP 5xx giả. Không dùng thêm package npm hoặc sửa package-lock.

Metrics frontend nghe nội bộ Pod `9091/metrics`; NodePort frontend vẫn chỉ target
port HTTP 3000. Không thêm listener ALB, hostPort hay port host Docker cho 9091.
Service ClusterIP/ServiceMonitor riêng cho Prometheus lấy job `coco-frontend`.
`npm run dev/start` trực tiếp không tự nạp preload này; runtime Docker được dùng
trên AWS mới có entry point đó. Không chạy file preload một mình để tạo số liệu.

**Cần build image frontend mới**, chỉ cập nhật dashboard sẽ chưa có dữ liệu
frontend. Chủ dự án chạy từ local, gốc repo, theo thứ tự:

```sh
node --test frontend/tests/http-metrics.test.mjs
python3 -m unittest discover -s scripts/tests -p 'test_frontend_metrics_task.py' -v
npm --prefix frontend run lint
python3 -m json.tool k8s/monitoring/resources/dashboards/coco-application.json >/dev/null
```

Các test mới dùng HTTP server localhost/mock CLI, không gọi AWS hay DB. Tác giả
chưa chạy test/lint/build/deploy hoặc query live trong lần sửa này. Chỉ tiếp tục
khi các kiểm tra đạt:

```sh
export COCO_FRONTEND_METRICS_TAG="dev-frontend-metrics-$(date -u +%Y%m%d%H%M%S)"
bash scripts/aws/build-push-frontend-dev.sh "$COCO_FRONTEND_METRICS_TAG"
python3 scripts/aws/run-dev-task.py frontend-image --tag "$COCO_FRONTEND_METRICS_TAG"
```

Dùng lệnh status được in ra, đợi SSM **Success** trước khi sang bước tiếp. Task chỉ
set image Deployment frontend và chờ rollout; không chạm backend, SSM Secret,
Redis, DB hoặc ASG. Tag này là frontend-only, không dùng làm tag chung hai image
trong prepare-dev-release.py. Không chạy task deploy với application.yaml cũ sau
rollout này vì có thể đưa frontend về image cũ; lần full release tiếp theo phải
build/render bộ release mới từ source đã cập nhật.

```sh
python3 scripts/aws/run-dev-task.py http-metrics
```

Task này chờ rollout frontend, gọi endpoint metrics loopback từ chính container
để xác nhận image mới, rồi apply Service/ServiceMonitor riêng. Đợi command Success.
Nếu endpoint chưa có, nó dừng trước khi đăng ký target; không sửa password hoặc
reinstall Helm chỉ để bật scrape. Sau đó:

```sh
python3 scripts/aws/run-dev-task.py dashboards
bash scripts/aws/demo-k6-dev.sh smoke
```

Đợi task dashboard Success, rồi mở `http://localhost:3002/d/coco-application`,
refresh và chọn Last 15 minutes. Target Prometheus `coco-frontend` phải UP; cần
vài lần scrape sau khi có request để thấy cả hai đường. Không có lịch sử frontend
trước thời điểm triển khai metrics mới. Nếu No data, kiểm tra target thay vì
tăng tải hoặc thêm `or vector(0)` để che thiếu metric.

Tham chiếu: [Prometheus histograms](https://prometheus.io/docs/practices/histograms/),
[Node HTTP finish](https://nodejs.org/docs/latest-v24.x/api/http.html#event-finish_2).

### Panel scaling và cập nhật dashboard riêng

Ngay dưới ba biểu đồ CPU/lưu lượng là bốn panel scaling:

- **Số Pod mong muốn và sẵn sàng**: spec replicas và Available replicas của hai
  Deployment backend/frontend, thể hiện dạng bậc thang để thấy tăng/giảm.
- **Số worker Ready**: tổng node worker Ready theo Kubernetes, loại control plane
  kubeadm; không phải ASG desired hay số instance EC2 Running.
- **Pod Pending và chưa được schedule**: theo namespace coco/scaling-demo. Pending
  không tự chứng minh thiếu CPU/RAM; có thể do image, PVC hoặc placement, cần xem events.
- **CPU HPA hiện tại so với mục tiêu**: lấy CPU utilization từ HPA status và target
  từ HPA spec (hiện 60%), vẽ đường mục tiêu nét đứt màu cam. Không hardcode 60 vào
  query; nếu đổi HPA target, panel sẽ theo metric mới. Số CPU này có thể khác biểu
  đồ cAdvisor vì nguồn và cửa sổ lấy mẫu khác nhau.

Các panel dùng kube-state-metrics, không cần CloudWatch datasource hoặc sửa DB.
Namespace chưa có Pod hoặc HPA chưa có CPU metric có thể chưa xuất hiện series;
không thay missing metric bằng 0. Sau khi chạy k6, đối chiếu request → CPU HPA →
replicas → Pending/Ready worker, không mặc định cứ tăng request là EC2 phải tăng.

Sau khi sửa JSON dashboard, cập nhật riêng ConfigMap từ **local tại gốc repo**:

```sh
python3 -m json.tool k8s/monitoring/resources/dashboards/coco-application.json >/dev/null
python3 scripts/aws/run-dev-task.py dashboards
```

Lệnh đầu kiểm tra JSON cục bộ, lệnh sau gửi SSM command; dùng lệnh status được in
ra và đợi Success. Task chỉ cập nhật ConfigMap dashboard, không đổi Secret, PVC,
Helm release hoặc restart app/Grafana. Sidecar dashboard đang bật trong values sẽ
đồng bộ nội dung; refresh trình duyệt sau khi đồng bộ. Không cần build web.
Chưa tự chạy kiểm tra JSON, task SSM hoặc query live trong lần thêm biểu đồ này.

Mở `http://localhost:3002/d/coco-application`, giữ tunnel, chọn Last 1 hour và refresh
30s. Rate cần đủ mẫu scrape; worker/Pod mới có thể chưa hiện ngay. Nếu No data,
kiểm tra scrape/labels và nguồn cAdvisor, kube-state-metrics, node-exporter; không
coi thiếu metric là CPU bằng 0. Dashboard dùng $__rate_interval cho cửa sổ rate.

Chạy mỗi port-forward trong một terminal riêng; chỉ bind localhost:

```sh
kubectl --context coco-dev -n monitoring port-forward svc/monitoring-grafana 3002:80
kubectl --context coco-dev -n monitoring port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090
kubectl --context coco-dev -n monitoring port-forward svc/monitoring-kube-prometheus-alertmanager 9093:9093
```

Grafana `http://localhost:3002`, dashboard `Coco - Application`. Prometheus `http://localhost:9090/targets`: backend và hai probe phải UP. Kiểm tra query `probe_success` bằng 1; target UP chỉ chứng minh scrape được exporter, không chứng minh trang web khỏe. Truy cập frontend bằng trình duyệt để có lưu lượng đọc; rate/p95 có thể cần vài phút và chưa hiện khi chưa có request API. Không tạo đơn hàng thử trên DB thật chỉ để tạo metrics.

Alertmanager `http://localhost:9093`: kiểm tra receiver/route. Để tự gửi một email thử có tên rõ ràng (sau khi đã điền đúng người nhận):

```sh
curl --fail-with-body -X POST http://127.0.0.1:9093/api/v2/alerts -H 'Content-Type: application/json' --data '[{"labels":{"alertname":"CocoMonitoringEmailTest","severity":"info","namespace":"coco","cluster":"coco-dev"},"annotations":{"summary":"Manual monitoring SMTP test"}}]'
```

Đợi khoảng 30 giây theo `group_wait`, kiểm tra inbox/spam và log Alertmanager nếu chưa nhận. Alert thử tự hết hạn nếu không gửi lại. Chỉ coi SMTP đạt sau khi email thật đến nơi; HTTP 200 từ API chưa chứng minh đã gửi mail thành công.

Rule mặc định: backend mất metrics 5 phút; probe lỗi 3 phút; 5xx >5% trong 5 phút (ít nhất 20 request), giữ 5 phút; p95 >2 giây giữ 10 phút; restart >3 lần/15 phút. Điều chỉnh theo lưu lượng thực tế sau khi có baseline. Rule hạ tầng/PVC có sẵn trong chart.

Không expose `/metrics`, Grafana, Prometheus, Alertmanager hoặc blackbox ra ALB/Internet. Service metrics là nội bộ nhưng ứng dụng vẫn phục vụ cùng port; kiểm tra routing ALB/NodePort không cho public vào `/metrics` trước khi mở web. Các manifest này chưa thêm NetworkPolicy vì CNI hiện tại cần kiểm tra khả năng enforce trước.

## Prod sau khi dev đã đạt

Chuẩn bị CSI/IAM, certificate, capacity và Secret riêng trên context prod; review backup/HA trước khi sử dụng thật. Prod kế thừa dev rồi ghi đè dung lượng, retention và TLS; bắt buộc truyền cả hai file:

```sh
helm template monitoring prometheus-community/kube-prometheus-stack --version 93.7.0 --namespace monitoring -f k8s/monitoring/values-dev.yaml -f k8s/monitoring/values-prod.yaml > /tmp/coco-monitoring-prod.yaml
```

Chưa có lệnh apply prod trong giai đoạn dev này. Không dùng `values-prod.yaml` đơn lẻ.

Tham chiếu cấu hình: [chart 93.7.0](https://github.com/prometheus-community/helm-charts/tree/kube-prometheus-stack-93.7.0/charts/kube-prometheus-stack), [Alertmanager SMTP](https://prometheus.io/docs/alerting/latest/configuration/), [StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/).
