#!/usr/bin/env bash
# Invoked by the owner-run SSM task, as root on the dev control plane.
set -euo pipefail
umask 077
export KUBECONFIG=/etc/kubernetes/admin.conf
COCO_MONITORING_DIR="${1:?Supply the private monitoring task directory}"
kubectl get csidriver ebs.csi.aws.com >/dev/null
kubectl get storageclass coco-monitoring-gp3 >/dev/null
kubectl -n kube-system rollout status deployment/ebs-csi-controller --timeout=300s
kubectl -n kube-system rollout status daemonset/ebs-csi-node --timeout=300s
kubectl get namespace coco >/dev/null

if ! command -v helm >/dev/null; then
  curl -fsSL --retry 5 https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 \
    -o "$COCO_MONITORING_DIR/get-helm-3.sh"
  bash "$COCO_MONITORING_DIR/get-helm-3.sh" --version v3.22.1
fi
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
aws ssm get-parameter --region ap-southeast-1 \
  --name /ecommerce/dev/monitoring/secrets --with-decryption \
  --query Parameter.Value --output text > "$COCO_MONITORING_DIR/secrets.json"
python3 - "$COCO_MONITORING_DIR/secrets.json" <<'COCO_MONITORING_SECRETS'
import json
from pathlib import Path
import subprocess
import sys

values = json.loads(Path(sys.argv[1]).read_text())
expected = {'alertmanager.yaml', 'smtp-password', 'grafana-user', 'grafana-password'}
if set(values) != expected or any(not isinstance(v, str) or not v for v in values.values()):
    raise SystemExit('Unexpected monitoring secret bundle; no Secrets updated')
for name, data in (
    ('grafana-admin', {'admin-user': values['grafana-user'], 'admin-password': values['grafana-password']}),
    ('alertmanager-smtp-auth', {'password': values['smtp-password']}),
    ('alertmanager-smtp', {'alertmanager.yaml': values['alertmanager.yaml']}),
):
    resource = {'apiVersion': 'v1', 'kind': 'Secret', 'type': 'Opaque',
                'metadata': {'name': name, 'namespace': 'monitoring'}, 'stringData': data}
    # Capture API failures too, so credential payloads cannot enter SSM output.
    result = subprocess.run(['kubectl', 'apply', '-f', '-'], input=json.dumps(resource),
                            capture_output=True, text=True)
    if result.returncode:
        raise SystemExit('Could not configure monitoring Secret: ' + name)
    print('Configured Secret: ' + name)
COCO_MONITORING_SECRETS

# Helm handles installation ordering, CRDs and admission hooks for this chart.
# No --atomic/uninstall fallback: failed installation must not delete PVCs.
helm upgrade --install monitoring kube-prometheus-stack \
  --repo https://prometheus-community.github.io/helm-charts \
  --version 93.7.0 --namespace monitoring \
  -f "$COCO_MONITORING_DIR/values-dev.yaml" --wait --timeout 15m
kubectl wait --for=condition=Established \
  crd/servicemonitors.monitoring.coreos.com crd/probes.monitoring.coreos.com \
  crd/prometheusrules.monitoring.coreos.com --timeout=180s
kubectl apply --dry-run=server -f "$COCO_MONITORING_DIR/resources.yaml"
kubectl apply -f "$COCO_MONITORING_DIR/resources.yaml"
kubectl -n monitoring rollout status deployment/coco-blackbox --timeout=300s
kubectl -n monitoring rollout status deployment/monitoring-grafana --timeout=600s
for COCO_STATEFULSET in prometheus-monitoring-kube-prometheus-prometheus alertmanager-monitoring-kube-prometheus-alertmanager; do
  kubectl -n monitoring wait --for=create "statefulset/$COCO_STATEFULSET" --timeout=300s
  kubectl -n monitoring rollout status "statefulset/$COCO_STATEFULSET" --timeout=600s
done
kubectl -n monitoring get pods,pvc,svc
kubectl -n monitoring get servicemonitor,probe,prometheusrule
echo 'Monitoring resources ready. Verify Prometheus targets, dashboard and SMTP delivery separately.'
