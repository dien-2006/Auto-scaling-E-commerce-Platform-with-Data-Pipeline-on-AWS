#!/usr/bin/env bash
# Owner-run through SSM on the control plane. No SQL, resets or instance refresh.
set -euo pipefail
umask 077
COCO_SCALING_DIR="${1:?Supply the prepared temporary directory}"
export KUBECONFIG=/etc/kubernetes/admin.conf
kubectl get --raw=/readyz >/dev/null
kubectl wait --for=condition=Ready nodes --all --timeout=600s
kubectl version -o json | python3 -c '
import json, sys
v = json.load(sys.stdin)["serverVersion"]
if v["major"] != "1" or v["minor"].rstrip("+") != "34":
    sys.exit("This autoscaler release requires Kubernetes minor 1.34")
'
# Fail rather than competing with another Helm/direct autoscaler deployment.
kubectl get deployments -A -o json | python3 -c '
import json, sys
for d in json.load(sys.stdin)["items"]:
    if any("cluster-autoscaler" in c.get("image", "") for c in d["spec"]["template"]["spec"]["containers"]):
        if (d["metadata"]["namespace"], d["metadata"]["name"]) != ("kube-system", "cluster-autoscaler") or d["metadata"].get("labels", {}).get("coco.dev/managed-by") != "scripts":
            sys.exit("An existing autoscaler installation requires an explicit migration")
'
aws sts get-caller-identity --region ap-southeast-1 --query Account --output text |
  python3 -c 'import sys; sys.exit(0 if sys.stdin.read().strip() == "858525799322" else "Wrong AWS account")'
cat >"$COCO_SCALING_DIR/aws-config" <<'EOF'
[profile coco-cluster-autoscaler]
role_arn = arn:aws:iam::858525799322:role/ecommerce-dev-cluster-autoscaler
credential_source = Ec2InstanceMetadata
region = ap-southeast-1
EOF
# This tests the assumed role, not the broader credentials of the local operator.
COCO_ROLE_READY=false
for COCO_ROLE_ATTEMPT in {1..12}; do
  if AWS_CONFIG_FILE="$COCO_SCALING_DIR/aws-config" AWS_PROFILE=coco-cluster-autoscaler \
      aws autoscaling describe-auto-scaling-groups --region ap-southeast-1 \
      --auto-scaling-group-names ecommerce-dev-worker-asg --output json --no-cli-pager \
      >"$COCO_SCALING_DIR/group.json"; then
    COCO_ROLE_READY=true
    break
  fi
  sleep 5
done
[[ "$COCO_ROLE_READY" == true ]] || { echo 'Autoscaler role is not ready' >&2; exit 1; }
python3 - "$COCO_SCALING_DIR/group.json" <<'PY'
import json, sys
groups = json.load(open(sys.argv[1]))["AutoScalingGroups"]
if len(groups) != 1 or groups[0]["MinSize"] != 2 or groups[0]["MaxSize"] != 4:
    sys.exit("Expected the reviewed 2-4 dev worker ASG")
PY
# Joining future workers must keep working after today's token expires.
test -x /usr/local/sbin/coco-publish-join.sh
systemctl is-active --quiet coco-join-publisher.timer
install -d -m 0755 /etc/systemd/system/coco-join-publisher.service.d
cat >/etc/systemd/system/coco-join-publisher.service.d/retry.conf <<'EOF'
[Unit]
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=0
[Service]
Restart=on-failure
RestartSec=30
EOF
systemctl daemon-reload
systemctl start coco-join-publisher.service
systemctl is-failed --quiet coco-join-publisher.service && exit 1
# The multi-resource manifest contains no bare Pod/test hook; server dry-run does
# not require the ServiceAccount to have been persisted before the Deployment.
kubectl apply --dry-run=server -f "$COCO_SCALING_DIR/cluster-autoscaler.yaml"
python3 "$COCO_SCALING_DIR/protect-baseline.py" "$COCO_SCALING_DIR/group.json"
kubectl apply -f "$COCO_SCALING_DIR/cluster-autoscaler.yaml"
kubectl -n kube-system rollout status deployment/cluster-autoscaler --timeout=600s
COCO_STATUS_READY=false
for COCO_STATUS_ATTEMPT in {1..30}; do
  if kubectl -n kube-system get configmap cluster-autoscaler-status -o json 2>/dev/null |
      python3 -c 'import json, sys; sys.exit(0 if "ecommerce-dev-worker-asg" in json.load(sys.stdin).get("data", {}).get("status", "") else 1)' 2>/dev/null; then
    COCO_STATUS_READY=true
    break
  fi
  sleep 6
done
if [[ "$COCO_STATUS_READY" != true ]]; then
  kubectl -n kube-system logs deployment/cluster-autoscaler --tail=100
  echo 'Controller has not published status for the dev ASG; inspect the logs before testing scale-out.' >&2
  exit 1
fi
kubectl -n kube-system get deployment cluster-autoscaler
kubectl -n kube-system get configmap cluster-autoscaler-status -o yaml
kubectl -n kube-system logs deployment/cluster-autoscaler --tail=80
echo 'Controller rollout completed. Verify status ConfigMap and an actual scale-out/scale-in test separately.'
