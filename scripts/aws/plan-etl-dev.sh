#!/usr/bin/env bash
# Update only the Glue runtime arguments/output wiring. Never apply automatically.
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"
require_command terraform
check_aws_account
terraform -chdir="$COCO_TERRAFORM_DEV" plan \
  -target=module.etl.aws_glue_job.extract \
  -target=module.etl.aws_glue_job.transform \
  -target=module.etl.aws_glue_catalog_database.analytics \
  -target=module.etl.aws_athena_workgroup.analytics \
  -out=etl-dev.tfplan
terraform -chdir="$COCO_TERRAFORM_DEV" show -no-color etl-dev.tfplan
printf '\nReview plan: stop for deletes, EC2 replacement, RDS changes, or unrelated modifications.\n'
printf 'No apply performed. Glue scripts are uploaded separately; no job was started.\n'
