#!/usr/bin/env python3
"""Read-only owner-run check before installing Cluster Autoscaler on kubeadm dev."""

import base64
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
REGION = "ap-southeast-1"
ACCOUNT = "858525799322"


def command(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def aws(*args):
    return json.loads(command(["aws", *args, "--region", REGION,
                               "--output", "json", "--no-cli-pager"]))


def inspect_group(group, template):
    tags = {tag["Key"]: tag["Value"] for tag in group.get("Tags", [])}
    source = base64.b64decode(template.get("UserData", ""), validate=True).decode()
    checks = {
        "discovery_enabled": tags.get("k8s.io/cluster-autoscaler/enabled") == "true",
        "discovery_cluster": tags.get("k8s.io/cluster-autoscaler/ecommerce-dev-k8s") == "owned",
        "awscli_official_installer": "awscli.amazonaws.com/awscli-exe-linux-" in source,
        "aws_provider_identity": "COCO_AWS_NODE_ARGS=--provider-id=" in source,
        "ecr_credential_provider": "coco-ecr-credential-provider" in source,
        "join_current_cluster": "kubeadm join" in source and "worker_joined" in source,
        "kubernetes_minor_1_34": "pkgs.k8s.io/core:/stable:/v1.34/" in source,
        "imds_v2_required": template.get("MetadataOptions", {}).get("HttpTokens") == "required",
        "imds_hop_limit_2": template.get("MetadataOptions", {}).get("HttpPutResponseHopLimit") == 2,
        "at_least_two_azs": len(group.get("AvailabilityZones", [])) >= 2,
        "bounded_capacity": 1 <= group["MinSize"] <= group["DesiredCapacity"] <= group["MaxSize"] <= 4,
        "desired_workers_in_service": sum(
            instance.get("LifecycleState") == "InService" and instance.get("HealthStatus") == "Healthy"
            for instance in group.get("Instances", [])
        ) >= group["DesiredCapacity"],
    }
    return checks


def main():
    try:
        if aws("sts", "get-caller-identity")["Account"] != ACCOUNT:
            raise ValueError("Wrong AWS account")
        name = command(["terraform", "-chdir=" + str(ROOT / "terraform/environments/dev"),
                        "output", "-raw", "kubernetes_worker_asg"]).strip()
        if name != "ecommerce-dev-worker-asg":
            raise ValueError("Unexpected dev worker ASG")
        groups = aws("autoscaling", "describe-auto-scaling-groups",
                     "--auto-scaling-group-names", name)["AutoScalingGroups"]
        if len(groups) != 1:
            raise ValueError("Expected exactly one current dev worker ASG")
        group = groups[0]
        reference = group.get("LaunchTemplate")
        if not reference:
            raise ValueError("Expected an ASG launch template")
        version = aws("ec2", "describe-launch-template-versions",
                      "--launch-template-id", reference["LaunchTemplateId"],
                      "--versions", reference["Version"])["LaunchTemplateVersions"][0]
        checks = inspect_group(group, version["LaunchTemplateData"])
        rows = []
        ids = [instance["InstanceId"] for instance in group.get("Instances", [])]
        if ids:
            response = aws("ec2", "describe-instances", "--instance-ids", *ids)
            rows = [{"id": instance["InstanceId"], "ip": instance.get("PrivateIpAddress"),
                     "az": instance["Placement"]["AvailabilityZone"],
                     "state": instance["State"]["Name"]}
                    for reservation in response["Reservations"] for instance in reservation["Instances"]]
        print(json.dumps({"asg": name, "minimum": group["MinSize"],
                          "desired": group["DesiredCapacity"], "maximum": group["MaxSize"],
                          "launch_template_version": version["VersionNumber"],
                          "checks": checks, "workers": rows}, indent=2))
        print("Read-only check. No instances, desired capacity or IAM permissions were changed.")
        print("This does not prove Cluster Autoscaler is installed or has scaled a worker.")
        print("One ASG across two AZs does not guarantee a replacement in the AZ of an existing EBS volume.")
        if not all(checks.values()):
            print("Fix failed prerequisites before installing Cluster Autoscaler.", file=sys.stderr)
            return 1
        return 0
    except subprocess.CalledProcessError as exc:
        print("Autoscaling inspection failed: " + (exc.stderr or str(exc)).strip(), file=sys.stderr)
        return 1
    except (KeyError, ValueError, OSError) as exc:
        print("Autoscaling inspection stopped: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
