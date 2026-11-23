#!/usr/bin/env bash
# Run on the control-plane EC2 through SSM: sudo bash /path/to/check-cluster.sh
# Readiness checks only; no apply, SQL, resets, or resource deletion.
set -euo pipefail
export KUBECONFIG=/etc/kubernetes/admin.conf

if [[ ! -r "$KUBECONFIG" ]]; then
  printf 'Chạy trên control plane bằng sudo; thiếu quyền đọc admin.conf.\n' >&2
  exit 1
fi
if ! command -v kubectl >/dev/null 2>&1; then
  printf 'kubectl chưa được cài trên máy này.\n' >&2
  exit 1
fi

COCO_MINIMUM_NODES="${COCO_MINIMUM_NODES:-3}"
if [[ ! "$COCO_MINIMUM_NODES" =~ ^[1-9][0-9]*$ ]]; then
  printf 'COCO_MINIMUM_NODES phải là số nguyên dương.\n' >&2
  exit 1
fi

COCO_DEADLINE=$((SECONDS + 600))
while true; do
  COCO_NODE_NAMES="$(kubectl get nodes -o name)"
  COCO_NODE_COUNT=0
  while IFS= read -r COCO_NODE_NAME; do
    if [[ -n "$COCO_NODE_NAME" ]]; then
      COCO_NODE_COUNT=$((COCO_NODE_COUNT + 1))
    fi
  done <<< "$COCO_NODE_NAMES"
  if (( COCO_NODE_COUNT >= COCO_MINIMUM_NODES )); then
    break
  fi
  if (( SECONDS >= COCO_DEADLINE )); then
    printf 'Chỉ có %s node đăng ký, cần ít nhất %s.\n' \
      "$COCO_NODE_COUNT" "$COCO_MINIMUM_NODES" >&2
    kubectl get nodes -o wide
    exit 1
  fi
  printf 'Đang chờ node đăng ký: %s/%s\n' "$COCO_NODE_COUNT" "$COCO_MINIMUM_NODES"
  sleep 10
done

kubectl wait --for=condition=Ready nodes --all --timeout=600s
kubectl -n kube-flannel rollout status daemonset/kube-flannel-ds --timeout=600s
kubectl -n kube-system rollout status deployment/coredns --timeout=600s
kubectl get nodes -o wide
kubectl -n kube-system get pods -o wide
kubectl -n kube-flannel get pods -o wide
printf 'Đạt kiểm tra node/CNI/CoreDNS; chưa kiểm chứng web, ECR, CSI hoặc DB.\n'
