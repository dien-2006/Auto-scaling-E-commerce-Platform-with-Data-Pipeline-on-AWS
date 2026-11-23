#!/usr/bin/env python3
"""Owner-run destroy/recreate of this dev stack, using AWS CLI and existing scripts.

No backup is made. SQL source files are never edited. Automatic SQL import is
limited to the new RDS generation created by `up`, with an empty-schema guard.
"""
import argparse
import contextlib
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
TF = ROOT / "terraform/environments/dev"
DEST = ROOT / "artifacts/deploy/dev"
RECORD = DEST / "stack-lifecycle.json"
ACCOUNT = "858525799322"
REGION = "ap-southeast-1"
CLUSTER = "ecommerce-dev-k8s"
WORKFLOW = "ecommerce-dev-pipeline"
DB = "ecommerce-dev-postgresql"
BUCKETS = {f"ecommerce-dev-{kind}-{ACCOUNT}-{REGION}" for kind in ("product-images", "data-lake")}
REPOS = {"ecommerce/dev/backend", "ecommerce/dev/frontend"}
PARAMETERS = {"/ecommerce/dev/application/backend-env", "/ecommerce/dev/monitoring/secrets",
              "/ecommerce/dev/kubernetes/worker-join"}
ENV = {**os.environ, "AWS_REGION": REGION, "AWS_DEFAULT_REGION": REGION,
       "AWS_PAGER": "", "TF_IN_AUTOMATION": "1", "TF_INPUT": "0"}


class Failure(RuntimeError):
    pass


def run(args, *, capture=False, env=None, input_text=None):
    result = subprocess.run([str(a) for a in args], cwd=ROOT, env=env or ENV,
                            input=input_text, text=True, capture_output=capture)
    if result.returncode:
        # Captured commands can carry secrets: never echo argv/stdout/stderr.
        code = re.search(r"An error occurred \(([A-Za-z0-9_.-]+)\)", result.stderr or "") if capture else None
        detail = " (AWS " + code[1] + ")" if code else ""
        raise Failure("Command failed: " + str(args[0]) + detail + "; inspect the preceding output or AWS task ID")
    return result.stdout if capture else ""


def aws(*args):
    result = run(["aws", *args, "--region", REGION, "--output", "json", "--no-cli-pager"], capture=True)
    return json.loads(result) if result.strip() else {}


def tf(*args, capture=False):
    return run(["terraform", "-chdir=" + str(TF), *args], capture=capture)


def resources(document):
    def visit(module):
        for resource in module.get("resources", []):
            if resource.get("mode") == "managed":
                yield resource
        for child in module.get("child_modules", []):
            yield from visit(child)
    return list(visit(document.get("values", {}).get("root_module", {})))


def private_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".stack-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_record():
    value = json.loads(RECORD.read_text()) if RECORD.exists() else {}
    if value and (value.get("account"), value.get("region")) != (ACCOUNT, REGION):
        raise Failure("Lifecycle record belongs to another account/region")
    return value


def save(record):
    private_json(RECORD, record)


def new_record(mode):
    return {"account": ACCOUNT, "region": REGION, "mode": mode,
            "generation": uuid.uuid4().hex, "done": [], "commands": {}}


def validate_plan(plan, destroy):
    allowed = ("no-op", "delete") if destroy else ("no-op", "create")
    for change in plan.get("resource_changes", []):
        if change.get("mode") == "data":
            continue
        actions = change["change"]["actions"]
        if len(actions) != 1 or actions[0] not in allowed:
            raise Failure("Unexpected Terraform actions at " + change["address"] + ": " + str(actions))


def apply_plan(destroy=False):
    name = "stack-destroy.tfplan" if destroy else "stack-up.tfplan"
    tf("plan", *(["-destroy"] if destroy else []), "-input=false",
       "-var=aws_region=" + REGION, "-out=" + name)
    validate_plan(json.loads(tf("show", "-json", name, capture=True)), destroy)
    tf("apply", "-input=false", name)


def output(name):
    return tf("output", "-raw", name, capture=True).strip()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def preflight_rebuild(check_docker=True):
    for tool in ("docker", "kubectl", "helm", "uv", "psql", "session-manager-plugin"):
        if not shutil.which(tool):
            raise Failure("Missing tool: " + tool)
    if check_docker:
        run(["docker", "info"], capture=True)
    for source in ("sql/marketplace_schema.sql", "sql/example_data.sql"):
        if not (ROOT / source).is_file():
            raise Failure("Missing local source: " + source)
    for number in (1, 2, 3):
        if not (ROOT / f"data health/logo/{number}.png").is_file():
            raise Failure("Missing shop logo: data health/logo/" + str(number) + ".png")
    images = ROOT / "data health/ProductImages"
    if not images.is_dir() or not any(images.rglob("*.jpg")):
        raise Failure("Missing local product images")
    release = load_module("stack_release", ROOT / "scripts/aws/prepare-dev-release.py")
    smtp = release.env_values(ROOT / ".env")
    for key in ("MARKETPLACE_SMTP_HOST", "MARKETPLACE_SMTP_USERNAME",
                "MARKETPLACE_SMTP_PASSWORD", "MARKETPLACE_OTP_FROM_EMAIL"):
        if not smtp.get(key):
            raise Failure("Missing private .env setting: " + key)
    monitoring = load_module("stack_monitoring", ROOT / "scripts/aws/prepare-monitoring-dev.py")
    config = (DEST / "alertmanager.yaml").read_text()
    monitoring.validate_config(config)
    bundle_path = DEST / "monitoring-secrets.json"
    bundle = json.loads(bundle_path.read_text())
    if (set(bundle) != {"alertmanager.yaml", "smtp-password", "grafana-user", "grafana-password"}
            or bundle["alertmanager.yaml"] != config
            or any(not isinstance(v, str) or not v for v in bundle.values())
            or len(bundle["grafana-password"]) < 16):
        raise Failure("Prepare matching monitoring credentials/config before using stack commands")
    os.chmod(bundle_path, 0o600)
    print("Local rebuild inputs present; no credentials printed.", flush=True)


def stage(record, name, action):
    if name in record["done"]:
        print("Already completed: " + name, flush=True)
        return
    print("Starting: " + name, flush=True)
    action()
    record["done"].append(name)
    save(record)
    print("Completed: " + name, flush=True)


def wait_until(description, check, seconds=1800):
    deadline = time.monotonic() + seconds
    while True:
        if check():
            return
        if time.monotonic() >= deadline:
            raise Failure("Timed out: " + description + "; rerun the same command to resume")
        print("Waiting: " + description, flush=True)
        time.sleep(10)


def wait_ssm(command_id, seconds=5400):
    print("SSM command: " + command_id, flush=True)
    def ready():
        parent = aws("ssm", "list-commands", "--command-id", command_id).get("Commands", [])
        rows = aws("ssm", "list-command-invocations", "--command-id", command_id).get("CommandInvocations", [])
        statuses = [row["Status"] for row in rows] + [p["Status"] for p in parent]
        if any(s in {"Failed", "TimedOut", "Cancelled"} for s in statuses):
            raise Failure("SSM task failed: " + command_id + "; inspect get-command-invocation before retrying")
        return bool(parent and parent[0].get("TargetCount", 0) > 0 and
                    len(rows) == parent[0]["TargetCount"] and all(s == "Success" for s in statuses))
    wait_until("SSM " + command_id, ready, seconds)


def ssm_script(record, name, instance, script, seconds=1800):
    if name not in record["commands"]:
        result = aws("ssm", "send-command", "--instance-ids", instance,
                     "--document-name", "AWS-RunShellScript", "--parameters", json.dumps({
                         "commands": ["bash <<'COCO_STACK'\nset -euo pipefail\n" + script + "\nCOCO_STACK"],
                         "executionTimeout": [str(seconds)],
                     }))
        record["commands"][name] = result["Command"]["CommandId"]
        save(record)
    wait_ssm(record["commands"][name], seconds + 120)


def task(record, name):
    key = "task-" + name
    if key not in record["commands"]:
        result = run([sys.executable, ROOT / "scripts/aws/run-dev-task.py", name], capture=True)
        print(result, end="", flush=True)
        match = re.search(r"Command ID: ([a-f0-9-]{36})", result)
        if not match:
            raise Failure("No SSM command ID returned for task " + name)
        record["commands"][key] = match[1]
        save(record)
    wait_ssm(record["commands"][key])


def python_script(name, *args):
    run([sys.executable, ROOT / "scripts/aws" / name, *args])


def bash_script(name, *args):
    run(["bash", ROOT / "scripts/aws" / name, *args])


def control_plane():
    state = resources(json.loads(tf("show", "-json", capture=True)))
    values = [r["values"] for r in state if r["address"] == "module.kubernetes.aws_instance.control_plane"]
    if len(values) != 1:
        raise Failure("Expected one control plane in current dev Terraform state")
    return values[0]["id"]


def cluster_ready(record):
    instance = control_plane()
    wait_until("control plane SSM Online", lambda: any(
        row.get("PingStatus") == "Online" for row in aws(
            "ssm", "describe-instance-information", "--filters",
            json.dumps([{"Key": "InstanceIds", "Values": [instance]}])).get("InstanceInformationList", [])))
    ssm_script(record, "bootstrap", instance, """
cloud-init status --wait
export KUBECONFIG=/etc/kubernetes/admin.conf
for attempt in {1..180}; do
  if kubectl get nodes -o json | python3 -c '
import json,sys
nodes=json.load(sys.stdin)["items"]
workers=[n for n in nodes if "node-role.kubernetes.io/control-plane" not in n["metadata"].get("labels",{})]
ready=lambda n:any(c["type"]=="Ready" and c["status"]=="True" for c in n.get("status",{}).get("conditions",[]))
zones={n["metadata"].get("labels",{}).get("topology.kubernetes.io/zone") for n in workers}
sys.exit(0 if len(workers)>=2 and all(ready(n) for n in nodes) and zones=={"ap-southeast-1a","ap-southeast-1b"} else 1)
'; then
    kubectl -n kube-system rollout status deployment/coredns --timeout=300s
    kubectl get nodes -o wide
    exit 0
  fi
  sleep 10
done
exit 1
""", seconds=2400)


def import_new_database(record):
    database = aws("rds", "describe-db-instances", "--db-instance-identifier", DB)["DBInstances"][0]
    identity = database["DbiResourceId"]
    if record.get("rds_resource_id") not in (None, identity):
        raise Failure("RDS identity changed during rebuild; refusing automatic SQL")
    record["rds_resource_id"] = identity
    save(record)
    endpoint = output("rds_endpoint")
    if database["Endpoint"]["Address"] != endpoint or output("rds_database_name") != "coco_marketplace":
        raise Failure("RDS output/identity mismatch")
    secret = json.loads(aws("secretsmanager", "get-secret-value", "--secret-id",
                            output("rds_master_secret_arn"))["SecretString"])
    with tempfile.TemporaryDirectory(prefix="coco-db-") as directory:
        pgpass = Path(directory) / "pgpass"
        escape = lambda value: str(value).replace("\\", "\\\\").replace(":", "\\:")
        pgpass.write_text(":".join(escape(v) for v in (
            "127.0.0.1", "15432", "coco_marketplace", secret["username"], secret["password"])) + "\n")
        os.chmod(pgpass, 0o600)
        env = {**ENV, "PGHOST": "127.0.0.1", "PGPORT": "15432", "PGDATABASE": "coco_marketplace",
               "PGUSER": secret["username"], "PGPASSFILE": str(pgpass), "PGSSLMODE": "require",
               "PGCONNECT_TIMEOUT": "5"}
        for inherited in ("PGPASSWORD", "PGSERVICE", "PGSERVICEFILE", "PGOPTIONS"):
            env.pop(inherited, None)
        # Refuse to attach to somebody else's tunnel on the same local port.
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 15432))
        tunnel = subprocess.Popen([
            "aws", "ssm", "start-session", "--region", REGION, "--target", control_plane(),
            "--document-name", "AWS-StartPortForwardingSessionToRemoteHost", "--parameters",
            json.dumps({"host": [endpoint], "portNumber": ["5432"], "localPortNumber": ["15432"]}),
        ], env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        try:
            def connected():
                if tunnel.poll() is not None:
                    raise Failure("RDS tunnel exited; check Session Manager plugin and port 15432")
                result = subprocess.run(["psql", "-X", "-w", "-Atc", "SELECT 1"], env=env,
                                        capture_output=True, text=True)
                return result.returncode == 0 and result.stdout.strip() == "1"
            wait_until("new RDS tunnel", connected, 180)
            # Handle a lost local checkpoint after a successful atomic commit.
            count = run(["psql", "-X", "-w", "-Atc",
                         "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                         "WHERE n.nspname='marketplace'"], capture=True, env=env).strip()
            if count == "0":
                run(["bash", ROOT / "scripts/db/init-rds-dev.sh", "--non-interactive"], env=env)
            else:
                if "db-import-started" not in record:
                    raise Failure("Unexpected existing marketplace objects; no SQL imported")
                expected = run(["psql", "-X", "-w", "-Atc",
                    "SELECT (SELECT count(*) FROM marketplace.users)=99 AND "
                    "(SELECT count(*) FROM marketplace.shops WHERE shop_status='APPROVED')=3 AND "
                    "(SELECT count(*) FROM marketplace.categories)=6 AND "
                    "(SELECT count(*) FROM marketplace.products)=297 AND "
                    "(SELECT count(*) FROM marketplace.product_images)=2391 AND "
                    "(SELECT count(*) FROM marketplace.inventory)=297"], capture=True, env=env).strip()
                if expected != "t":
                    raise Failure("Existing objects differ from expected seed; no tables modified")
        finally:
            # Kill only this script's process group, including its plugin child.
            import signal
            with contextlib.suppress(ProcessLookupError):
                os.killpg(tunnel.pid, signal.SIGTERM)
            with contextlib.suppress(subprocess.TimeoutExpired):
                tunnel.wait(timeout=10)


def up(record):
    preflight_rebuild()
    existing = resources(json.loads(tf("show", "-json", capture=True)))
    if record.get("mode") == "destroying":
        raise Failure("Destroy is incomplete; finish destroy --delete-data before up")
    if record.get("mode") not in {"building", "ready"}:
        if existing:
            raise Failure("Existing stack found; up recreates only an empty dev stack. Use destroy first")
        record = new_record("building")
        record["sql_sha256"] = sql_digest()
        save(record)
    if record.get("sql_sha256") != sql_digest():
        raise Failure("SQL source changed during rebuild; inspect lifecycle record")
    if record["mode"] == "ready":
        if not existing:
            raise Failure("Recorded stack no longer exists; finish destroy --delete-data to reset its generation")
        print("This generation is already deployed. Use your web/Grafana URLs; up does not rebuild a live stack.")
        return
    stage(record, "terraform", apply_plan)
    stage(record, "cluster", lambda: cluster_ready(record))
    if "database" not in record["done"]:
        record["db-import-started"] = True
        save(record)
    stage(record, "database", lambda: import_new_database(record))
    def images():
        tag = record.get("tag") or ("rebuild-" + record["generation"])
        record["tag"] = tag
        save(record)
        found = []
        for repo in sorted(REPOS):
            rows = aws("ecr", "list-images", "--repository-name", repo).get("imageIds", [])
            found.append(any(row.get("imageTag") == tag for row in rows))
        if all(found):
            return
        if any(found):
            tag = "rebuild-" + uuid.uuid4().hex
        record["tag"] = tag
        save(record)
        bash_script("build-push-dev.sh", tag)
    stage(record, "images", images)
    stage(record, "release", lambda: python_script("prepare-dev-release.py", "--tag", record["tag"]))
    def backend_secret():
        aws("ssm", "put-parameter", "--name", "/ecommerce/dev/application/backend-env",
            "--type", "SecureString", "--tier", "Standard", "--key-id", output("deployment_secret_kms_key_arn"),
            "--value", "file://" + str(DEST / "backend-secret.env"), "--overwrite")
    stage(record, "backend-secret", backend_secret)
    stage(record, "catalog-images", lambda: bash_script("upload-catalog-images.sh", "--upload"))
    stage(record, "web", lambda: task(record, "deploy"))
    stage(record, "csi-render", lambda: python_script("prepare-ebs-csi-dev.py"))
    stage(record, "csi", lambda: task(record, "csi"))
    stage(record, "monitoring-render", lambda: python_script("prepare-monitoring-dev.py", "--reuse-credentials"))
    stage(record, "monitoring-secret", lambda: python_script("prepare-monitoring-dev.py", "--store"))
    stage(record, "monitoring", lambda: task(record, "monitoring"))
    stage(record, "scaling-render", lambda: python_script("prepare-autoscaling-dev.py", "render"))
    stage(record, "scaling", lambda: task(record, "autoscaling"))
    stage(record, "etl-config", lambda: python_script("prepare-etl-dev.py"))
    stage(record, "etl-upload", lambda: bash_script("etl-dev.sh", "upload"))
    stage(record, "etl-manual", lambda: bash_script("etl-dev.sh", "setup", "--replace-start-trigger"))
    # A fresh generation must not resume an old deleted workflow's local Run ID.
    receipt = DEST / ("etl-stack-" + record["generation"] + ".json")
    stage(record, "etl-first-batch", lambda: bash_script("etl-dev.sh", "finish", "--receipt", str(receipt)))
    stage(record, "etl-schedule", lambda: bash_script("etl-dev.sh", "enable-schedule", "--replace-start-trigger"))
    stage(record, "web-smoke", lambda: bash_script("demo-k6-dev.sh", "smoke"))
    record["mode"] = "ready"
    save(record)
    print("Dev stack recreated. Web: http://" + output("alb_dns_name"))
    print("Images: " + output("cloudfront_images_url"))
    print("Grafana is private; reopen its SSM/port-forward sessions separately.")


def sql_digest():
    digest = hashlib.sha256()
    for name in ("marketplace_schema.sql", "example_data.sql"):
        digest.update((ROOT / "sql" / name).read_bytes())
    return digest.hexdigest()


def empty_bucket(bucket):
    if bucket not in BUCKETS:
        raise Failure("Refusing unrelated S3 bucket")
    aws("s3api", "head-bucket", "--bucket", bucket, "--expected-bucket-owner", ACCOUNT)
    # Read one page then delete it; do not mutate a collection while paginating
    # with a cursor whose previous versions have just been deleted.
    while True:
        page = aws("s3api", "list-object-versions", "--bucket", bucket, "--max-keys", "1000", "--no-paginate",
                   "--expected-bucket-owner", ACCOUNT)
        objects = [{"Key": row["Key"], "VersionId": row["VersionId"]}
                   for key in ("Versions", "DeleteMarkers") for row in page.get(key, [])]
        if not objects:
            break
        result = delete_objects(bucket, objects)
        if result.get("Errors"):
            raise Failure("S3 version deletion failed; refusing to claim bucket is empty")
    # Also handle any unversioned objects and incomplete multipart uploads.
    while True:
        page = aws("s3api", "list-objects-v2", "--bucket", bucket, "--max-keys", "1000", "--no-paginate",
                   "--expected-bucket-owner", ACCOUNT)
        objects = [{"Key": row["Key"]} for row in page.get("Contents", [])]
        if not objects:
            break
        if delete_objects(bucket, objects).get("Errors"):
            raise Failure("S3 object deletion failed")
    while True:
        uploads = aws("s3api", "list-multipart-uploads", "--bucket", bucket, "--max-uploads", "1000",
                      "--no-paginate", "--expected-bucket-owner", ACCOUNT).get("Uploads", [])
        if not uploads:
            break
        for upload in uploads:
            aws("s3api", "abort-multipart-upload", "--bucket", bucket, "--key", upload["Key"],
                "--upload-id", upload["UploadId"], "--expected-bucket-owner", ACCOUNT)


def delete_objects(bucket, objects):
    # 1,000 long keys plus version IDs can exceed the OS argv size limit.
    with tempfile.TemporaryDirectory(prefix="coco-s3-delete-") as directory:
        path = Path(directory) / "objects.json"
        private_json(path, {"Objects": objects, "Quiet": True})
        return aws("s3api", "delete-objects", "--bucket", bucket, "--expected-bucket-owner", ACCOUNT,
                   "--delete", "file://" + str(path))


def empty_repo(repo):
    if repo not in REPOS:
        raise Failure("Refusing unrelated ECR repository")
    for _ in range(20):
        rows = aws("ecr", "list-images", "--repository-name", repo).get("imageIds", [])
        digests = list({row["imageDigest"] for row in rows})
        if not digests:
            return
        progress = False
        for index in range(0, len(digests), 100):
            result = aws("ecr", "batch-delete-image", "--repository-name", repo,
                         "--image-ids", json.dumps([{"imageDigest": d} for d in digests[index:index + 100]]))
            # Image indexes must be removed before their referenced manifests.
            for failure in result.get("failures", []):
                if failure.get("failureCode") not in {"ImageReferencedByManifestList", "ImageNotFound"}:
                    raise Failure("ECR image deletion failed")
            progress = progress or bool(result.get("imageIds"))
        if not progress:
            raise Failure("ECR deletion made no progress; inspect manifest references")
    raise Failure("ECR repository did not become empty")


def delete_glue():
    triggers = [t for t in aws("glue", "get-triggers").get("Triggers", []) if t.get("WorkflowName") == WORKFLOW]
    allowed = {"coco-dev-manual-extract", "coco-dev-scheduled-extract", "coco-dev-conditional-transform"}
    if any(t["Name"] not in allowed for t in triggers):
        raise Failure("Unexpected trigger attached to dev workflow")
    for trigger in triggers:
        if trigger.get("State") in {"ACTIVATED", "ACTIVATING"}:
            aws("glue", "stop-trigger", "--name", trigger["Name"])
        wait_until("Glue trigger inactive", lambda name=trigger["Name"]:
                   aws("glue", "get-trigger", "--name", name)["Trigger"]["State"] in {"CREATED", "DEACTIVATED"}, 300)
    workflows = aws("glue", "list-workflows").get("Workflows", [])
    if WORKFLOW in workflows:
        active = aws("glue", "get-workflow-runs", "--name", WORKFLOW).get("Runs", [])
        if any(r.get("Status") in {"RUNNING", "STOPPING"} for r in active):
            raise Failure("ETL workflow is active; let it finish before destroy")
    jobs = set(aws("glue", "list-jobs").get("JobNames", []))
    for job in ("ecommerce-dev-extract", "ecommerce-dev-transform"):
        if job in jobs and any(r.get("JobRunState") in {"STARTING", "RUNNING", "STOPPING", "WAITING"}
                              for r in aws("glue", "get-job-runs", "--job-name", job).get("JobRuns", [])):
            raise Failure("A dev Glue job is active; let it finish before destroy")
    for trigger in triggers:
        aws("glue", "delete-trigger", "--name", trigger["Name"])
    if WORKFLOW in workflows:
        aws("glue", "delete-workflow", "--name", WORKFLOW)


def owned_volume(volume):
    tags = {t["Key"]: t["Value"] for t in volume.get("Tags", [])}
    # Require an exact cluster tag, CSI origin and a dev project's namespace.
    return (tags.get("kubernetes.io/cluster/" + CLUSTER) == "owned" and
            tags.get("ebs.csi.aws.com/cluster") == "true" and
            tags.get("kubernetes.io/created-for/pvc/namespace") in {"monitoring", "coco"} and
            volume.get("AvailabilityZone") in {REGION + "a", REGION + "b"})


def destroy(record):
    # Keep only local config/secrets and source inputs needed for a future up.
    # This is not a database/object backup. Fail BEFORE deleting anything if missing.
    preflight_rebuild(check_docker=False)
    state = resources(json.loads(tf("show", "-json", capture=True)))
    if not state and record.get("mode") != "destroying":
        record = new_record("destroyed")
        save(record)
        print("No managed dev resources remain in this Terraform state.")
        return
    if record.get("mode") != "destroying":
        record = new_record("destroying")
        record["buckets"] = [r["values"]["id"] for r in state if r["type"] == "aws_s3_bucket"]
        record["repos"] = [r["values"]["name"] for r in state if r["type"] == "aws_ecr_repository"]
        record["workgroups"] = [r["values"]["name"] for r in state if r["type"] == "aws_athena_workgroup"]
        record["vpc"] = next((r["values"]["id"] for r in state if r["type"] == "aws_vpc"), None)
        volumes = aws("ec2", "describe-volumes", "--filters",
                      "Name=tag:kubernetes.io/cluster/" + CLUSTER + ",Values=owned").get("Volumes", [])
        if any(not owned_volume(v) for v in volumes):
            raise Failure("Found cluster-tagged volumes outside expected CSI namespaces; inspect before destroy")
        record["volumes"] = [v["VolumeId"] for v in volumes]
        save(record)
    if (not set(record["buckets"]) <= BUCKETS or not set(record["repos"]) <= REPOS
            or not set(record["workgroups"]) <= {"ecommerce-dev-analytics"}):
        raise Failure("Terraform state contains buckets/repositories outside this dev stack")
    # Validate a destroy-only plan before touching data outside Terraform.
    tf("plan", "-destroy", "-input=false", "-var=aws_region=" + REGION, "-out=stack-destroy-review.tfplan")
    validate_plan(json.loads(tf("show", "-json", "stack-destroy-review.tfplan", capture=True)), True)
    stage(record, "disable-etl", delete_glue)
    # Stop web writers and CA first, then stop ASG scale activity without
    # terminating nodes until Terraform destroys them in dependency order.
    def freeze_compute():
        if not record["vpc"]:
            return
        groups = aws("autoscaling", "describe-auto-scaling-groups", "--auto-scaling-group-names",
                     "ecommerce-dev-worker-asg").get("AutoScalingGroups", [])
        if groups:
            aws("autoscaling", "suspend-processes", "--auto-scaling-group-name", "ecommerce-dev-worker-asg")
        instances = aws("ec2", "describe-instances", "--filters",
                        "Name=vpc-id,Values=" + str(record["vpc"]), "Name=instance-state-name,Values=running,pending")
        nodes = [n for r in instances.get("Reservations", []) for n in r["Instances"]]
        if any({t["Key"]: t["Value"] for t in n.get("Tags", [])}.get("Name") not in
               {"ecommerce-dev-worker", "ecommerce-dev-control-plane"} for n in nodes):
            raise Failure("Unexpected EC2 in dev VPC; refusing to stop it")
        ids = [n["InstanceId"] for n in nodes]
        if any(n["State"]["Name"] == "pending" for n in nodes):
            raise Failure("EC2 still pending; wait and retry destroy")
        if ids:
            aws("ec2", "stop-instances", "--instance-ids", *ids)
            run(["aws", "ec2", "wait", "instance-stopped", "--region", REGION, "--instance-ids", *ids], capture=True)
        # Resume only termination: Terraform must be able to reduce/delete the ASG.
        if groups:
            aws("autoscaling", "resume-processes", "--auto-scaling-group-name", "ecommerce-dev-worker-asg",
                "--scaling-processes", "Terminate")
    stage(record, "freeze-compute", freeze_compute)
    def capture_volumes():
        rows = aws("ec2", "describe-volumes", "--filters",
                   "Name=tag:kubernetes.io/cluster/" + CLUSTER + ",Values=owned").get("Volumes", [])
        if any(not owned_volume(v) for v in rows):
            raise Failure("Unexpected CSI volume ownership after stopping compute")
        record["volumes"] = sorted(set(record["volumes"]) | {v["VolumeId"] for v in rows})
        save(record)
    stage(record, "volume-inventory", capture_volumes)
    for bucket in record["buckets"]:
        stage(record, "empty-" + bucket, lambda bucket=bucket: empty_bucket(bucket))
    for repo in record["repos"]:
        stage(record, "empty-" + repo, lambda repo=repo: empty_repo(repo))
    def workgroups():
        present = {w["Name"] for w in aws("athena", "list-work-groups").get("WorkGroups", [])}
        for name in set(record["workgroups"]) & present:
            # Terraform's ordinary workgroup destruction stays protected. This
            # explicit destroy command also removes its saved named queries.
            aws("athena", "delete-work-group", "--work-group", name, "--recursive-delete-option")
    stage(record, "athena-workgroup", workgroups)
    def parameters():
        present = {p["Name"] for p in aws("ssm", "describe-parameters").get("Parameters", [])}
        for name in sorted(PARAMETERS & present):
            aws("ssm", "delete-parameter", "--name", name)
    stage(record, "parameters", parameters)
    stage(record, "terraform-destroy", lambda: apply_plan(destroy=True))
    def delete_volumes():
        for identifier in record["volumes"]:
            rows = aws("ec2", "describe-volumes", "--filters", "Name=volume-id,Values=" + identifier).get("Volumes", [])
            if not rows:
                continue
            if not owned_volume(rows[0]):
                raise Failure("Volume ownership changed; refusing deletion")
            wait_until("monitoring volume detached " + identifier, lambda identifier=identifier:
                all(v["State"] == "available" and not v.get("Attachments") for v in aws(
                    "ec2", "describe-volumes", "--filters", "Name=volume-id,Values=" + identifier).get("Volumes", [])), 600)
            aws("ec2", "delete-volume", "--volume-id", identifier)
    stage(record, "csi-volumes", delete_volumes)
    if resources(json.loads(tf("show", "-json", capture=True))):
        raise Failure("Terraform managed resources remain")
    record["mode"] = "destroyed"
    save(record)
    print("Dev resources in Terraform state and recorded CSI volumes deleted. No backup was made.")
    print("Local source, tfvars, SMTP/Grafana config remain for the next up. KMS deletion is scheduled by AWS.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "up", "destroy"))
    parser.add_argument("--delete-data", action="store_true", help="Destroy dev DB, all S3 versions, ECR images and CSI data without backup")
    parser.add_argument("--retry-failed", action="store_true",
                        help="On up only: retry recorded terminal failed SSM tasks after fixing their cause")
    args = parser.parse_args()
    if args.action == "destroy" and not args.delete_data:
        parser.error("destroy requires --delete-data; this irreversibly deletes dev data without backup")
    if args.action != "destroy" and args.delete_data:
        parser.error("--delete-data applies only to destroy")
    if args.retry_failed and args.action != "up":
        parser.error("--retry-failed applies only to up")
    os.umask(0o077)
    try:
        for tool in ("aws", "terraform"):
            if not shutil.which(tool):
                raise Failure("Missing tool: " + tool)
        if aws("sts", "get-caller-identity")["Account"] != ACCOUNT:
            raise Failure("Wrong AWS account")
        DEST.mkdir(parents=True, exist_ok=True)
        with (DEST / ".stack.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if args.action == "check":
                preflight_rebuild()
                print("Preflight passed. No AWS writes, Terraform apply or SQL executed.")
                return 0
            tf("init", "-input=false")
            if tf("workspace", "show", capture=True).strip() != "default":
                raise Failure("Expected default workspace in terraform/environments/dev")
            record = load_record()
            if args.retry_failed:
                for key, command_id in list(record.get("commands", {}).items()):
                    rows = aws("ssm", "list-commands", "--command-id", command_id).get("Commands", [])
                    if rows and rows[0]["Status"] in {"Failed", "TimedOut", "Cancelled"}:
                        del record["commands"][key]
                save(record)
            if args.action == "destroy":
                print("DESTROY DEV: DB, all S3 versions, ECR images and CSI data will be deleted without backup.", flush=True)
                destroy(record)
            else:
                up(record)
        return 0
    except Failure as exc:
        print(str(exc), file=sys.stderr)
        print("Stack command stopped; no automatic rollback. Progress: artifacts/deploy/dev/stack-lifecycle.json", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        # Avoid leaking settings/credentials through exceptions or command args.
        print("Stack command stopped. See the last stage/SSM ID above; no automatic destroy or rollback was attempted.", file=sys.stderr)
        print("Private progress: artifacts/deploy/dev/stack-lifecycle.json. Keep local configs and SQL sources.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
