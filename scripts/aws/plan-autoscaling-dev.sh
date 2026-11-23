#!/usr/bin/env bash
# Targeted IAM plan only. Existing workers are handled by the separate preview.
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"
require_command terraform
require_command python3
check_aws_account
umask 077
terraform -chdir="$COCO_TERRAFORM_DEV" plan \
  -target=aws_iam_role.cluster_autoscaler \
  -target=aws_iam_role_policy.cluster_autoscaler \
  -target=aws_iam_role_policy.control_plane_assume_autoscaler \
  -out=autoscaling-dev.tfplan
terraform -chdir="$COCO_TERRAFORM_DEV" show -json autoscaling-dev.tfplan |
  python3 "$COCO_REPO_ROOT/scripts/aws/guard-autoscaling-plan.py"
terraform -chdir="$COCO_TERRAFORM_DEV" show -no-color autoscaling-dev.tfplan
printf '\nReview the three IAM resources, then apply the saved plan yourself. No apply was performed.\n'
