#!/usr/bin/env python3
"""Owner-run autoscaling preparation. Bootstrap preview is the default action."""

import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
REGION = "ap-southeast-1"
ACCOUNT = "858525799322"
ASG = "ecommerce-dev-worker-asg"
ROLE = f"arn:aws:iam::{ACCOUNT}:role/ecommerce-dev-cluster-autoscaler"

_spec = importlib.util.spec_from_file_location("autoscaling_check", Path(__file__).with_name("check-autoscaling-dev.py"))
checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checker)


def command(args, input_text=None):
    return subprocess.run(args, input=input_text, check=True, capture_output=True, text=True).stdout


def aws(*args):
    output = command(["aws", *args, "--region", REGION, "--output", "json", "--no-cli-pager"]).strip()
    return json.loads(output) if output else {}


def current_group():
    groups = aws("autoscaling", "describe-auto-scaling-groups",
                 "--auto-scaling-group-names", ASG)["AutoScalingGroups"]
    if len(groups) != 1:
        raise ValueError("Expected exactly one existing dev worker ASG")
    group = groups[0]
    tags = {tag["Key"]: tag["Value"] for tag in group.get("Tags", [])}
    if (tags.get("k8s.io/cluster-autoscaler/ecommerce-dev-k8s") != "owned" or
            tags.get("k8s.io/cluster-autoscaler/enabled") != "true" or
            not 2 <= group["DesiredCapacity"] <= 4 or
            set(group["AvailabilityZones"]) != {REGION + "a", REGION + "b"}):
        raise ValueError("Unexpected ASG ownership, desired capacity or AZs; inspect before changing")
    return group


def current_template(group):
    reference = group["LaunchTemplate"]
    return aws("ec2", "describe-launch-template-versions",
               "--launch-template-id", reference["LaunchTemplateId"], "--versions", reference["Version"])["LaunchTemplateVersions"][0]


def source_bootstrap():
    # Console evaluates the current SOURCE local using the existing control-plane
    # IP in state. It does not apply a plan or refresh/stop/replace the EC2 nodes.
    expression = ('jsonencode({bootstrap=module.kubernetes.worker_bootstrap_base64,'
                  'template_id=module.kubernetes.worker_launch_template_id,'
                  'control_plane_ip=module.kubernetes.control_plane_private_ip})\n')
    result = command(["terraform", "-chdir=" + str(ROOT / "terraform/environments/dev"), "console"], expression)
    config = json.loads(json.loads(result))
    raw = base64.b64decode(config["bootstrap"], validate=True)
    source = raw.decode()
    if len(raw) > 16384 or not source.startswith("#!/bin/bash\n"):
        raise ValueError("Invalid/oversized EC2 user data")
    if not re.fullmatch(r"lt-[0-9a-f]+", config["template_id"]):
        raise ValueError("Unexpected worker launch template ID")
    if f'kubeadm join {config["control_plane_ip"]}:6443 ' not in source:
        raise ValueError("Bootstrap does not target the Terraform control plane")
    return config


def bootstrap(submit=False):
    group = current_group()
    old = current_template(group)
    config = source_bootstrap()
    reference = group["LaunchTemplate"]
    if reference["LaunchTemplateId"] != config["template_id"]:
        raise ValueError("Live ASG does not use the Terraform worker launch template")
    cp = aws("ec2", "describe-instances", "--filters",
             "Name=tag:Name,Values=ecommerce-dev-control-plane", "Name=instance-state-name,Values=running")
    nodes = [item for reservation in cp["Reservations"] for item in reservation["Instances"]]
    if len(nodes) != 1 or nodes[0]["PrivateIpAddress"] != config["control_plane_ip"]:
        raise ValueError("Control-plane IP in state differs from the running dev instance")
    data = {**old["LaunchTemplateData"], "UserData": config["bootstrap"],
            "MetadataOptions": {"HttpEndpoint": "enabled", "HttpTokens": "required", "HttpPutResponseHopLimit": 2}}
    checks = checker.inspect_group(group, data)
    if not all(checks.values()):
        raise ValueError("New bootstrap failed prerequisites: " + str([key for key, value in checks.items() if not value]))
    changed = (old["LaunchTemplateData"].get("UserData") != config["bootstrap"] or
               any(old["LaunchTemplateData"].get("MetadataOptions", {}).get(key) != value
                   for key, value in data["MetadataOptions"].items()))
    preview = {"asg": ASG, "template_id": reference["LaunchTemplateId"],
               "previous_version": old["VersionNumber"], "new_bootstrap_required": changed,
               "bootstrap_sha256": hashlib.sha256(base64.b64decode(config["bootstrap"])).hexdigest(),
               "previous_minimum": group["MinSize"], "minimum": 2, "maximum": 4,
               "desired_unchanged": group["DesiredCapacity"]}
    print(json.dumps(preview, indent=2))
    if not submit:
        print("Preview only. Re-run bootstrap --submit to publish the bootstrap and set the ASG floor to two.")
        return
    version = old["VersionNumber"]
    if changed:
        patch = {"UserData": config["bootstrap"], "MetadataOptions": data["MetadataOptions"]}
        token = hashlib.sha256((reference["LaunchTemplateId"] + str(version) + json.dumps(patch, sort_keys=True)).encode()).hexdigest()
        result = aws("ec2", "create-launch-template-version", "--launch-template-id", reference["LaunchTemplateId"],
                     "--source-version", str(version), "--version-description", "COCO reviewed worker bootstrap",
                     "--client-token", token, "--launch-template-data", json.dumps(patch))
        version = result["LaunchTemplateVersion"]["VersionNumber"]
    aws("autoscaling", "update-auto-scaling-group", "--auto-scaling-group-name", ASG,
        "--launch-template", json.dumps({"LaunchTemplateId": reference["LaunchTemplateId"], "Version": str(version)}),
        "--min-size", "2", "--max-size", "4")
    print(f"ASG now pins launch template version {version}; only FUTURE workers use it. No instance refresh/replacement requested.")


def render():
    role = command(["terraform", "-chdir=" + str(ROOT / "terraform/environments/dev"),
                    "output", "-raw", "cluster_autoscaler_role_arn"]).strip()
    if role != ROLE:
        raise ValueError("Apply the reviewed autoscaling IAM plan first")
    group = current_group()
    version = current_template(group)
    checks = checker.inspect_group(group, version["LaunchTemplateData"])
    if not all(checks.values()) or group["MinSize"] != 2 or group["MaxSize"] != 4:
        raise ValueError("Live worker bootstrap/capacity gate failed. Complete bootstrap --submit first")
    manifest = (ROOT / "k8s/autoscaling/cluster-autoscaler-dev.yaml").read_text()
    if manifest.count("REPLACE_AUTOSCALER_ROLE_ARN") != 1:
        raise ValueError("Unexpected autoscaler manifest template")
    manifest = manifest.replace("REPLACE_AUTOSCALER_ROLE_ARN", role)
    target = ROOT / "artifacts/deploy/dev"
    target.mkdir(parents=True, exist_ok=True)
    (target / "cluster-autoscaler.yaml").write_text(manifest)
    print("Prepared artifacts/deploy/dev/cluster-autoscaler.yaml. No Kubernetes deployment performed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["bootstrap", "render"], nargs="?", default="bootstrap")
    parser.add_argument("--submit", action="store_true", help="Explicitly update only the future-worker bootstrap and ASG limits")
    args = parser.parse_args()
    if args.submit and args.action != "bootstrap":
        parser.error("--submit applies only to bootstrap")
    try:
        if aws("sts", "get-caller-identity")["Account"] != ACCOUNT:
            raise ValueError("Wrong AWS account")
        if args.action == "bootstrap":
            bootstrap(args.submit)
        else:
            render()
        return 0
    except subprocess.CalledProcessError as exc:
        # Do not print the CLI command: create-launch-template-version includes
        # the entire user-data payload. API stderr is sufficient for diagnosis.
        print("Autoscaling preparation failed: " + (exc.stderr or "Command failed").strip(), file=sys.stderr)
        return 1
    except (ValueError, KeyError, OSError) as exc:
        print("Autoscaling preparation stopped: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
