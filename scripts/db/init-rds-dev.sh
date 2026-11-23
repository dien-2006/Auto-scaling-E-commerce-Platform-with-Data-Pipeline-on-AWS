#!/usr/bin/env bash
# Owner-run, one-time import into empty dev RDS through an SSM tunnel.
# Source SQL files are read unchanged. Never drops tables or clears data.
set -euo pipefail
COCO_PSQL_AUTH=(-W)
case "${1:-}" in
  '') ;;
  --non-interactive)
    [[ $# == 1 && -n "${PGPASSFILE:-}" && -f "$PGPASSFILE" ]] || {
      printf 'Non-interactive import requires a private PGPASSFILE.\n' >&2; exit 1;
    }
    COCO_PSQL_AUTH=(-w)
    ;;
  *) printf 'Usage: bash scripts/db/init-rds-dev.sh [--non-interactive]\n' >&2; exit 1 ;;
esac
COCO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
command -v psql >/dev/null || { printf 'Missing tool: psql\n' >&2; exit 1; }
for COCO_SOURCE in marketplace_schema.sql example_data.sql; do
  [[ -r "$COCO_ROOT/sql/$COCO_SOURCE" ]] || {
    printf 'Cannot read SQL source: %s\n' "$COCO_SOURCE" >&2
    exit 1
  }
done
[[ "${PGHOST:-}" == "127.0.0.1" && "${PGPORT:-}" == "15432" &&
   "${PGDATABASE:-}" == "coco_marketplace" && -n "${PGUSER:-}" ]] || {
  printf 'Set PGHOST=127.0.0.1 PGPORT=15432 PGDATABASE=coco_marketplace and PGUSER; open the dev RDS SSM tunnel first.\n' >&2
  exit 1
}
[[ "${PGSSLMODE:-}" == "require" || "${PGSSLMODE:-}" == "verify-full" ]] || {
  printf 'Set PGSSLMODE=require (or configure verify-full).\n' >&2
  exit 1
}
printf 'Import schema and demo data into %s via %s:%s as %s.\n' \
  "$PGDATABASE" "$PGHOST" "$PGPORT" "$PGUSER"
{
  cat <<'COCO_SQL_GUARD'
DO $$
BEGIN
  IF current_database() <> 'coco_marketplace' THEN
    RAISE EXCEPTION 'Wrong database; expected coco_marketplace';
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'marketplace'
  ) THEN
    RAISE EXCEPTION 'marketplace is not empty; import refused. No objects were removed.';
  END IF;
END;
$$;
COCO_SQL_GUARD
  # Both source files contain their own transaction boundaries. Omit only those
  # standalone lines in the input stream so psql owns ONE transaction for both.
  # PL/pgSQL BEGIN/END blocks remain intact; no file is rewritten.
  awk '!/^[[:space:]]*(BEGIN|COMMIT);[[:space:]]*$/' \
    "$COCO_ROOT/sql/marketplace_schema.sql" "$COCO_ROOT/sql/example_data.sql"
  cat <<'COCO_SQL_VERIFY'
DO $$
BEGIN
  IF (SELECT COUNT(*) FROM marketplace.users) <> 99
     OR NOT EXISTS (SELECT 1 FROM marketplace.users WHERE user_id = 99 AND user_role = 'ADMIN')
     OR (SELECT COUNT(*) FROM marketplace.shops WHERE shop_status = 'APPROVED') <> 3
     OR (SELECT COUNT(*) FROM marketplace.categories) <> 6
     OR (SELECT COUNT(*) FROM marketplace.products) <> 297
     OR (SELECT COUNT(*) FROM marketplace.product_images) <> 2391
     OR (SELECT COUNT(*) FROM marketplace.inventory) <> 297 THEN
    RAISE EXCEPTION 'Unexpected demo data counts or administrator; rolling back import';
  END IF;
END;
$$;
COCO_SQL_VERIFY
} | psql -X "${COCO_PSQL_AUTH[@]}" --set=ON_ERROR_STOP=1 --single-transaction --file=- --output=/dev/null
printf 'Import committed: 99 users, 3 approved shops, 6 categories, 297 products, 2391 images, 297 inventory rows.\n'
