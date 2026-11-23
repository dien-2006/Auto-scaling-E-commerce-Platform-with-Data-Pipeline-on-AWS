#!/usr/bin/env bash
# Owner-run frontend-only image release. No backend build, secrets or SQL.
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"
require_command terraform
require_command docker
check_aws_account
(( $# <= 1 )) || { echo 'Usage: bash scripts/aws/build-push-frontend-dev.sh [NEW_TAG]' >&2; exit 1; }
COCO_FRONTEND_TAG="${1:-dev-frontend-$(date -u +%Y%m%d%H%M%S)}"
[[ "$COCO_FRONTEND_TAG" =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]] || { echo 'Invalid image tag' >&2; exit 1; }
COCO_FRONTEND_REPOSITORY="$(terraform -chdir="$COCO_TERRAFORM_DEV" output -raw ecr_frontend_url)"
COCO_FRONTEND_REGISTRY=858525799322.dkr.ecr.ap-southeast-1.amazonaws.com
[[ "$COCO_FRONTEND_REPOSITORY" == "$COCO_FRONTEND_REGISTRY/ecommerce/dev/frontend" ]] || { echo 'Unexpected frontend repository' >&2; exit 1; }
COCO_FRONTEND_EXISTING="$(aws ecr list-images --region "$AWS_REGION" \
  --repository-name ecommerce/dev/frontend --filter tagStatus=TAGGED \
  --query "imageIds[?imageTag=='$COCO_FRONTEND_TAG'].imageTag" --output text)"
[[ -z "$COCO_FRONTEND_EXISTING" ]] || { echo 'Immutable tag already exists; choose a new tag' >&2; exit 1; }
docker build --platform linux/amd64 -t "$COCO_FRONTEND_REPOSITORY:$COCO_FRONTEND_TAG" "$COCO_REPO_ROOT/frontend"
aws ecr get-login-password --region "$AWS_REGION" |
  docker login --username AWS --password-stdin "$COCO_FRONTEND_REGISTRY"
docker push --platform linux/amd64 "$COCO_FRONTEND_REPOSITORY:$COCO_FRONTEND_TAG"
aws ecr describe-images --region "$AWS_REGION" --repository-name ecommerce/dev/frontend \
  --image-ids "imageTag=$COCO_FRONTEND_TAG" \
  --query 'imageDetails[0].{Digest:imageDigest,Tags:imageTags}' --output json
printf '\nPublished frontend-only tag: %s\n' "$COCO_FRONTEND_TAG"
printf 'Deploy with: python3 scripts/aws/run-dev-task.py frontend-image --tag %s\n' "$COCO_FRONTEND_TAG"
