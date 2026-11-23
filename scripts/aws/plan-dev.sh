#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

require_command terraform
check_aws_account

terraform -chdir="$COCO_TERRAFORM_DEV" init
terraform -chdir="$COCO_TERRAFORM_DEV" validate
terraform -chdir="$COCO_TERRAFORM_DEV" plan \
  -var="aws_region=$AWS_REGION" \
  -out="$COCO_PLAN_FILE"

printf '\nĐã lưu plan: %s\n' "$COCO_PLAN_FILE"
printf 'Xem plan trước khi apply:\n'
printf 'terraform -chdir="%s" show -no-color dev.tfplan\n' "$COCO_TERRAFORM_DEV"
