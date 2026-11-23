#!/usr/bin/env python3
"""Kubelet credentialprovider/v1 adapter using the node role through AWS CLI v2.

Default: stdin request -> stdout response, never log credentials.
--install: install kubelet config/drop-in on an Ubuntu kubeadm node (root only).
"""

import base64
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

PROVIDER = "coco-ecr-credential-provider"
REGISTRY = re.compile(r"([0-9]{12})\.dkr\.ecr\.(ap-southeast-1)\.amazonaws\.com\Z")


def credentials(request, run=subprocess.run):
    if request.get("kind") != "CredentialProviderRequest" or request.get("apiVersion") != (
        "credentialprovider.kubelet.k8s.io/v1"
    ):
        raise ValueError("unsupported request")
    image = request.get("image", "")
    if not isinstance(image, str) or len(image) > 4096:
        raise ValueError("invalid image")
    host = image.split("/", 1)[0]
    match = REGISTRY.fullmatch(host)
    if not match:
        raise ValueError("unsupported registry")
    account, region = match.groups()
    aws = shutil.which("aws")
    if not aws:
        raise ValueError("AWS CLI is missing")
    result = run(
        [aws, "ecr", "get-authorization-token", "--region", region,
         "--registry-ids", account, "--output", "json", "--no-cli-pager"],
        check=True, capture_output=True, text=True, timeout=25,
    )
    rows = json.loads(result.stdout)["authorizationData"]
    row = next(row for row in rows if row["proxyEndpoint"] == "https://" + host)
    username, password = base64.b64decode(row["authorizationToken"], validate=True).decode().split(":", 1)
    if username != "AWS" or not password:
        raise ValueError("invalid ECR response")
    return {
        "apiVersion": "credentialprovider.kubelet.k8s.io/v1",
        "kind": "CredentialProviderResponse",
        "cacheKeyType": "Registry",
        "cacheDuration": "10m",
        "auth": {host: {"username": username, "password": password}},
    }


def install():
    if os.geteuid() != 0 or not shutil.which("kubelet"):
        raise ValueError("install requires root on a kubeadm node")
    binary_dir = Path("/usr/local/libexec/kubelet-credential-providers")
    binary_dir.mkdir(parents=True, exist_ok=True)
    target = binary_dir / PROVIDER
    source = Path(__file__).resolve()
    if source != target:
        target.write_text(source.read_text())
    target.chmod(0o755)
    config = Path("/etc/kubernetes/coco-credential-provider.json")
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps({
        "apiVersion": "kubelet.config.k8s.io/v1",
        "kind": "CredentialProviderConfig",
        "providers": [{
            "name": PROVIDER,
            "matchImages": ["*.dkr.ecr.ap-southeast-1.amazonaws.com"],
            "defaultCacheDuration": "10m",
            "apiVersion": "credentialprovider.kubelet.k8s.io/v1",
        }],
    }, indent=2) + "\n")
    dropin = Path("/etc/systemd/system/kubelet.service.d/20-coco-ecr.conf")
    dropin.parent.mkdir(parents=True, exist_ok=True)
    # Preserve kubeadm's environment/flags and append only the provider settings.
    dropin.write_text(
        '[Service]\n'
        'Environment="COCO_ECR_ARGS=--image-credential-provider-config='
        '/etc/kubernetes/coco-credential-provider.json '
        '--image-credential-provider-bin-dir=/usr/local/libexec/kubelet-credential-providers"\n'
        'ExecStart=\n'
        'ExecStart=/usr/bin/kubelet $KUBELET_KUBECONFIG_ARGS $KUBELET_CONFIG_ARGS '
        '$KUBELET_KUBEADM_ARGS $KUBELET_EXTRA_ARGS $COCO_ECR_ARGS $COCO_AWS_NODE_ARGS\n'
    )
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    if Path("/etc/kubernetes/kubelet.conf").is_file():
        subprocess.run(["systemctl", "restart", "kubelet"], check=True)
    print("ECR credential provider installed; verify a real image pull before deployment.")


def main():
    try:
        if sys.argv[1:] == ["--install"]:
            install()
        elif not sys.argv[1:]:
            raw = sys.stdin.read(16385)
            if len(raw) > 16384:
                raise ValueError("request too large")
            print(json.dumps(credentials(json.loads(raw))))
        else:
            raise ValueError("unsupported arguments")
        return 0
    except Exception:
        # Never print AWS CLI output, input payloads, authorization tokens or passwords.
        print("ECR credential provider failed; check installation, node IAM and AWS connectivity.",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
