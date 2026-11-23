#!/usr/bin/env bash
# Owner-run static baseline only; never uploads/applies an IAM policy.
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"
require_command uvx
export DISABLE_IAM_POLICY_AUTOPILOT_TELEMETRY=true
uvx iam-policy-autopilot@latest --version
umask 077
mkdir -p "$COCO_REPO_ROOT/artifacts/deploy/dev"
uvx iam-policy-autopilot@latest generate-policies \
  "$COCO_REPO_ROOT/etl/common/aws_clients.py" \
  "$COCO_REPO_ROOT/etl/check_aws.py" \
  "$COCO_REPO_ROOT/etl/extract/extract_postgres.py" \
  "$COCO_REPO_ROOT/etl/extract/setup_workflow.py" \
  "$COCO_REPO_ROOT/etl/extract/run_workflow.py" \
  "$COCO_REPO_ROOT/etl/transform/transform.py" \
  "$COCO_REPO_ROOT/etl/orchestration/deploy_scripts.py" \
  "$COCO_REPO_ROOT/etl/orchestration/complete_pipeline.py" \
  "$COCO_REPO_ROOT/etl/athena/create_tables.py" \
  "$COCO_REPO_ROOT/etl/athena/run_queries.py" \
  --region ap-southeast-1 --account 858525799322 \
  --service-hints s3 glue athena sts secretsmanager \
  --tf-dir "$COCO_TERRAFORM_DEV" --pretty \
  > "$COCO_REPO_ROOT/artifacts/deploy/dev/etl-iam-baseline.json"
printf 'Baseline saved to artifacts/deploy/dev/etl-iam-baseline.json. Review separately for job roles and operator; nothing applied.\n'
