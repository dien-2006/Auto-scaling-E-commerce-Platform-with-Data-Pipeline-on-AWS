# Manifest ứng dụng dùng chung

`frontend/` và `backend/` định nghĩa Deployment, Service NodePort, HPA và PodDisruptionBudget. Namespace ứng dụng là `coco`.

Không triển khai trực tiếp base: image mặc định chưa có ECR URI và base không tạo backend ConfigMap. Hãy chạy [overlay dev](../overlays/dev/README.md) hoặc [overlay prod](../overlays/prod/README.md).

Frontend dùng port 80, NodePort 30080, CPU request 100m, HPA 2–4. Backend dùng port 3000, NodePort 30081, CPU request 300m, HPA 2–10. Cần xác nhận các port và endpoint health check khớp image ứng dụng thực tế.

HPA quản lý số replica nên Deployment không khai báo `spec.replicas`. Không thêm trường này chỉ để ép số Pod; điều chỉnh giới hạn trong HPA nếu có nhu cầu được xác nhận.
