#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"
require_command terraform
require_command docker
check_aws_account

COCO_SOURCE_TAG=""
if [[ "${1:-}" == --push-built-from ]]; then
  if (( $# != 3 )); then
    printf 'Usage: bash scripts/aws/build-push-dev.sh --push-built-from OLD_TAG NEW_TAG\n' >&2
    exit 1
  fi
  COCO_SOURCE_TAG="$2"
  COCO_TAG="$3"
  if [[ -z "$COCO_SOURCE_TAG" ]]; then
    printf 'OLD_TAG must not be empty when reusing a local build.\n' >&2
    exit 1
  fi
elif (( $# <= 1 )); then
  COCO_TAG="${1:-dev-$(date -u +%Y%m%d%H%M%S)}"
else
  printf 'Usage: bash scripts/aws/build-push-dev.sh [NEW_IMAGE_TAG]\n' >&2
  exit 1
fi
if [[ ! "$COCO_TAG" =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]] || \
   [[ -n "$COCO_SOURCE_TAG" && ! "$COCO_SOURCE_TAG" =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]; then
  printf 'Invalid image tag.\n' >&2
  exit 1
fi
COCO_BACKEND_REPO="$(terraform -chdir="$COCO_TERRAFORM_DEV" output -raw ecr_backend_url)"
COCO_FRONTEND_REPO="$(terraform -chdir="$COCO_TERRAFORM_DEV" output -raw ecr_frontend_url)"
COCO_ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
COCO_REGISTRY="$COCO_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com"
if [[ "$COCO_BACKEND_REPO" != "$COCO_REGISTRY/ecommerce/dev/backend" || \
      "$COCO_FRONTEND_REPO" != "$COCO_REGISTRY/ecommerce/dev/frontend" ]]; then
  printf 'Terraform outputs do not match this account/dev/region. Stop.\n' >&2
  exit 1
fi

# Fail before building when an immutable tag was already published. Do not treat
# AWS permission/network errors as "tag absent"; set -e propagates those failures.
for COCO_REPOSITORY in "$COCO_BACKEND_REPO" "$COCO_FRONTEND_REPO"; do
  COCO_EXISTING_TAG="$(aws ecr list-images --region "$AWS_REGION" \
    --repository-name "${COCO_REPOSITORY#*/}" --filter tagStatus=TAGGED \
    --query "imageIds[?imageTag=='$COCO_TAG'].imageTag" --output text)"
  if [[ -n "$COCO_EXISTING_TAG" ]]; then
    printf 'Tag %s đã có trong %s. Dùng tag mới; không đổi repository sang MUTABLE.\n' \
      "$COCO_TAG" "$COCO_REPOSITORY" >&2
    exit 1
  fi
done

if [[ -n "$COCO_SOURCE_TAG" ]]; then
  # Inspect both first. Reuse exactly the owner's existing local build, without
  # pulling a possibly incomplete remote tag, rebuilding, or deleting anything.
  docker image inspect "$COCO_BACKEND_REPO:$COCO_SOURCE_TAG" >/dev/null
  docker image inspect "$COCO_FRONTEND_REPO:$COCO_SOURCE_TAG" >/dev/null
  docker tag "$COCO_BACKEND_REPO:$COCO_SOURCE_TAG" "$COCO_BACKEND_REPO:$COCO_TAG"
  docker tag "$COCO_FRONTEND_REPO:$COCO_SOURCE_TAG" "$COCO_FRONTEND_REPO:$COCO_TAG"
else
  # Build both before publishing either. No SQL or application startup is run.
  docker build --platform linux/amd64 -t "$COCO_BACKEND_REPO:$COCO_TAG" "$COCO_REPO_ROOT/backend"
  docker build --platform linux/amd64 -t "$COCO_FRONTEND_REPO:$COCO_TAG" "$COCO_REPO_ROOT/frontend"
fi
aws ecr get-login-password --region "$AWS_REGION" |
  docker login --username AWS --password-stdin "$COCO_REGISTRY"
# Publish only the runnable platform manifest. Containerd image-store pushes of
# an index plus attestations can attempt several writes to an immutable tag.
# Docker API >=1.46 is required; Docker 28 supports this flag.
docker push --platform linux/amd64 "$COCO_BACKEND_REPO:$COCO_TAG"
docker push --platform linux/amd64 "$COCO_FRONTEND_REPO:$COCO_TAG"
for COCO_REPOSITORY in "$COCO_BACKEND_REPO" "$COCO_FRONTEND_REPO"; do
  aws ecr describe-images --region "$AWS_REGION" \
    --repository-name "${COCO_REPOSITORY#*/}" --image-ids "imageTag=$COCO_TAG" \
    --query 'imageDetails[0].{Digest:imageDigest,Tags:imageTags}' --output json
done
printf '\nPublished tag: %s\nUse the same tag with prepare-dev-release.py.\n' "$COCO_TAG"
