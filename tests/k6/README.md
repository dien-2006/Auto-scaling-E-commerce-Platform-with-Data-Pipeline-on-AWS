# k6 qua cùng URL web

## Demo HTTP cho HPA/worker dev

`web-scaling.js` chỉ dùng GET `/`, `/health/live` và `/api/v1/products`, đi qua
ALB → Next → backend; catalog dùng transaction read-only trong backend. Không
đăng nhập, tạo user/order, gửi OTP hay thay đổi bảng/dữ liệu DB. Script smoke cũ
bên dưới giữ nguyên để kiểm tra CSRF/auth, không dùng làm bài tải thuần GET.

Từ gốc repo **trên local**, chủ dự án chạy:

```sh
bash -n scripts/aws/demo-k6-dev.sh
bash scripts/aws/demo-k6-dev.sh smoke
```

Chỉ tiếp tục khi preflight và smoke qua. Wrapper kiểm tra AWS account, lấy đúng
ALB dev từ Terraform output, dùng k6 local nếu đã cài hoặc Docker image đã ghim
digest của harness hiện hữu. Không cần cài k6 lên EC2/control plane. Docker daemon
phải hoạt động nếu dùng fallback; lần đầu có thể tải image.

Nếu pause demo trước đó còn chạy, dừng và chờ SSM command Success trước khi thử
HTTP, để không nhầm worker tăng do request tài nguyên giả lập với HPA:

```sh
python3 scripts/aws/run-dev-task.py scaling-demo-stop
```

Chỉ chạy lệnh stop nếu đã tạo scaling-demo; nếu chưa tạo thì bỏ qua. Đây không phải
lệnh dừng k6 và không thay replica ứng dụng.

Khi smoke PASS, chủ động tạo tải:

```sh
bash scripts/aws/demo-k6-dev.sh scale
```

Mặc định ramp 0→5 trong 30s, 5→20 trong 1m, lên 50 VUs trong 2m, giữ 10m, giảm về
0 trong 1m; thêm tối đa 30s cho iteration kết thúc. VU là người dùng ảo đồng thời,
không phải request/giây. Mỗi iteration gồm hai GET tuần tự và nghỉ 0,5s. Thời gian
thực tế/throughput phụ thuộc latency. Đây là k6 HTTP, không chạy JavaScript của
trình duyệt hoặc tự tải toàn bộ ảnh/S3/CSS như browser.

Sau khi xem kết quả/CPU, có thể chủ động đổi tải có giới hạn:

```sh
PEAK_VUS=100 HOLD_SECONDS=600 bash scripts/aws/demo-k6-dev.sh scale
```

Giới hạn 1–200 VUs, giữ 60–1200s. Không tự tăng tải hoặc thay HPA/ASG để ép ra kết
quả. Có phí request/ALB/RDS và EC2/EBS nếu ASG tăng worker. Ctrl+C dừng phát tải
k6; Pod/worker có thể vẫn cao cho đến khi hết stabilization hoặc còn workload khác.
Lệnh k6 thất bại không tự dừng/tắt EC2 hoặc deployment.

## Quan sát và nghiệm thu

Giữ tunnel Grafana đang mở; chọn Last 1 hour, refresh 30s. Dashboard
`Coco - Application`: request/s, p95, lỗi 5xx, CPU/memory và HPA desired/max.
Để xem replica thật trong Explore → Prometheus → Code → Range:

```promql
sum by (deployment) (kube_deployment_status_replicas_available{namespace="coco",deployment=~"coco-backend|coco-frontend"})
```

Tổng node Ready (bao gồm một control plane; 3→5 tổng node tương ứng 2→4 worker):

```promql
sum(kube_node_status_condition{condition="Ready",status="true"})
```

Hoặc mở phiên SSM control plane ở terminal khác và theo dõi:

```sh
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf -n coco get hpa -w
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf -n coco get pods -o wide -w
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes -w
```

Chạy từng lệnh watch ở terminal riêng, hoặc Ctrl+C chuyển lệnh; Ctrl+C watch không
dừng workload. Script in UTC start/finish để đối chiếu đúng khoảng trên Grafana.
Không dùng port-forward Grafana làm BASE_URL của k6.

Chỉ kết luận HPA khi CPU/request vượt mục tiêu và replicas tự tăng, sau tải tự giảm.
Chỉ kết luận worker scaling nếu Pod Pending vì thiếu tài nguyên khiến ASG tăng,
worker mới Ready và worker dư tự rút sau khi bỏ tải. Nếu 2 worker còn đủ chỗ thì
HPA có thể tăng Pod mà ASG vẫn giữ 2; đó là kết quả hợp lệ, không ép tăng node.
Theo dõi scale-down 10–20 phút hoặc lâu hơn khi còn PDB/protection/workload khác.

Ngưỡng demo: checks >99%, lỗi HTTP <5%, p95 <5s. Nếu fail/5xx nhiều, xem p95,
CPU/DB/pool/events; không coi test đạt chỉ vì Pod tăng. Đây không phải chứng nhận
capacity/SLO production. Chưa có lượt chạy AWS của bài demo mới được xác nhận;
harness k6 cô lập từng PASS bên dưới không chứng minh bài tải AWS hiện tại.

Tham khảo [k6 ramping-vus](https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/ramping-vus/).

## Smoke CSRF/auth hiện hữu

Xem [schema25/CRUD/k6](../../docs/schema25-crud-k6.md) cho kiến trúc AWS, cấu hình origin, kết quả và giới hạn.

```powershell
k6 run -e BASE_URL=https://YOUR_STAGING_DOMAIN tests/k6/web-smoke.js
```

Mặc định1VU/5iterations,25checks; không đăng ký tài khoản, đặt hàng hoặc thay đổi tồn. PubliccatalogGET/cookie-CSRF loginvalidation/guestAdmin denial được kiểm. K6 quản lý cookies theoVU; APIprivate không có đường bypass. BASE_URL bắt buộc, root origin không chứacredential/path/query. PUBLIC_ORIGIN mặc định bằngBASE_URL; override chỉ khi testcontainer dùng host.docker.internal để gọi app có origin riêng được cấu hình rõ ràng.

Load tùy chọn: `-e TEST_ENV=staging -e VUS=5 -e ITERATIONS=50`, chỉ môi trường test được chỉ định; các giới hạn không phải chứng nhận capacity/AutoScaling. Không dùng chính sách này để tự chạy stress lên DB nghiệp vụ. Không cần sửa CORS để chạy k6HTTP.

Smoke cô lập trước đây đã chạyPASS bằng `E2E_SUITE=k6` trên tests/e2e/run.py, Dockerk6v2.4.0 digestpin, Nextproduction/FastAPI/PostgreSQL16SQL25bảng test riêng. Kết quả đó không chứng minh bài tải mới trên AWS hiện tại; chạy dev theo phần đầu tài liệu. LAN/localhost không phảiURLpublic theo sơ đồ. Các bài k6 không tự thay AWSresource/Terraform/firewall.
