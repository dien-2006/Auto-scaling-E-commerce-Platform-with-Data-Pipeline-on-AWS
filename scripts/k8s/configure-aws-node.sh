#!/usr/bin/env bash
# First-boot kubelet identity. Reads host IMDSv2; never calls the EC2 write APIs.
set -euo pipefail
[[ "$EUID" == 0 ]] || { echo 'Run as root on an EC2 Kubernetes node' >&2; exit 1; }
COCO_IMDS=http://169.254.169.254/latest
COCO_IMDS_TOKEN="$(curl --noproxy '*' -fsS --connect-timeout 3 --max-time 15 --retry 4 \
  -X PUT "$COCO_IMDS/api/token" -H 'X-aws-ec2-metadata-token-ttl-seconds: 300')"
metadata() {
  curl --noproxy '*' -fsS --connect-timeout 3 --max-time 15 --retry 4 \
    -H "X-aws-ec2-metadata-token: $COCO_IMDS_TOKEN" "$COCO_IMDS/meta-data/$1"
}
COCO_INSTANCE_ID="$(metadata instance-id)"
COCO_AZ="$(metadata placement/availability-zone)"
COCO_REGION="$(metadata placement/region)"
COCO_INSTANCE_TYPE="$(metadata instance-type)"
unset COCO_IMDS_TOKEN
[[ "$COCO_INSTANCE_ID" =~ ^i-[0-9a-f]{17}$ &&
   "$COCO_REGION" =~ ^[a-z]{2}(-[a-z]+)+-[0-9]+$ &&
   "$COCO_AZ" == "$COCO_REGION"[a-z] &&
   "$COCO_INSTANCE_TYPE" =~ ^[a-z0-9]+\.[a-z0-9]+$ ]] || {
  echo 'Unexpected EC2 metadata; refusing to configure kubelet identity' >&2
  exit 1
}
install -d -m 0755 /etc/kubernetes /etc/systemd/system/kubelet.service.d
cat >/etc/kubernetes/coco-aws-node.env <<EOF
COCO_AWS_NODE_ARGS=--provider-id=aws:///$COCO_AZ/$COCO_INSTANCE_ID --node-labels=topology.kubernetes.io/region=$COCO_REGION,topology.kubernetes.io/zone=$COCO_AZ,node.kubernetes.io/instance-type=$COCO_INSTANCE_TYPE
EOF
cat >/etc/systemd/system/kubelet.service.d/25-coco-aws-node.conf <<'EOF'
[Service]
EnvironmentFile=/etc/kubernetes/coco-aws-node.env
EOF
systemctl daemon-reload
echo "Kubelet registration configured for $COCO_INSTANCE_ID in $COCO_AZ"
