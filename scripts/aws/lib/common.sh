#!/usr/bin/env bash
# Source this file from the entry-point scripts; it does not call AWS itself.
set -euo pipefail

COCO_SCRIPTS_DIRECTORY="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
COCO_REPO_ROOT="$(cd -- "$COCO_SCRIPTS_DIRECTORY/.." && pwd)"
COCO_TERRAFORM_DEV="$COCO_REPO_ROOT/terraform/environments/dev"
COCO_PLAN_FILE="$COCO_TERRAFORM_DEV/dev.tfplan"
export AWS_REGION=ap-southeast-1
export AWS_DEFAULT_REGION="$AWS_REGION"
export AWS_PAGER=""

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Thiếu công cụ: %s\n' "$1" >&2
    exit 1
  fi
}

check_aws_account() {
  require_command aws
  local coco_current_account
  coco_current_account="$(aws sts get-caller-identity --region "$AWS_REGION" --query Account --output text)"
  printf 'AWS account: %s; region: %s\n' "$coco_current_account" "$AWS_REGION"
  if [[ "$coco_current_account" != 858525799322 ]]; then
    printf 'Sai account của dự án; dừng trước khi tạo hoặc thay đổi tài nguyên.\n' >&2
    exit 1
  fi
}
