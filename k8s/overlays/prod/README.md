# Chạy ứng dụng Kubernetes prod

Các lệnh chạy từ **gốc repo** với kubeconfig context `coco-prod` đã được cấu hình và có đường mạng tới Kubernetes API private.

1. Hoàn thành [các điều kiện trong README Kubernetes](../../README.md): node Ready, CNI/ECR authentication hoạt động.
2. Thay `ACCOUNT_ID` trong `kustomization.yaml`, kiểm tra repository `ecommerce/prod/frontend`, `ecommerce/prod/backend` và tag `v1.0.0` đã có trong ECR.
3. Cài [Metrics Server](../../metrics-server/README.md) cho đúng môi trường. Prod cần kubelet serving certificate hợp lệ trước.
4. Tạo Secret `coco-backend-secret` trong namespace `coco` bằng thông tin RDS của prod. Xem cách tạo trong README chung.
5. Nếu Deployment đang tồn tại, làm bước chuyển quyền replica sang HPA trong README chung trước khi apply.

Render cục bộ, chưa thay đổi cluster:

```sh
kubectl kustomize k8s/overlays/prod
```

Triển khai lên cluster thật:

```sh
kubectl --context coco-prod cluster-info
kubectl --context coco-prod apply -k k8s/overlays/prod
kubectl --context coco-prod -n coco rollout status deployment/coco-frontend
kubectl --context coco-prod -n coco rollout status deployment/coco-backend
kubectl --context coco-prod -n coco get pods,svc,hpa,pdb
kubectl --context coco-prod -n coco top pods
```

Frontend HPA 2–4 Pod; backend HPA 2–10 Pod; cả hai CPU target 60%, cửa sổ ổn định giảm 300 giây. Service NodePort frontend 30080/backend 30081. Truy cập ứng dụng qua ALB của prod.

Nếu có lỗi, xem `kubectl --context coco-prod -n coco describe pod TEN_POD` và `kubectl --context coco-prod -n coco logs deployment/coco-backend --tail=100`. Không dán log chứa dữ liệu nhạy cảm vào báo cáo công khai.
