#!/usr/bin/env bash
# Generate the operator/deployment baseline from the saved Terraform plan.
# This is NOT the Cluster Autoscaler runtime policy and is never auto-applied.
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"
require_command uvx
require_command terraform
export DISABLE_IAM_POLICY_AUTOPILOT_TELEMETRY=true
uvx iam-policy-autopilot@latest --version
umask 077
mkdir -p "$COCO_REPO_ROOT/artifacts/deploy/dev"
terraform -chdir="$COCO_TERRAFORM_DEV" show -json autoscaling-dev.tfplan \
  > "$COCO_REPO_ROOT/artifacts/deploy/dev/autoscaling-plan.json"
uvx iam-policy-autopilot@latest generate-policies \
  "$COCO_REPO_ROOT/artifacts/deploy/dev/autoscaling-plan.json" \
  --region ap-southeast-1 --account 858525799322 --pretty \
  > "$COCO_REPO_ROOT/artifacts/deploy/dev/autoscaling-operator-iam-baseline.json"
printf 'Saved operator baseline privately; no policy uploaded/applied. Keep plan JSON private and do not commit it.\n'
