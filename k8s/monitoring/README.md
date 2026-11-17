# Chạy Prometheus và Grafana

Cần Helm, context Kubernetes đúng môi trường và node/network hoạt động. Đây là monitoring trong Kubernetes; Metrics Server phục vụ HPA là [add-on riêng](../metrics-server/README.md).

## Chuẩn bị Secret Grafana

Từ **gốc repo**, tạo namespace trên môi trường muốn dùng:

```sh
kubectl --context coco-dev create namespace monitoring --dry-run=client -o yaml | kubectl --context coco-dev apply -f -
```

Tạo Secret tên `grafana-admin` trong namespace `monitoring`, có hai key `admin-user` và `admin-password` theo values. Có thể dùng file cục bộ riêng `admin-user`, `admin-password` trong một thư mục tạm an toàn:

```sh
kubectl --context coco-dev -n monitoring create secret generic grafana-admin --from-file=admin-user=/DUONG_DAN_FILE_USERNAME --from-file=admin-password=/DUONG_DAN_FILE_PASSWORD
```

Điền đường dẫn thật trước khi chạy; nội dung file là giá trị đăng nhập, tránh newline cuối nếu không muốn newline trở thành một phần mật khẩu. Nếu Secret đã tồn tại, quản lý cập nhật qua quy trình Secret của bạn; lệnh create không ghi đè. Không đưa file mật khẩu vào repo. Prod cần Secret riêng trên context `coco-prod`.

## Cài monitoring

```sh
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm --kube-context coco-dev upgrade --install monitoring prometheus-community/kube-prometheus-stack --namespace monitoring -f k8s/monitoring/values-dev.yaml
```

Cho prod, chuẩn bị namespace/Secret trên prod rồi chạy:

```sh
helm --kube-context coco-prod upgrade --install monitoring prometheus-community/kube-prometheus-stack --namespace monitoring -f k8s/monitoring/values-prod.yaml
```

Kiểm tra chart version phù hợp với Kubernetes 1.34 và cố định bản đã kiểm thử bằng `--version` trước khi dùng cho prod.

## Kiểm tra và mở Grafana

```sh
kubectl --context coco-dev -n monitoring get pods,svc
kubectl --context coco-dev -n monitoring port-forward svc/monitoring-grafana 3001:80
```

Mở `http://localhost:3001`, đăng nhập bằng Secret đã chuẩn bị. Đổi context sang `coco-prod` để xem prod.

Cả hai values hiện dùng storage tạm: Prometheus/Grafana có thể mất dữ liệu khi Pod được tạo lại. `retention: 3d/7d` không làm dữ liệu trở nên bền vững. Muốn lưu bền cần cấu hình CSI/StorageClass/PVC trước; README này không thay đổi storage hoặc thêm tài nguyên AWS.
