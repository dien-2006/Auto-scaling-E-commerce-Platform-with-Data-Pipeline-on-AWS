#!/usr/bin/env bash
# Owner-run local checks only. No Docker build, AWS calls, SQL, migration or deploy.
set -euo pipefail
COCO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
for COCO_TOOL in uv node npm terraform python3; do
  command -v "$COCO_TOOL" >/dev/null || { printf 'Missing tool: %s\n' "$COCO_TOOL" >&2; exit 1; }
done
node -e 'if (Number(process.versions.node.split(".")[0]) !== 24) { console.error("Node.js 24 is required"); process.exit(1); }'
list_shell_scripts() {
  if command -v rg >/dev/null 2>&1; then
    rg --files -0 "$COCO_ROOT/scripts" -g '*.sh'
  else
    find "$COCO_ROOT/scripts" -type f -name '*.sh' -print0
  fi
}
while IFS= read -r -d '' COCO_SCRIPT; do
  bash -n "$COCO_SCRIPT"
done < <(list_shell_scripts)
python3 -m unittest discover -s "$COCO_ROOT/scripts/tests"
(
  cd "$COCO_ROOT/backend"
  uv lock --check
  uv sync --locked
  uv run --locked pytest tests/test_metrics.py tests/test_app.py tests/test_catalog.py tests/test_storage_images.py tests/test_seller_products.py tests/test_checkout.py
  uv run --locked ruff check app/core/metrics.py app/core/middleware.py app/main.py \
    app/services/storage.py app/services/catalog.py app/services/seller_shop.py \
    app/repositories/catalog.py app/api/v1/routers/catalog.py app/api/v1/routers/seller_shop.py \
    tests/test_catalog.py tests/test_storage_images.py tests/test_metrics.py \
    app/models/marketplace.py app/schemas/seller_products.py app/services/checkout.py \
    tests/test_seller_products.py tests/test_checkout.py
)
(
  cd "$COCO_ROOT/frontend"
  npm ci --no-audit --no-fund
  npm test
  npm run lint
  npm run typecheck
)
terraform -chdir="$COCO_ROOT/terraform/environments/dev" init
terraform -chdir="$COCO_ROOT/terraform/environments/dev" validate
terraform -chdir="$COCO_ROOT/terraform/environments/dev" test
terraform -chdir="$COCO_ROOT/terraform/environments/prod" init -backend=false
terraform -chdir="$COCO_ROOT/terraform/environments/prod" validate
terraform -chdir="$COCO_ROOT/terraform/environments/prod" test
printf 'Local checks passed. No build, AWS deployment or real-database tests were run.\n'
