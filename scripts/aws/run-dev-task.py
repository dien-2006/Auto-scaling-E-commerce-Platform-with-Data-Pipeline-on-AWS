#!/usr/bin/env python3
"""Owner-run SSM tasks. No SQL, table creation, migrations, or resource deletion."""

import argparse
import base64
import gzip
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
REGION = "ap-southeast-1"


def aws(*args):
    result = subprocess.run(
        ["aws", *args, "--region", REGION, "--output", "json", "--no-cli-pager"],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def instances(role):
    result = aws("ec2", "describe-instances", "--filters",
                 "Name=tag:Name,Values=ecommerce-dev-" + role,
                 "Name=instance-state-name,Values=running")
    return [instance["InstanceId"] for reservation in result["Reservations"]
            for instance in reservation["Instances"]]


def packed(path):
    return base64.b64encode(gzip.compress(path.read_bytes(), mtime=0)).decode()


def extract(path, target):
    return "printf '%s' '" + packed(path) + "' | base64 -d | gzip -d > " + target + "\n"


def submit(ids, script, timeout=1800):
    if not ids or len(script.encode()) > 48000:
        raise ValueError("No nodes found or task payload is too large")
    result = aws(
        "ssm", "send-command", "--instance-ids", *ids,
        "--document-name", "AWS-RunShellScript",
        "--max-concurrency", "1", "--max-errors", "0",
        "--parameters", json.dumps({
            "commands": ["bash <<'COCO_DEV_TASK'\nset -euo pipefail\numask 077\n" + script + "\nCOCO_DEV_TASK"],
            "executionTimeout": [str(timeout)],
        }),
    )
    print("Command ID: " + result["Command"]["CommandId"])
    print("Check with: python3 scripts/aws/run-dev-task.py status " + result["Command"]["CommandId"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task", choices=["ecr", "csi", "monitoring", "frontend-image", "http-metrics", "dashboards", "autoscaling", "scaling-status", "scaling-demo", "scaling-demo-stop", "deploy", "status"])
    parser.add_argument("command_id", nargs="?")
    parser.add_argument("--tag", help="Existing immutable frontend ECR image tag; only for frontend-image")
    args = parser.parse_args()
    if args.tag is not None and args.task != "frontend-image":
        parser.error("--tag applies only to frontend-image")
    try:
        if aws("sts", "get-caller-identity")["Account"] != "858525799322":
            raise ValueError("Wrong AWS account")
        if args.task == "status":
            if not args.command_id:
                raise ValueError("Supply a command ID")
            result = aws("ssm", "list-command-invocations", "--command-id", args.command_id)
            print(json.dumps([{"Instance": row["InstanceId"], "Status": row["Status"]}
                              for row in result["CommandInvocations"]], indent=2))
            statuses = [row["Status"] for row in result["CommandInvocations"]]
            commands = aws("ssm", "list-commands", "--command-id", args.command_id)["Commands"]
            parent = commands[0] if commands else {}
            expected = parent.get("TargetCount", 0)
            if any(status in {"Failed", "TimedOut", "Cancelled"} for status in statuses):
                return 1
            if parent.get("Status") in {"Failed", "TimedOut", "Cancelled"}:
                return 1
            complete = (expected > 0 and len(statuses) == expected and
                        parent.get("Status") == "Success" and
                        all(status == "Success" for status in statuses))
            return 0 if complete else 2
        if args.task == "ecr":
            ids = instances("worker")
            if len(ids) < 2:
                raise ValueError("Expected at least two running dev workers")
            source = ROOT / "scripts/k8s/ecr-credential-provider.py"
            script = "install -d -m 0755 /usr/local/libexec/kubelet-credential-providers\n"
            target = "/usr/local/libexec/kubelet-credential-providers/coco-ecr-credential-provider"
            script += extract(source, target)
            script += "chmod 0755 " + target + "\n" + target + " --install\nsystemctl is-active kubelet\n"
            # Align existing dev nodes with the new launch template deliberately.
            for instance in ids:
                aws("ec2", "modify-instance-metadata-options", "--instance-id", instance,
                    "--http-tokens", "required", "--http-put-response-hop-limit", "2")
            submit(ids, script)
        elif args.task == "csi":
            ids = instances("control-plane")
            if len(ids) != 1:
                raise ValueError("Expected exactly one running dev control plane")
            release = ROOT / "artifacts/deploy/dev"
            script = "export KUBECONFIG=/etc/kubernetes/admin.conf\n"
            script += "kubectl wait --for=condition=Ready nodes --all --timeout=300s\n"
            script += """
kubectl get nodes -o json | python3 -c '
import json, sys
nodes = json.load(sys.stdin)["items"]
if len(nodes) < 3 or any(
    not n.get("spec", {}).get("providerID", "").startswith("aws:///ap-southeast-1") or
    n["metadata"].get("labels", {}).get("topology.kubernetes.io/zone") not in
        ("ap-southeast-1a", "ap-southeast-1b") for n in nodes
):
    sys.exit("Missing AWS node identity/AZ; install CSI only after repair succeeds")
'
COCO_CSI_DIR=$(mktemp -d /tmp/coco-csi.XXXXXX)
"""
            script += extract(release / "ebs-csi.yaml", '"$COCO_CSI_DIR/ebs-csi.yaml"')
            script += extract(ROOT / "k8s/monitoring/storageclass.yaml", '"$COCO_CSI_DIR/storageclass.yaml"')
            script += """
kubectl apply --dry-run=server -f "$COCO_CSI_DIR/ebs-csi.yaml"
kubectl apply -f "$COCO_CSI_DIR/ebs-csi.yaml"
kubectl -n kube-system rollout status deployment/ebs-csi-controller --timeout=600s
kubectl -n kube-system rollout status daemonset/ebs-csi-node --timeout=600s
kubectl apply -f "$COCO_CSI_DIR/storageclass.yaml"
kubectl get csidriver ebs.csi.aws.com
kubectl get storageclass coco-monitoring-gp3
kubectl get csinode
"""
            submit(ids, script)
        elif args.task == "monitoring":
            ids = instances("control-plane")
            if len(ids) != 1:
                raise ValueError("Expected exactly one running dev control plane")
            release = ROOT / "artifacts/deploy/dev"
            script = "COCO_MONITORING_DIR=$(mktemp -d /tmp/coco-monitoring.XXXXXX)\n"
            script += "trap 'rm -f \"$COCO_MONITORING_DIR/secrets.json\"' EXIT\n"
            script += extract(ROOT / "k8s/monitoring/values-dev.yaml", '"$COCO_MONITORING_DIR/values-dev.yaml"')
            script += extract(release / "monitoring-resources.yaml", '"$COCO_MONITORING_DIR/resources.yaml"')
            script += extract(ROOT / "scripts/k8s/install-monitoring-dev.sh", '"$COCO_MONITORING_DIR/install.sh"')
            script += 'bash "$COCO_MONITORING_DIR/install.sh" "$COCO_MONITORING_DIR"\n'
            submit(ids, script, timeout=5400)
        elif args.task == "frontend-image":
            if not args.tag or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}", args.tag):
                raise ValueError("Supply a valid existing frontend image tag with --tag")
            aws("ecr", "describe-images", "--repository-name", "ecommerce/dev/frontend",
                "--image-ids", "imageTag=" + args.tag)
            ids = instances("control-plane")
            if len(ids) != 1:
                raise ValueError("Expected exactly one running dev control plane")
            image = "858525799322.dkr.ecr.ap-southeast-1.amazonaws.com/ecommerce/dev/frontend:" + args.tag
            script = "export KUBECONFIG=/etc/kubernetes/admin.conf\n"
            script += "kubectl -n coco set image deployment/coco-frontend frontend=" + image + "\n"
            script += "kubectl -n coco rollout status deployment/coco-frontend --timeout=600s\n"
            script += "kubectl -n coco get deployment coco-frontend\n"
            submit(ids, script)
        elif args.task == "http-metrics":
            ids = instances("control-plane")
            if len(ids) != 1:
                raise ValueError("Expected exactly one running dev control plane")
            script = "export KUBECONFIG=/etc/kubernetes/admin.conf\n"
            script += "kubectl get crd servicemonitors.monitoring.coreos.com >/dev/null\n"
            script += "kubectl -n coco rollout status deployment/coco-frontend --timeout=600s\n"
            script += """
kubectl -n coco exec deployment/coco-frontend -c frontend -- node -e '
fetch("http://127.0.0.1:9091/metrics", {signal: AbortSignal.timeout(5000)})
  .then(async r => {
    if (!r.ok || !(await r.text()).includes("# TYPE marketplace_frontend_http_requests_total counter")) process.exit(1);
  }).catch(() => { console.error("Frontend HTTP metrics unavailable; deploy the new frontend image first"); process.exit(1); });
'
COCO_HTTP_METRICS_DIR=$(mktemp -d /tmp/coco-http-metrics.XXXXXX)
"""
            script += extract(ROOT / "k8s/monitoring/resources/frontend-metrics.yaml", '"$COCO_HTTP_METRICS_DIR/frontend-metrics.yaml"')
            script += 'kubectl apply --dry-run=server -f "$COCO_HTTP_METRICS_DIR/frontend-metrics.yaml"\n'
            script += 'kubectl apply -f "$COCO_HTTP_METRICS_DIR/frontend-metrics.yaml"\n'
            script += "kubectl -n monitoring get servicemonitor coco-frontend\n"
            script += "kubectl -n coco get endpointslice -l kubernetes.io/service-name=coco-frontend-metrics\n"
            submit(ids, script)
        elif args.task == "dashboards":
            ids = instances("control-plane")
            if len(ids) != 1:
                raise ValueError("Expected exactly one running dev control plane")
            source = ROOT / "k8s/monitoring/resources/dashboards/coco-application.json"
            dashboard = json.loads(source.read_text())
            if dashboard.get("uid") != "coco-application" or not dashboard.get("panels"):
                raise ValueError("Expected the Coco application dashboard")
            script = "export KUBECONFIG=/etc/kubernetes/admin.conf\n"
            script += "kubectl get namespace monitoring >/dev/null\n"
            script += "COCO_DASHBOARD_DIR=$(mktemp -d /tmp/coco-dashboard.XXXXXX)\n"
            script += extract(source, '"$COCO_DASHBOARD_DIR/coco-application.json"')
            script += """
kubectl -n monitoring create configmap coco-application-dashboard \
  --from-file=coco-application.json="$COCO_DASHBOARD_DIR/coco-application.json" \
  --dry-run=client -o yaml |
  kubectl label --local -f - grafana_dashboard=1 --overwrite -o yaml \
  > "$COCO_DASHBOARD_DIR/dashboard-configmap.yaml"
kubectl apply --dry-run=server -f "$COCO_DASHBOARD_DIR/dashboard-configmap.yaml"
kubectl apply -f "$COCO_DASHBOARD_DIR/dashboard-configmap.yaml"
echo 'Dashboard ConfigMap updated. Grafana dashboard sidecar must import it; refresh Coco - Application after synchronization.'
"""
            submit(ids, script)
        elif args.task in {"autoscaling", "scaling-status", "scaling-demo", "scaling-demo-stop"}:
            ids = instances("control-plane")
            if len(ids) != 1:
                raise ValueError("Expected exactly one running dev control plane")
            script = "export KUBECONFIG=/etc/kubernetes/admin.conf\n"
            if args.task == "autoscaling":
                script += "COCO_SCALING_DIR=$(mktemp -d /tmp/coco-scaling.XXXXXX)\n"
                script += extract(ROOT / "artifacts/deploy/dev/cluster-autoscaler.yaml", '"$COCO_SCALING_DIR/cluster-autoscaler.yaml"')
                script += extract(ROOT / "scripts/k8s/protect-scaling-baseline.py", '"$COCO_SCALING_DIR/protect-baseline.py"')
                script += extract(ROOT / "scripts/k8s/install-autoscaling-dev.sh", '"$COCO_SCALING_DIR/install.sh"')
                script += 'bash "$COCO_SCALING_DIR/install.sh" "$COCO_SCALING_DIR"\n'
            elif args.task == "scaling-demo":
                script += "kubectl -n kube-system rollout status deployment/cluster-autoscaler --timeout=180s\n"
                script += "COCO_SCALING_DIR=$(mktemp -d /tmp/coco-scaling-demo.XXXXXX)\n"
                script += extract(ROOT / "k8s/autoscaling/demo.yaml", '"$COCO_SCALING_DIR/demo.yaml"')
                # Apply namespace before validating the namespaced Deployment.
                script += "kubectl create namespace scaling-demo --dry-run=client -o yaml | kubectl apply -f -\n"
                script += 'kubectl apply --dry-run=server -f "$COCO_SCALING_DIR/demo.yaml"\n'
                script += 'kubectl apply -f "$COCO_SCALING_DIR/demo.yaml"\n'
                script += "kubectl -n scaling-demo rollout status deployment/worker-pressure --timeout=2400s\n"
                script += "kubectl -n scaling-demo get pods -o wide\nkubectl get nodes -o wide\n"
            elif args.task == "scaling-demo-stop":
                script += "kubectl -n scaling-demo scale deployment/worker-pressure --replicas=0\n"
                script += "kubectl -n scaling-demo get deployment worker-pressure\n"
                script += "echo 'Demo requests removed. Autoscaler may scale in eligible extra workers after its stabilization period.'\n"
            else:
                script += "kubectl get nodes -o wide\n"
                script += "kubectl -n kube-system get deployment cluster-autoscaler\n"
                script += "kubectl -n kube-system get configmap cluster-autoscaler-status -o yaml\n"
                script += "kubectl -n kube-system logs deployment/cluster-autoscaler --tail=100\n"
                script += "kubectl -n coco get hpa\n"
                script += "if kubectl get namespace scaling-demo >/dev/null 2>&1; then kubectl -n scaling-demo get pods -o wide; fi\n"
            submit(ids, script, timeout=3000 if args.task == "scaling-demo" else 1800)
        else:
            ids = instances("control-plane")
            if len(ids) != 1:
                raise ValueError("Expected exactly one running dev control plane")
            release = ROOT / "artifacts/deploy/dev"
            script = "export KUBECONFIG=/etc/kubernetes/admin.conf\n"
            script += "kubectl get --raw=/readyz >/dev/null\n"
            script += "kubectl wait --for=condition=Ready nodes --all --timeout=300s\n"
            script += "COCO_TASK_DIR=$(mktemp -d /tmp/coco-deploy.XXXXXX)\n"
            script += "trap 'rm -f \"$COCO_TASK_DIR/backend-secret.env\"' EXIT\n"
            script += extract(release / "application.yaml", '"$COCO_TASK_DIR/application.yaml"')
            script += extract(release / "metrics-server.yaml", '"$COCO_TASK_DIR/metrics-server.yaml"')
            script += """
aws ssm get-parameter --region ap-southeast-1 \
  --name /ecommerce/dev/application/backend-env --with-decryption \
  --query Parameter.Value --output text > "$COCO_TASK_DIR/backend-secret.env"
kubectl create namespace coco --dry-run=client -o yaml | kubectl apply -f -
kubectl apply --dry-run=server -f "$COCO_TASK_DIR/metrics-server.yaml"
kubectl apply --dry-run=server -f "$COCO_TASK_DIR/application.yaml"
kubectl -n coco create secret generic coco-backend-secret \
  --from-env-file="$COCO_TASK_DIR/backend-secret.env" --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f "$COCO_TASK_DIR/metrics-server.yaml"
kubectl -n kube-system rollout status deployment/metrics-server --timeout=300s
kubectl wait --for=condition=Available apiservice/v1beta1.metrics.k8s.io --timeout=300s
kubectl apply -f "$COCO_TASK_DIR/application.yaml"
kubectl -n coco rollout status deployment/coco-otp-redis --timeout=300s
kubectl -n coco rollout status deployment/coco-backend --timeout=600s
kubectl -n coco rollout status deployment/coco-frontend --timeout=600s
kubectl -n coco get pods,svc,hpa
kubectl top nodes
"""
            submit(ids, script)
        return 0
    except subprocess.CalledProcessError as exc:
        print("AWS task failed at " + str(exc.cmd[1:3]) + "; inspect permissions/account and retry only after checking status.", file=sys.stderr)
        return 1
    except (ValueError, KeyError, OSError) as exc:
        print("Task could not be prepared: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
