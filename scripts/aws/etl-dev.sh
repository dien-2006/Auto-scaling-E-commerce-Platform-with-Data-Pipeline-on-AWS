#!/usr/bin/env bash
# Owner-run ETL entry points. Only the selected action runs; never runs SQL on RDS.
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"
require_command uv
export COCO_ETL_ENV_FILE="$COCO_REPO_ROOT/artifacts/deploy/dev/etl.env"
export PYTHONPATH="$COCO_REPO_ROOT/etl"
COCO_ETL_ACTION="${1:-help}"
if (( $# > 0 )); then shift; fi
run_python() {
  uv run --no-project --with-requirements "$COCO_REPO_ROOT/etl/requirements.txt" python "$@"
}
if [[ "$COCO_ETL_ACTION" != test && "$COCO_ETL_ACTION" != help && ! -f "$COCO_ETL_ENV_FILE" ]]; then
  printf 'Prepare artifacts/deploy/dev/etl.env from Terraform outputs first.\n' >&2
  exit 1
fi
case "$COCO_ETL_ACTION" in
  test) run_python -m unittest discover -s "$COCO_REPO_ROOT/etl/tests" -v ;;
  check) run_python "$COCO_REPO_ROOT/etl/check_aws.py" ;;
  upload) run_python -m orchestration.deploy_scripts ;;
  setup) run_python -m extract.setup_workflow --disable-schedule "$@" ;;
  enable-schedule) run_python -m extract.setup_workflow --enable-schedule "$@" ;;
  disable-schedule) run_python -m extract.setup_workflow --disable-schedule "$@" ;;
  run) run_python -m extract.run_workflow --watch "$@" ;;
  finish) run_python -m orchestration.complete_pipeline "$@" ;;
  publish) run_python -m athena.create_tables "$@" ;;
  report) run_python -m athena.run_queries "$@" ;;
  *) printf 'Usage: bash scripts/aws/etl-dev.sh {test|check|setup|upload|run|finish|publish|report|enable-schedule|disable-schedule} [arguments]\n' ;;
esac
