#!/usr/bin/env python3
"""Reject mutations outside the three dedicated autoscaler IAM resources."""
import json
import sys

ALLOWED = {"aws_iam_role.cluster_autoscaler", "aws_iam_role_policy.cluster_autoscaler",
           "aws_iam_role_policy.control_plane_assume_autoscaler"}


def validate(plan):
    unexpected = []
    for resource in plan.get("resource_changes", []):
        actions = resource["change"]["actions"]
        if actions in (["no-op"], ["read"]):
            continue
        if resource["address"] not in ALLOWED or actions not in (["create"], ["update"]):
            unexpected.append(resource["address"] + ": " + "/".join(actions))
    if unexpected:
        raise ValueError("Do NOT apply this plan. Unexpected mutations: " + ", ".join(unexpected))


def main():
    try:
        validate(json.load(sys.stdin))
        print("Plan gate passed: only dedicated autoscaler IAM resources may change; no EC2, ASG or RDS mutation.")
        return 0
    except (KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
