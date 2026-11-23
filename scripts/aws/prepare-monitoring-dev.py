#!/usr/bin/env python3
"""Owner-run: prepare monitoring; optionally store encrypted credentials, never deploy."""

import argparse
import getpass
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
DESTINATION = ROOT / "artifacts/deploy/dev"
PARAMETER = "/ecommerce/dev/monitoring/secrets"
CHART_VERSION = "93.7.0"


def command(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def validate_config(config):
    if re.search(r"example\.(com|org)|REPLACE_|CHANGEME", config, re.I):
        raise ValueError("Fill the SMTP placeholders in artifacts/deploy/dev/alertmanager.yaml first")
    if re.search(r"^\s*smtp_auth_(password|secret)\s*:", config, re.M):
        raise ValueError("Do not inline SMTP passwords; keep smtp_auth_password_file")
    for key in ("smtp_smarthost", "smtp_from", "smtp_auth_username", "to"):
        if not re.search(r"^\s*(?:-\s*)?" + key + r":\s*\S+", config, re.M):
            raise ValueError("Missing Alertmanager field: " + key)
    if not re.search(r"^\s*smtp_require_tls:\s*true\s*(?:#.*)?$", config, re.M):
        raise ValueError("SMTP TLS must remain enabled")
    expected = "/etc/alertmanager/secrets/alertmanager-smtp-auth/password"
    if not re.search(r"^\s*smtp_auth_password_file:\s*[\"']?" + re.escape(expected) +
                     r"[\"']?\s*(?:#.*)?$", config, re.M):
        raise ValueError("Keep the expected smtp_auth_password_file path")


def write_private(path, value):
    descriptor = os.open(path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", action="store_true", help="Store prepared secrets in SSM SecureString")
    parser.add_argument("--reuse-credentials", action="store_true",
                        help="Render with the existing private credential bundle; do not prompt")
    args = parser.parse_args()
    if args.store and args.reuse_credentials:
        parser.error("Choose --store or --reuse-credentials")
    try:
        account = json.loads(command(["aws", "sts", "get-caller-identity", "--region",
                                      "ap-southeast-1", "--output", "json", "--no-cli-pager"]))
        if account["Account"] != "858525799322":
            raise ValueError("Wrong AWS account")
        config = (DESTINATION / "alertmanager.yaml").read_text()
        validate_config(config)
        secret_file = DESTINATION / "monitoring-secrets.json"
        if args.store:
            prepared = json.loads(secret_file.read_text())
            if prepared.get("alertmanager.yaml") != config:
                raise ValueError("Alertmanager config changed; prepare credentials again before --store")
            if set(prepared) != {"alertmanager.yaml", "smtp-password", "grafana-user", "grafana-password"}:
                raise ValueError("Unexpected monitoring credential bundle")
            key = command(["terraform", "-chdir=" + str(ROOT / "terraform/environments/dev"),
                           "output", "-raw", "deployment_secret_kms_key_arn"]).strip()
            if not re.fullmatch(r"arn:aws:kms:ap-southeast-1:858525799322:key/[a-f0-9-]{36}", key):
                raise ValueError("Unexpected dev encryption key")
            result = json.loads(command([
                "aws", "ssm", "put-parameter", "--region", "ap-southeast-1", "--name", PARAMETER,
                "--type", "SecureString", "--tier", "Standard", "--key-id", key,
                "--value", "file://" + str(secret_file), "--overwrite", "--output", "json", "--no-cli-pager",
            ]))
            print("Monitoring SecureString stored, version " + str(result["Version"]))
            return 0
        # Render before asking for credentials; these are local commands only.
        chart = command(["helm", "template", "monitoring", "kube-prometheus-stack", "--repo",
                         "https://prometheus-community.github.io/helm-charts", "--version", CHART_VERSION,
                         "--namespace", "monitoring", "--kube-version", "1.34.0", "--include-crds",
                         "--skip-tests", "-f", str(ROOT / "k8s/monitoring/values-dev.yaml")])
        resources = command(["kubectl", "kustomize", str(ROOT / "k8s/monitoring/resources")])
        if args.reuse_credentials:
            saved = json.loads(secret_file.read_text())
            if saved.get("alertmanager.yaml") != config:
                raise ValueError("Saved SMTP config differs; prepare monitoring credentials first")
            username = saved["grafana-user"]
            password = repeat = saved["grafana-password"]
            smtp = saved["smtp-password"]
        else:
            username = input("Grafana username [admin]: ").strip() or "admin"
            password = getpass.getpass("Grafana password (at least 16 characters): ")
            repeat = getpass.getpass("Repeat Grafana password: ")
            smtp = getpass.getpass("SMTP password/app password: ")
        if password != repeat or len(password) < 16 or not smtp:
            raise ValueError("Passwords do not match, Grafana password too short, or SMTP password empty")
        if any("\n" in value or "\r" in value for value in (username, password, smtp)):
            raise ValueError("Credentials must not contain newlines")
        payload = json.dumps({"alertmanager.yaml": config, "smtp-password": smtp,
                              "grafana-user": username, "grafana-password": password}, ensure_ascii=False)
        if len(payload.encode()) > 4096:
            raise ValueError("Monitoring credential bundle exceeds the Standard SSM limit")
        DESTINATION.mkdir(parents=True, exist_ok=True)
        write_private(secret_file, payload)
        (DESTINATION / "monitoring-chart.yaml").write_text(chart)
        (DESTINATION / "monitoring-resources.yaml").write_text(resources)
        print("Prepared monitoring files. Passwords saved privately, not printed. No deployment performed.")
        return 0
    except subprocess.CalledProcessError as exc:
        # In --store mode the request contains a private file; never dump command output.
        print("Monitoring preparation command failed: " + str(exc.cmd[:3]), file=sys.stderr)
        return 1
    except (ValueError, OSError, EOFError, KeyError) as exc:
        print("Monitoring preparation stopped: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
