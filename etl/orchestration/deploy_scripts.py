
import sys
from pathlib import Path
from urllib.parse import urlparse

from common.aws_clients import AWSClients
from common.config import ETL_ROOT


def parse_s3_uri(uri: str):
    parsed = urlparse(uri)

    if parsed.scheme != "s3":
        raise ValueError(f"Not an S3 URI: {uri}")

    return parsed.netloc, parsed.path.lstrip("/")


def main():
    aws = AWSClients()
    settings = aws.settings

    scripts = {
        settings.extract_job:
            ETL_ROOT / "extract" / "extract_postgres.py",

        settings.transform_job:
            ETL_ROOT / "transform" / "transform.py",
    }

    # Check all jobs and destinations before uploading.
    targets = []

    for job_name, local_path in scripts.items():
        if not local_path.is_file():
            raise FileNotFoundError(local_path)

        response = aws.glue.get_job(JobName=job_name)

        script_uri = response["Job"]["Command"]["ScriptLocation"]

        bucket, key = parse_s3_uri(script_uri)

        if bucket != settings.bucket:
            raise RuntimeError(
                f"Unexpected bucket for {job_name}: {bucket}"
            )

        if not key.startswith("scripts/"):
            raise RuntimeError(
                f"Unexpected script key for {job_name}: {key}"
            )

        targets.append((local_path, bucket, key))

    for local_path, bucket, key in targets:
        print(f"Uploading {local_path.name} -> s3://{bucket}/{key}")

        aws.s3.upload_file(
            str(local_path),
            bucket,
            key,
            ExtraArgs={
                "ServerSideEncryption": "AES256",
            },
        )

    print("Both Glue scripts uploaded successfully.")


if __name__ == "__main__":
    main()
