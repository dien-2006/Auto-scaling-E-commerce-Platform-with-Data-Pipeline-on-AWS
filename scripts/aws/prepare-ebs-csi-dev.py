#!/usr/bin/env python3
"""Owner-run local CSI render. Reads Terraform outputs; does not deploy or create EBS."""

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CHART_VERSION = "2.67.1"


def command(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def main():
    try:
        account = json.loads(command(["aws", "sts", "get-caller-identity", "--region",
                                      "ap-southeast-1", "--output", "json", "--no-cli-pager"]))
        if account["Account"] != "858525799322":
            raise ValueError("Wrong AWS account")
        role = command(["terraform", "-chdir=" + str(ROOT / "terraform/environments/dev"),
                        "output", "-raw", "ebs_csi_role_arn"]).strip()
        if not re.fullmatch(r"arn:aws:iam::858525799322:role/ecommerce-dev-ebs-csi", role):
            raise ValueError("Unexpected CSI role ARN; apply the reviewed IAM plan first")
        with tempfile.TemporaryDirectory(prefix="coco-csi-render-") as directory:
            work = Path(directory)
            chart = command(["helm", "template", "aws-ebs-csi-driver", "aws-ebs-csi-driver",
                             "--repo", "https://kubernetes-sigs.github.io/aws-ebs-csi-driver",
                             "--version", CHART_VERSION, "--namespace", "kube-system",
                             "--kube-version", "1.34.0", "--skip-tests",
                             "-f", str(ROOT / "k8s/ebs-csi/values-dev.yaml")])
            if "name: ebs-csi-controller" not in chart or "v1.67.2" not in chart:
                raise ValueError("Unexpected CSI chart render")
            if "ebs-csi-driver-test" in chart:
                raise ValueError("CSI render contains Helm tester resources; refusing deployment output")
            (work / "driver.yaml").write_text(chart)
            profile = ("[profile coco-ebs-csi]\nrole_arn = " + role +
                       "\ncredential_source = Ec2InstanceMetadata\nregion = ap-southeast-1\n"
                       "role_session_name = coco-dev-ebs-csi\n")
            (work / "profile.json").write_text(json.dumps({
                "apiVersion": "v1", "kind": "ConfigMap",
                "metadata": {"name": "coco-ebs-csi-aws-config", "namespace": "kube-system"},
                "data": {"config": profile},
            }))
            # The upstream chart has no controller.hostNetwork value. Patch the
            # rendered Deployment explicitly, rather than passing an ignored value.
            (work / "kustomization.yaml").write_text(json.dumps({
                "apiVersion": "kustomize.config.k8s.io/v1beta1", "kind": "Kustomization",
                "namespace": "kube-system", "resources": ["profile.json", "driver.yaml"],
                "patches": [{"target": {"kind": "Deployment", "name": "ebs-csi-controller"},
                             "patch": json.dumps([
                                 {"op": "add", "path": "/spec/template/spec/hostNetwork", "value": True},
                                 {"op": "add", "path": "/spec/template/spec/dnsPolicy",
                                  "value": "ClusterFirstWithHostNet"},
                             ])}],
            }))
            manifest = command(["kubectl", "kustomize", str(work)])
        destination = ROOT / "artifacts/deploy/dev"
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "ebs-csi.yaml").write_text(manifest)
        print("Rendered artifacts/deploy/dev/ebs-csi.yaml. No deployment or volume creation performed.")
        return 0
    except subprocess.CalledProcessError as exc:
        print("CSI render failed: " + str(exc.cmd[:3]), file=sys.stderr)
        print(exc.stderr.strip(), file=sys.stderr)
        return 1
    except (ValueError, KeyError, OSError) as exc:
        print("CSI render stopped: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
