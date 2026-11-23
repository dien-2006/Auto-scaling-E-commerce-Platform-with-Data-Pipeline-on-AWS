#!/usr/bin/env bash
# Run on the affected EC2 through SSM, not on the developer workstation.
# Only repairs the known apt awscli failure before kubeadm init/join.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export PATH="/usr/local/bin:$PATH"

if [[ "$EUID" -ne 0 ]]; then
  printf 'Chạy script bằng sudo bash trên EC2 bị lỗi.\n' >&2
  exit 1
fi

COCO_ORIGINAL_BOOTSTRAP=/var/lib/cloud/instance/scripts/part-001
if [[ ! -f "$COCO_ORIGINAL_BOOTSTRAP" ]] || \
   ! grep -Fq 'retry apt-get install -y ca-certificates curl gnupg unzip containerd awscli' \
     "$COCO_ORIGINAL_BOOTSTRAP"; then
  printf 'Không tìm thấy đúng bootstrap bị lỗi awscli. Dừng để kiểm tra.\n' >&2
  exit 1
fi

if [[ -f /etc/kubernetes/admin.conf || -f /etc/kubernetes/kubelet.conf || \
      -f /etc/kubernetes/manifests/kube-apiserver.yaml ]]; then
  printf 'Kubernetes đã init/join hoặc có cấu hình một phần. Không chạy lại bootstrap.\n' >&2
  exit 1
fi

if [[ "$(systemctl show cloud-final.service --property=ActiveState --value)" == activating ]]; then
  printf 'Cloud-init vẫn đang chạy. Đợi hoàn tất trước khi sửa.\n' >&2
  exit 1
fi

apt-get update
apt-get install -y ca-certificates curl unzip
case "$(uname -m)" in
  x86_64) COCO_AWS_CLI_ARCH=x86_64 ;;
  aarch64) COCO_AWS_CLI_ARCH=aarch64 ;;
  *) printf 'Kiến trúc chưa hỗ trợ.\n' >&2; exit 1 ;;
esac

COCO_REPAIR_DIRECTORY=$(mktemp -d /tmp/coco-bootstrap-repair.XXXXXX)
if ! command -v aws >/dev/null 2>&1; then
  curl -fsSL --retry 5 \
    "https://awscli.amazonaws.com/awscli-exe-linux-$COCO_AWS_CLI_ARCH.zip" \
    -o "$COCO_REPAIR_DIRECTORY/awscliv2.zip"
  unzip -q "$COCO_REPAIR_DIRECTORY/awscliv2.zip" -d "$COCO_REPAIR_DIRECTORY"
  "$COCO_REPAIR_DIRECTORY/aws/install" --update
fi
aws --version

# Preserve the original user-data script. Retry a copy with only the bad apt item removed.
sed 's/retry apt-get install -y ca-certificates curl gnupg unzip containerd awscli/retry apt-get install -y ca-certificates curl gnupg unzip containerd/' \
  "$COCO_ORIGINAL_BOOTSTRAP" > "$COCO_REPAIR_DIRECTORY/retry-bootstrap.sh"

printf 'Chạy bản bootstrap đã bỏ gói apt awscli; log: /var/log/coco-bootstrap-repair.log\n'
bash "$COCO_REPAIR_DIRECTORY/retry-bootstrap.sh" 2>&1 | tee /var/log/coco-bootstrap-repair.log
printf 'Bootstrap chạy lại thành công. Cloud-init vẫn có thể giữ trạng thái lỗi cũ.\n'
