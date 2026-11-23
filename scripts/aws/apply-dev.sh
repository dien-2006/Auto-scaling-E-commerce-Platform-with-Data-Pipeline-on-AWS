#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

require_command terraform

if [[ ! -f "$COCO_PLAN_FILE" ]]; then
  printf 'Chưa có dev.tfplan. Chạy bash scripts/aws/plan-dev.sh và xem plan trước.\n' >&2
  exit 1
fi

check_aws_account
printf '\nÁp dụng dev.tfplan đã lưu, không hỏi yes; tài nguyên AWS có thể phát sinh phí.\n'
terraform -chdir="$COCO_TERRAFORM_DEV" apply "$COCO_PLAN_FILE"
terraform -chdir="$COCO_TERRAFORM_DEV" output
