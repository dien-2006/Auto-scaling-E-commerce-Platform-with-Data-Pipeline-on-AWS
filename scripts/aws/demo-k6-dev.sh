#!/usr/bin/env bash
# Owner-run HTTP demo against the dev ALB. Does not deploy, run SQL or modify ASG settings.
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"
COCO_K6_PROFILE="${1:-smoke}"
case "$COCO_K6_PROFILE" in
  smoke|scale) ;;
  *) printf 'Usage: bash scripts/aws/demo-k6-dev.sh [smoke|scale]\n' >&2; exit 1 ;;
esac
require_command terraform
check_aws_account
COCO_K6_ALB="$(terraform -chdir="$COCO_TERRAFORM_DEV" output -raw alb_dns_name)"
[[ "$COCO_K6_ALB" =~ ^ecommerce-dev-alb-[a-zA-Z0-9.-]+\.ap-southeast-1\.elb\.amazonaws\.com$ ]] || {
  printf 'Unexpected dev ALB hostname; refusing to send load.\n' >&2
  exit 1
}
COCO_K6_BASE="http://$COCO_K6_ALB"
COCO_K6_PEAK="${PEAK_VUS:-50}"
COCO_K6_HOLD="${HOLD_SECONDS:-600}"
printf 'Target: %s\nProfile: %s; peak VUs: %s; hold seconds: %s\n' \
  "$COCO_K6_BASE" "$COCO_K6_PROFILE" "$COCO_K6_PEAK" "$COCO_K6_HOLD"
printf 'UTC start: %s\n' "$(date -u +%FT%TZ)"
trap 'printf "UTC finish: %s\n" "$(date -u +%FT%TZ)"' EXIT
if command -v k6 >/dev/null 2>&1; then
  k6 run -e BASE_URL="$COCO_K6_BASE" -e PROFILE="$COCO_K6_PROFILE" \
    -e PEAK_VUS="$COCO_K6_PEAK" -e HOLD_SECONDS="$COCO_K6_HOLD" \
    "$COCO_REPO_ROOT/tests/k6/web-scaling.js"
else
  require_command docker
  docker info >/dev/null
  # Same pinned image already used by this repository's isolated k6 harness.
  docker run --rm -i \
    -e BASE_URL="$COCO_K6_BASE" -e PROFILE="$COCO_K6_PROFILE" \
    -e PEAK_VUS="$COCO_K6_PEAK" -e HOLD_SECONDS="$COCO_K6_HOLD" \
    grafana/k6@sha256:3d8e5c7f1d53ec59408c2ffbd9943602a0985ffcbd4a2430ec00f3ffca89796e \
    run - < "$COCO_REPO_ROOT/tests/k6/web-scaling.js"
fi
