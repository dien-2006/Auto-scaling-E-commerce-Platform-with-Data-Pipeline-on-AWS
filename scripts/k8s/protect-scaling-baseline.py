#!/usr/bin/env python3
"""Run on the dev control plane: validate inventory, then protect baseline nodes."""

import json
from pathlib import Path
import subprocess
import sys

PROTECTED = "cluster-autoscaler.kubernetes.io/scale-down-disabled"
BASELINE = "coco.dev/scaling-baseline"
ZONES = {"ap-southeast-1a", "ap-southeast-1b"}


def select_protected(nodes, pods, group):
    if group["AutoScalingGroupName"] != "ecommerce-dev-worker-asg":
        raise ValueError("Unexpected ASG")
    inventory = {item["InstanceId"]: item["AvailabilityZone"] for item in group["Instances"]
                 if item["LifecycleState"] == "InService" and item["HealthStatus"] == "Healthy"}
    workers = {}
    for node in nodes:
        labels = node["metadata"].get("labels", {})
        if "node-role.kubernetes.io/control-plane" in labels:
            continue
        provider = node.get("spec", {}).get("providerID", "")
        zone = labels.get("topology.kubernetes.io/zone")
        instance = provider.rsplit("/", 1)[-1]
        ready = any(c["type"] == "Ready" and c["status"] == "True" for c in node.get("status", {}).get("conditions", []))
        if (not ready or zone not in ZONES or inventory.get(instance) != zone or
                provider != f"aws:///{zone}/{instance}"):
            raise ValueError("Worker identity/readiness does not match the dev ASG: " + node["metadata"]["name"])
        workers[node["metadata"]["name"]] = node
    if len(workers) != len(inventory) or not 2 <= len(workers) <= 4:
        raise ValueError("ASG and Kubernetes worker counts differ; wait for all workers to join Ready")
    protected = set()
    for zone in sorted(ZONES):
        candidates = [node for node in workers.values() if node["metadata"]["labels"]["topology.kubernetes.io/zone"] == zone]
        if not candidates:
            raise ValueError("Missing Ready baseline worker in " + zone)
        candidates.sort(key=lambda n: (
            n["metadata"].get("annotations", {}).get(BASELINE) != "true",
            n["metadata"].get("creationTimestamp", ""), n["metadata"]["name"],
        ))
        protected.add(candidates[0]["metadata"]["name"])
    baseline = set(protected)
    for node in workers.values():
        if node["metadata"].get("annotations", {}).get(PROTECTED) == "true":
            protected.add(node["metadata"]["name"])
    # Never evict a node currently hosting PVC data, including monitoring EBS.
    for pod in pods:
        if pod.get("status", {}).get("phase") in {"Succeeded", "Failed"}:
            continue
        node = pod.get("spec", {}).get("nodeName")
        volumes = pod.get("spec", {}).get("volumes", [])
        if node in workers and any("persistentVolumeClaim" in volume for volume in volumes):
            protected.add(node)
    return baseline, protected


def kubectl(*args):
    result = subprocess.run(["kubectl", "--kubeconfig=/etc/kubernetes/admin.conf", *args],
                            check=True, capture_output=True, text=True)
    return result.stdout


def main():
    try:
        group = json.loads(Path(sys.argv[1]).read_text())["AutoScalingGroups"][0]
        nodes = json.loads(kubectl("get", "nodes", "-o", "json"))["items"]
        pods = json.loads(kubectl("get", "pods", "-A", "-o", "json"))["items"]
        baseline, protected = select_protected(nodes, pods, group)
        # Selection is fully validated before the first Kubernetes write.
        for name in sorted(protected):
            annotations = {PROTECTED: "true"}
            if name in baseline:
                annotations[BASELINE] = "true"
            kubectl("patch", "node", name, "--type=merge", "-p", json.dumps({"metadata": {"annotations": annotations}}))
        # Protect current singleton OTP cache without restarting it.
        for pod in pods:
            meta = pod["metadata"]
            if meta.get("namespace") == "coco" and meta.get("labels", {}).get("app") == "coco-otp-redis":
                kubectl("-n", "coco", "annotate", "pod", meta["name"],
                        "cluster-autoscaler.kubernetes.io/safe-to-evict=false", "--overwrite")
        print(json.dumps({"baseline": sorted(baseline), "protected_nodes": sorted(protected)}, indent=2))
        print("Existing protection annotations were preserved; no pods or volumes were deleted.")
        return 0
    except (IndexError, KeyError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print("Scaling baseline protection failed: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
