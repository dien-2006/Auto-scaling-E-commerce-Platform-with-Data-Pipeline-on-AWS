#!/usr/bin/env python3
"""Owner-run: write non-secret ETL configuration from the applied Terraform outputs."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    try:
        result = subprocess.run(["terraform", "-chdir=" + str(ROOT / "terraform/environments/dev"),
                                 "output", "-json", "etl_config"],
                                check=True, capture_output=True, text=True)
        config = json.loads(result.stdout)
        if config.get("AWS_ACCOUNT_ID") != "858525799322" or config.get("AWS_REGION") != "ap-southeast-1" or config.get("COCO_ENV") != "dev":
            raise ValueError("Unexpected dev account, region or environment")
        for key, value in config.items():
            if not re.fullmatch(r"[A-Z_]+", key) or not isinstance(value, str) or any(c in value for c in "\r\n'\""):
                raise ValueError("Invalid ETL configuration output")
        if config.get("GLUE_SCHEDULE") != "cron(0 18 * * ? *)":
            raise ValueError("Applied etl_config still has an old schedule. Review/apply a NEW etl-dev.tfplan first; expected 01:00 Vietnam (18:00 UTC). Existing etl.env was not overwritten")
        destination = ROOT / "artifacts/deploy/dev/etl.env"
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(destination, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write("# Generated from dev Terraform outputs. No AWS keys or DB passwords.\n")
            stream.write("\n".join(f"{key}='{value}'" for key, value in sorted(config.items())) + "\n")
        print("Prepared artifacts/deploy/dev/etl.env; original etl/.env was not modified.")
        return 0
    except subprocess.CalledProcessError as exc:
        print("Could not read applied Terraform output etl_config:", file=sys.stderr)
        print((exc.stderr or "Terraform output command failed").strip(), file=sys.stderr)
        print("Create a NEW plan with scripts/aws/plan-etl-dev.sh, review/apply etl-dev.tfplan, then retry. No ETL config was written.", file=sys.stderr)
        return 1
    except (ValueError, OSError) as exc:
        print("ETL configuration preparation failed: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
