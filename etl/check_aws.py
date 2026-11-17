import sys
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    ProfileNotFound,
)

from common.aws_clients import AWSClients


def check_resources():
    aws = AWSClients()
    settings = aws.settings

    print("=" * 50)
    print("COCO ETL - AWS Infrastructure Check")
    print("=" * 50)

    identity = aws.identity

    print(f"Environment : {settings.environment}")
    print(f"AWS Account : {identity['Account']}")
    print(f"Region      : {settings.region}")
    print(f"IAM Identity: {identity['Arn']}")

    print("\nChecking S3 bucket...")

    aws.s3.head_bucket(
        Bucket=settings.bucket
    )

    print(f"[OK] S3: {settings.bucket}")

    print("\nChecking Glue jobs...")

    for job_name in [
        settings.extract_job,
        settings.transform_job,
    ]:
        aws.glue.get_job(JobName=job_name)

        print(f"[OK] Glue Job: {job_name}")

    print("\nChecking Athena workgroup...")

    aws.athena.get_work_group(
        WorkGroup=settings.athena_workgroup
    )

    print(
        f"[OK] Athena: {settings.athena_workgroup}"
    )

    print("\nChecking Glue Catalog database...")

    aws.glue.get_database(
        Name=settings.athena_database
    )

    print(
        f"[OK] Catalog: {settings.athena_database}"
    )

    print("\nAll configured AWS resources were found.")


def main():
    try:
        check_resources()

    except (
        ClientError,
        NoCredentialsError,
        ProfileNotFound,
        RuntimeError,
        ValueError,
    ) as exc:
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
