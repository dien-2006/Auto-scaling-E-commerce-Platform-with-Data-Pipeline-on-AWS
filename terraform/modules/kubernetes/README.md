# Bootstrap kubeadm trên EC2

Module dùng chung cho dev/prod. Chỉnh sửa mã không tự chạy lệnh trên AWS.

## Các thay đổi xử lý lỗi bootstrap

- Cài AWS CLI bằng bộ cài chính thức, bỏ gói apt `awscli` đã gây lỗi trên Ubuntu 24.04.
- Khởi tạo Kubernetes bằng đúng phiên bản kubeadm được cài từ minor version đã chọn.
- Control plane cài Flannel v0.27.4, dùng Pod CIDR của module; VXLAN khớp cổng UDP
  8472 của security module. Chờ Flannel/CoreDNS sẵn sàng, timeout báo lỗi rõ ràng.
- Worker chỉ nhận join command trỏ tới IP control plane do Terraform vừa tạo.
  Đọc lại Parameter Store và thử lại khi token cũ hoặc API chưa sẵn sàng; không tự reset
  node đã có kubelet.conf. Lệnh join có timeout và vòng chờ có giới hạn.
- Root dev/prod chờ network module hoàn tất, gồm NAT/routes, trước khi tạo EC2.

Flannel là CNI duy nhất của cấu hình này. Không cài thêm vào cluster đã có CNI khác.
Node cần truy cập được registry Kubernetes/GHCR, repository apt, GitHub và AWS APIs.
Tham chiếu: [Flannel đã ghim phiên bản](https://github.com/flannel-io/flannel/blob/v0.27.4/Documentation/kube-flannel.yml),
[kubeadm và Pod network](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/).

## Máy hiện có và máy mới

Control plane giữ `user_data_replace_on_change = false`; không tự thay máy chỉ vì
đổi script. Apply thay user-data không chạy lại bootstrap trong hệ điều hành hiện có
và có thể stop/start EC2. Đổi launch template cũng không tự sửa các worker đang chạy.
Vì vậy không dùng apply như lệnh chữa cloud-init trên máy cũ.

Máy lỗi apt hiện tại: dùng `scripts/aws/repair-bootstrap-awscli.sh` theo hướng dẫn
scripts. Script đó sửa bản user-data cũ trên máy, chưa bổ sung Flannel từ template mới.
Sau khi control plane init thành công, kiểm tra cluster có CNI nào trước. Nếu chưa có
CNI và Pod CIDR đúng `10.244.0.0/16`, người dùng có thể cài bản tương ứng trong phiên SSM:

```sh
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get daemonsets -A
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes -o wide
```

Chưa cài CNI nếu chưa xác nhận hai điều kiện trên. Mọi sửa chữa hiện có và thay thế EC2
cần do chủ dự án chạy theo kế hoạch riêng; không destroy DB hoặc bucket để sửa cluster.

## Kiểm tra trước và sau triển khai

Trên local, chỉ kiểm tra mã Terraform:

```sh
terraform -chdir=terraform/environments/dev validate
terraform -chdir=terraform/environments/dev test
terraform -chdir=terraform/environments/prod validate
terraform -chdir=terraform/environments/prod test
```

Test mock/render không thay thế kiểm tra trên EC2 thật. Sau bootstrap, sao chép
`scripts/k8s/check-cluster.sh` lên control plane qua quy trình SSM đang dùng, rồi tự chạy
`sudo bash /DUONG_DAN/check-cluster.sh`. Mặc định yêu cầu tối thiểu 3 node đăng ký, tất cả
Ready, Flannel/CoreDNS rollout thành công. Nếu chủ động đổi số node, dùng
`sudo COCO_MINIMUM_NODES=2 bash /DUONG_DAN/check-cluster.sh` với số lượng đã chấp nhận.

Các thay đổi chưa được chạy validate/test hoặc kiểm chứng trên AWS trong phiên sửa này.
Đã bổ sung ECR credential provider cho first boot và script sửa worker hiện hữu;
adapter v1 trong repo dùng AWS CLI/node role, không phụ thuộc binary staging bị hết hạn.
Cần kiểm tra pull image thật sau khi cài. Bootstrap hiện đã lấy provider ID, region,
AZ và instance type từ IMDSv2 cho node mới. Node cũ dùng script
`scripts/aws/repair-node-identity.py` (preview trước, `--submit` do chủ dự án chạy).
Chưa tự cấu hình EBS CSI/IAM, Cluster Autoscaler,
kubelet serving certificate prod, runtime Secret hoặc triển khai ứng dụng. Cần hoàn
thiện và kiểm chứng các phần đó trước khi gọi là quy trình dựng lại toàn hệ thống.
