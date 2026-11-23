#!/usr/bin/env bash
# Explicit owner entry point. Nothing runs until this script is invoked.
set -euo pipefail
COCO_STACK_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 "$COCO_STACK_ROOT/scripts/aws/dev-stack.py" "$@"
