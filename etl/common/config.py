import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ETL_ROOT = Path(__file__).resolve().parents[1]

CONFIG_FILE = os.getenv("COCO_ETL_ENV_FILE")
# An explicitly selected Terraform-generated configuration is authoritative.
# The legacy etl/.env retains the usual environment-variable precedence.
load_dotenv(CONFIG_FILE or ETL_ROOT / ".env", override=bool(CONFIG_FILE))


def required(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise ValueError(f"Missing environment variable: {name}")

    return value


@dataclass(frozen=True)
class Settings:
    environment: str
    region: str
    profile: str | None
    account_id: str
    bucket: str

    extract_job: str
    transform_job: str
    workflow: str

    athena_database: str
    athena_workgroup: str
    schedule: str


def get_settings() -> Settings:
    env = required("COCO_ENV")

    if env not in ("dev", "prod"):
        raise ValueError("COCO_ENV must be dev or prod")

    account = required("AWS_ACCOUNT_ID")

    if len(account) != 12 or not account.isdigit():
        raise ValueError("Invalid AWS_ACCOUNT_ID")

    return Settings(
        environment=env,
        region=required("AWS_REGION"),
        profile=os.getenv("AWS_PROFILE") or None,
        account_id=account,
        bucket=required("ETL_BUCKET"),
        extract_job=required("GLUE_EXTRACT_JOB"),
        transform_job=required("GLUE_TRANSFORM_JOB"),
        workflow=required("GLUE_WORKFLOW"),
        athena_database=required("ATHENA_DATABASE"),
        athena_workgroup=required("ATHENA_WORKGROUP"),
        schedule=required("GLUE_SCHEDULE"),
    )
