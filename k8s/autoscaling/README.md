# Chạy Cluster Autoscaler

HPA tăng/giảm Pod. Cluster Autoscaler tăng/giảm worker EC2 khi Pod không đủ chỗ chạy hoặc node dư tài nguyên. Control plane vẫn một máy.

| Môi trường | Context | Values | Cluster/ASG discovery tag |
| --- | --- | --- | --- |
| Dev | `coco-dev` | `values-dev.yaml` | `ecommerce-dev-k8s` |
| Prod | `coco-prod` | `values-prod.yaml` | `ecommerce-prod-k8s` |

## Điều kiện trước khi cài

- Worker ASG do Terraform tạo: min 1, ban đầu 2, max 4.
- Identity của Autoscaler có quyền đọc EC2/ASG và thay đổi đúng worker ASG của môi trường đó. Terraform hiện chưa cấp đủ các quyền này.
- Node có AWS provider ID để liên kết với instance EC2. Bootstrap hiện chưa cấu hình rõ phần này.
- Pod lấy được credential AWS; kiểm tra IMDSv2/identity thay vì mặc định cho rằng EC2 role luôn truy cập được từ Pod.
- Node/network, Metrics Server và HPA ứng dụng đã hoạt động.

Không chạy bước cài dưới đây để thay thế các điều kiện còn thiếu. Xem [hướng dẫn chính](../README.md#3-install-cluster-autoscaler-via-helm).

## Cài khi đã đủ điều kiện

Từ **gốc repo**:

```sh
helm repo add autoscaler https://kubernetes.github.io/autoscaler
helm repo update
helm --kube-context coco-dev upgrade --install cluster-autoscaler autoscaler/cluster-autoscaler --namespace kube-system -f k8s/autoscaling/values-dev.yaml --set image.tag=v1.34.0
```

Đối với prod:

```sh
helm --kube-context coco-prod upgrade --install cluster-autoscaler autoscaler/cluster-autoscaler --namespace kube-system -f k8s/autoscaling/values-prod.yaml --set image.tag=v1.34.0
```

Image phải cùng minor version với Kubernetes 1.34. Kiểm tra chart tương thích và cố định chart version đã được thử nghiệm bằng `--version` trước khi dùng cho prod.

## Kiểm tra

```sh
kubectl --context coco-dev -n kube-system get deploy -l app.kubernetes.io/instance=cluster-autoscaler
kubectl --context coco-dev -n kube-system logs -l app.kubernetes.io/instance=cluster-autoscaler --all-containers=true --tail=100
kubectl --context coco-dev -n coco get hpa -w
```

Đổi context sang `coco-prod` để kiểm tra prod. Tạo tải khiến HPA tăng Pod; chỉ khi có Pod Pending do thiếu tài nguyên, Autoscaler mới có lý do tăng worker. ASG tối đa bốn worker không có nghĩa cứ có request là tăng ngay lên bốn.
