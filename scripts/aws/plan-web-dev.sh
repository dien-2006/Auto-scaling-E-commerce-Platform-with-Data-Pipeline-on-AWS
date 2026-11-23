#!/usr/bin/env bash
# Repair only web routing/image access/deployment-secret prerequisites.
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"
require_command terraform
check_aws_account
terraform -chdir="$COCO_TERRAFORM_DEV" plan \
  -target='module.alb.aws_lb.main' \
  -target='module.alb.aws_lb_listener_rule.backend_http' \
  -target='module.iam.aws_iam_role_policy.worker_images' \
  -target='module.storage.aws_s3_bucket_cors_configuration.images' \
  -target='module.cloudfront.aws_s3_bucket_policy.images' \
  -target='module.monitoring.aws_cloudwatch_metric_alarm.backend_5xx' \
  -target='module.monitoring.aws_cloudwatch_metric_alarm.backend_latency' \
  -target='aws_kms_key.deployment_secrets' \
  -target='aws_kms_alias.deployment_secrets' \
  -target='aws_iam_role_policy.control_plane_deployment_secrets' \
  -out=web-dev.tfplan
terraform -chdir="$COCO_TERRAFORM_DEV" show -no-color web-dev.tfplan
printf '\nReview dependencies: stop if this plan changes RDS, deletes resources or replaces EC2.\n'
printf 'No apply was performed. This targeted repair is not a full infrastructure reconciliation.\n'
