#!/usr/bin/env python3
"""Owner-run: render deployment files and read RDS secret into a private local file.

Does not write AWS resources or SQL, and does not modify the original .env.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
DESTINATION = ROOT / "artifacts/deploy/dev"
REGION = "ap-southeast-1"


class ConfigurationError(ValueError):
    """Safe messages that contain setting names, never credential values."""


def command(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def env_values(path):
    values = {}
    if not path.is_file():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.removeprefix("export ").partition("=")
        if separator:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[key.strip()] = value
    return values


def write_private(path, content):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(content)


def prepare(tag, smtp_env):
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}", tag):
        raise ConfigurationError("Invalid image tag")
    outputs = json.loads(command([
        "terraform", "-chdir=" + str(ROOT / "terraform/environments/dev"), "output", "-json"
    ]))

    def output(name):
        return str(outputs[name]["value"])

    bucket = output("images_bucket_name")
    if bucket != "ecommerce-dev-product-images-858525799322-ap-southeast-1":
        raise ConfigurationError("Unexpected dev bucket/account")
    account = json.loads(command(["aws", "sts", "get-caller-identity", "--output", "json"]))["Account"]
    if account != "858525799322":
        raise ConfigurationError("Wrong AWS account")
    origin = "http://" + output("alb_dns_name")
    cdn = output("cloudfront_images_url").rstrip("/")
    if not re.fullmatch(r"http://[a-zA-Z0-9.-]+", origin) or not re.fullmatch(r"https://[a-zA-Z0-9.-]+", cdn):
        raise ConfigurationError("Unexpected ALB or CDN output")

    secret_path = DESTINATION / "backend-secret.env"
    existing = env_values(secret_path)
    smtp = env_values(smtp_env)
    smtp_keys = ("MARKETPLACE_SMTP_HOST", "MARKETPLACE_SMTP_USERNAME",
                 "MARKETPLACE_SMTP_PASSWORD", "MARKETPLACE_OTP_FROM_EMAIL")
    missing = [key for key in smtp_keys if not smtp.get(key)]
    if missing:
        raise ConfigurationError("Missing SMTP settings in private env: " + ", ".join(missing))
    secret = json.loads(json.loads(command([
        "aws", "secretsmanager", "get-secret-value", "--region", REGION,
        "--secret-id", output("rds_master_secret_arn"), "--output", "json", "--no-cli-pager"
    ]))["SecretString"])
    values = {
        "MARKETPLACE_DB_HOST": output("rds_endpoint"),
        "MARKETPLACE_DB_PORT": output("rds_port"),
        "MARKETPLACE_DB_NAME": output("rds_database_name"),
        "MARKETPLACE_DB_USER": secret["username"],
        "MARKETPLACE_DB_PASSWORD": secret["password"],
    }
    for key in ("MARKETPLACE_JWT_SECRET", "MARKETPLACE_PROXY_SECRET", "MARKETPLACE_OTP_SECRET"):
        values[key] = existing.get(key) or secrets.token_urlsafe(48)
    values.update({key: smtp[key] for key in smtp_keys})
    values["MARKETPLACE_SMTP_PORT"] = smtp.get("MARKETPLACE_SMTP_PORT") or "587"
    values["MARKETPLACE_SMTP_SECURITY"] = smtp.get("MARKETPLACE_SMTP_SECURITY") or "STARTTLS"
    if values["MARKETPLACE_SMTP_SECURITY"] not in {"TLS", "STARTTLS"}:
        raise ConfigurationError("Invalid SMTP security")
    if not 1 <= int(values["MARKETPLACE_SMTP_PORT"]) <= 65535:
        raise ConfigurationError("Invalid SMTP port")
    if any("\n" in value or "\r" in value for value in values.values()):
        raise ConfigurationError("Multiline secrets cannot be stored in an env file")
    secret_text = "".join(key + "=" + value + "\n" for key, value in values.items())
    if len(secret_text.encode()) > 4096:
        raise ConfigurationError("Secret exceeds the Standard SSM parameter size")

    manifest = command(["kubectl", "kustomize", str(ROOT / "k8s/overlays/dev")])
    for name, placeholder in (("backend", "ACCOUNT_ID.dkr.ecr.ap-southeast-1.amazonaws.com/ecommerce/dev/backend:v1.0.0"),
                              ("frontend", "ACCOUNT_ID.dkr.ecr.ap-southeast-1.amazonaws.com/ecommerce/dev/frontend:v1.0.0")):
        repository = output("ecr_" + name + "_url")
        if repository != "858525799322.dkr.ecr.ap-southeast-1.amazonaws.com/ecommerce/dev/" + name:
            raise ConfigurationError("Unexpected ECR repository")
        manifest = manifest.replace(placeholder, repository + ":" + tag)
    manifest = manifest.replace("http://REPLACE_WITH_DEV_ALB", origin)
    manifest = manifest.replace("https://REPLACE_WITH_CLOUDFRONT", cdn)
    revision = hashlib.sha256((secret_text + origin + cdn + tag).encode()).hexdigest()
    manifest = manifest.replace("REPLACE_WITH_RUNTIME_CHECKSUM", revision)
    if "REPLACE_" in manifest or "ACCOUNT_ID" in manifest:
        raise ConfigurationError("Unresolved placeholders in rendered manifest")
    metrics = command(["kubectl", "kustomize", str(ROOT / "k8s/metrics-server/dev")])
    DESTINATION.mkdir(parents=True, exist_ok=True, mode=0o700)
    write_private(secret_path, secret_text)
    (DESTINATION / "application.yaml").write_text(manifest)
    (DESTINATION / "metrics-server.yaml").write_text(metrics)
    (DESTINATION / "release.json").write_text(json.dumps({"tag": tag, "origin": origin, "bucket": bucket}, indent=2))
    print("Prepared release files in artifacts/deploy/dev; secret values were not printed.")
    print("Web origin: " + origin)
    print("RDS schema/data must be prepared manually by the owner; no SQL was run.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--smtp-env", type=Path, default=ROOT / ".env")
    args = parser.parse_args()
    try:
        prepare(args.tag, args.smtp_env)
        return 0
    except subprocess.CalledProcessError as exc:
        print("Preparation failed at " + str(exc.cmd[:3]) + "; no secret values printed.", file=sys.stderr)
        return 1
    except ConfigurationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (ValueError, KeyError, OSError):
        print("Preparation failed: check account, Terraform outputs, SMTP env and required tools. No secret values printed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
