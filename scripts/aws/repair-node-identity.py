#!/usr/bin/env python3
"""Owner-run: preview/patch AWS node identity via SSM. No SQL or EC2 replacement."""

import argparse
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import sys

REGION = "ap-southeast-1"
ACCOUNT = "858525799322"
ROOT = Path(__file__).resolve().parents[2]


def command(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def aws(*args):
    return json.loads(command(["aws", *args, "--region", REGION,
                               "--output", "json", "--no-cli-pager"]))


def repair_script(records):
    # All records come from the filtered EC2 API and are validated before here.
    return """set -eu
export KUBECONFIG=/etc/kubernetes/admin.conf
kubectl wait --for=condition=Ready nodes --all --timeout=300s
python3 <<'COCO_IDENTITY_REPAIR'
import json
import subprocess
""" + "records = " + repr(records) + "\n" + """
def kubectl(*args):
    return subprocess.check_output(['kubectl', *args], text=True)

nodes = json.loads(kubectl('get', 'nodes', '-o', 'json'))['items']
by_ip = {r['ip']: r for r in records}
updates = []
seen = set()
for node in nodes:
    ips = [a['address'] for a in node['status']['addresses'] if a['type'] == 'InternalIP']
    matches = [by_ip[ip] for ip in ips if ip in by_ip]
    if len(matches) != 1:
        raise SystemExit('Node/IP does not match the dev EC2 inventory; no patches submitted')
    record = matches[0]
    if record['id'] in seen:
        raise SystemExit('Multiple nodes match one EC2 instance; no patches submitted')
    seen.add(record['id'])
    provider = 'aws:///' + record['az'] + '/' + record['id']
    if node.get('spec', {}).get('providerID') not in (None, '', provider):
        raise SystemExit('Conflicting provider ID; no patches submitted')
    labels = {'topology.kubernetes.io/region': 'ap-southeast-1',
              'topology.kubernetes.io/zone': record['az'],
              'node.kubernetes.io/instance-type': record['type']}
    for key, value in labels.items():
        if node['metadata'].get('labels', {}).get(key) not in (None, value):
            raise SystemExit('Conflicting AWS label; no patches submitted')
    updates.append((node['metadata']['name'], {'spec': {'providerID': provider},
                    'metadata': {'labels': labels}}))
if seen != {r['id'] for r in records}:
    raise SystemExit('EC2 inventory does not match all registered nodes; no patches submitted')
# Validate the whole inventory before the first write. Re-running is idempotent.
for name, patch in updates:
    print(kubectl('patch', 'node', name, '--type=merge', '-p', json.dumps(patch)), end='')
print(kubectl('get', 'nodes', '-L', 'topology.kubernetes.io/zone'))
COCO_IDENTITY_REPAIR
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submit", action="store_true", help="Submit the reviewed patch via SSM")
    args = parser.parse_args()
    try:
        if aws("sts", "get-caller-identity")["Account"] != ACCOUNT:
            raise ValueError("Wrong AWS account")
        vpc = command(["terraform", "-chdir=" + str(ROOT / "terraform/environments/dev"),
                       "output", "-raw", "vpc_id"]).strip()
        result = aws("ec2", "describe-instances", "--filters",
                     "Name=tag:Name,Values=ecommerce-dev-control-plane,ecommerce-dev-worker",
                     "Name=instance-state-name,Values=running", "Name=vpc-id,Values=" + vpc)
        records, controls = [], []
        for reservation in result["Reservations"]:
            for instance in reservation["Instances"]:
                name = next(t["Value"] for t in instance["Tags"] if t["Key"] == "Name")
                record = {"id": instance["InstanceId"], "ip": instance["PrivateIpAddress"],
                          "az": instance["Placement"]["AvailabilityZone"],
                          "type": instance["InstanceType"]}
                ipaddress.IPv4Address(record["ip"])
                if not (re.fullmatch(r"i-[0-9a-f]{17}", record["id"]) and
                        record["az"] in {"ap-southeast-1a", "ap-southeast-1b"} and
                        re.fullmatch(r"[a-z0-9]+\.[a-z0-9]+", record["type"])):
                    raise ValueError("Unexpected dev EC2 identity")
                records.append(record)
                if name == "ecommerce-dev-control-plane":
                    controls.append(record["id"])
        if len(controls) != 1 or len(records) < 3:
            raise ValueError("Expected one control plane and at least two workers")
        print(json.dumps(records, indent=2))
        if not args.submit:
            print("Preview only. To patch these Kubernetes nodes, re-run with --submit.")
            return 0
        result = aws("ssm", "send-command", "--instance-ids", controls[0],
                     "--document-name", "AWS-RunShellScript", "--parameters",
                     json.dumps({"commands": [repair_script(records)], "executionTimeout": ["600"]}))
        command_id = result["Command"]["CommandId"]
        print("Command ID: " + command_id)
        print("Check with: python3 scripts/aws/run-dev-task.py status " + command_id)
        return 0
    except subprocess.CalledProcessError as exc:
        print("Command failed: " + str(exc.cmd[:3]), file=sys.stderr)
        print(exc.stderr.strip(), file=sys.stderr)
        return 1
    except (ValueError, KeyError, StopIteration, OSError) as exc:
        print("Identity repair stopped: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
