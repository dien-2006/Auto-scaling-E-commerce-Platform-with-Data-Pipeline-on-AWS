#!/usr/bin/env bash
# Owner-run import. Default is a dry run; never edits the database or deletes objects.
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

case "${1:---dry-run}" in
  --dry-run) COCO_SYNC_OPTIONS=(--dryrun) ;;
  --upload) COCO_SYNC_OPTIONS=() ;;
  *) printf 'Usage: bash scripts/aws/upload-catalog-images.sh [--dry-run|--upload]\n' >&2; exit 1 ;;
esac
if (( $# > 1 )); then
  printf 'Unexpected extra arguments.\n' >&2
  exit 1
fi

COCO_IMPORT_BUCKET=ecommerce-dev-product-images-858525799322-ap-southeast-1
COCO_DATA_DIRECTORY="$COCO_REPO_ROOT/data health"
if [[ ! -d "$COCO_DATA_DIRECTORY/ProductImages" || ! -d "$COCO_DATA_DIRECTORY/logo" ]]; then
  printf 'Missing data health/ProductImages or data health/logo.\n' >&2
  exit 1
fi

check_aws_account
aws s3api head-bucket --bucket "$COCO_IMPORT_BUCKET" \
  --expected-bucket-owner 858525799322 --region "$AWS_REGION"

printf 'Destination: s3://%s/; preserve ProductImages/ and logo/ keys.\n' "$COCO_IMPORT_BUCKET"
printf 'Existing objects are skipped; no public ACL, deletion, or database writes.\n'

# --no-overwrite requires a sufficiently recent AWS CLI. If unsupported, stop;
# do not remove this flag and retry, since that would change overwrite behavior.
aws s3 sync "$COCO_DATA_DIRECTORY/ProductImages/" \
  "s3://$COCO_IMPORT_BUCKET/ProductImages/" \
  --region "$AWS_REGION" --no-overwrite --no-follow-symlinks \
  --exclude '*' --include '*.jpg' --content-type image/jpeg \
  "${COCO_SYNC_OPTIONS[@]}"

aws s3 sync "$COCO_DATA_DIRECTORY/logo/" "s3://$COCO_IMPORT_BUCKET/logo/" \
  --region "$AWS_REGION" --no-overwrite --no-follow-symlinks \
  --exclude '*' --include '1.png' --include '2.png' --include '3.png' \
  --content-type image/png "${COCO_SYNC_OPTIONS[@]}"
