#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

require_command terraform
check_aws_account

printf '\nTerraform outputs của dev:\n'
terraform -chdir="$COCO_TERRAFORM_DEV" output

printf '\nEC2 của ecommerce dev:\n'
aws ec2 describe-instances \
  --region "$AWS_REGION" \
  --filters \
    'Name=tag:Environment,Values=dev' \
    'Name=tag:Project,Values=ecommerce' \
    'Name=instance-state-name,Values=pending,running,stopping,stopped' \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name,PrivateIpAddress]' \
  --output table

printf '\nSSM managed instances trong account/region hiện tại (có thể gồm dự án khác):\n'
aws ssm describe-instance-information \
  --region "$AWS_REGION" \
  --query 'InstanceInformationList[].[InstanceId,PingStatus,PlatformName]' \
  --output table
