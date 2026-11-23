#!/usr/bin/env bash
# Owner-run plan only: CSI IAM and monitoring scrape rules. No EC2/RDS targets.
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"
require_command terraform
check_aws_account
terraform -chdir="$COCO_TERRAFORM_DEV" plan \
  -target=aws_iam_role.ebs_csi \
  -target=aws_iam_role_policy_attachment.ebs_csi \
  -target=aws_iam_role_policy.control_plane_assume_ebs_csi \
  -target=aws_iam_role_policy.control_plane_monitoring_secret \
  -target=module.security.aws_vpc_security_group_ingress_rule.control_plane_monitoring \
  -out=monitoring-dev.tfplan
terraform -chdir="$COCO_TERRAFORM_DEV" show -no-color monitoring-dev.tfplan
printf '\nReview: stop if the plan deletes resources, modifies RDS or changes/replaces EC2.\n'
printf 'No apply was performed. Targeted prerequisite plan, not full infrastructure reconciliation.\n'
