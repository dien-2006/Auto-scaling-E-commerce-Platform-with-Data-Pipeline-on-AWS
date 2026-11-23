"""Owner-run acceptance of one batch; resume without silently starting another."""

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from botocore.exceptions import BotoCoreError, ClientError

from athena.create_tables import publish_batch
from athena.run_queries import QUERIES, execute_query, print_results, wait_for_query
from common.aws_clients import AWSClients
from extract.run_workflow import wait_for_workflow


RECEIPT = Path(__file__).resolve().parents[2] / "artifacts/deploy/dev/etl-last-run.json"


def valid_run_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value):
        raise ValueError("Invalid workflow run ID")
    return value


def saved_run(path, settings):
    if not path.exists():
        return None
    record = json.loads(path.read_text())
    if not isinstance(record, dict):
        raise ValueError("Saved run receipt must be a JSON object")
    if any(record.get(key) != value for key, value in (
        ("account", settings.account_id), ("region", settings.region),
        ("workflow", settings.workflow),
    )):
        raise ValueError("Saved run belongs to another account, region or workflow")
    return valid_run_id(record.get("run_id"))


def save_run(path, settings, run_id):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".etl-run-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump({"account": settings.account_id, "region": settings.region,
                       "workflow": settings.workflow, "run_id": valid_run_id(run_id)}, stream)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def select_run(aws, path, run_id=None, new_run=False):
    settings = aws.settings
    if run_id:
        selected = valid_run_id(run_id)
        # Verify membership before replacing the local receipt.
        aws.glue.get_workflow_run(Name=settings.workflow, RunId=selected, IncludeGraph=False)
    else:
        previous = saved_run(path, settings)
        if previous and not new_run:
            print("Resuming saved batch; use --new-run only to start another paid batch.")
            return previous
        trigger = aws.glue.get_trigger(
            Name=f"coco-{settings.environment}-manual-extract",
        )["Trigger"]
        if (trigger.get("Type") != "ON_DEMAND" or
                trigger.get("WorkflowName") != settings.workflow or
                trigger.get("Actions") != [{"JobName": settings.extract_job}]):
            raise ValueError("Expected the owned ON_DEMAND starting trigger; do not start a scheduled workflow manually")
        for page in aws.glue.get_paginator("get_workflow_runs").paginate(Name=settings.workflow):
            active = [run["WorkflowRunId"] for run in page.get("Runs", [])
                      if run.get("Status") in {"RUNNING", "STOPPING"}]
            if active:
                raise RuntimeError("Workflow already active. Resume with --run-id " + active[0])
        selected = valid_run_id(aws.glue.start_workflow_run(Name=settings.workflow)["RunId"])
        print(f"Started Run ID: {selected}", flush=True)
    save_run(path, settings, selected)
    return selected


def complete(aws, path, run_id=None, new_run=False, timeout_seconds=7200):
    settings = aws.settings
    if settings.environment != "dev":
        raise ValueError("This acceptance command is for dev only")
    selected = select_run(aws, path, run_id, new_run)
    print(f"Run ID: {selected}", flush=True)
    print(f"Resume: bash scripts/aws/etl-dev.sh finish --run-id {selected}", flush=True)
    wait_for_workflow(aws.glue, settings.workflow, selected,
                      (settings.extract_job, settings.transform_job),
                      timeout_seconds=timeout_seconds)
    publish_batch(aws, selected)
    for report, sql in QUERIES.items():
        execution = execute_query(aws, sql)
        print(f"Report: {report}; Query ID: {execution}", flush=True)
        result = wait_for_query(aws, execution)
        print(f"Bytes scanned: {result.get('Statistics', {}).get('DataScannedInBytes', 0)}")
        print_results(aws, execution)
    print(f"ETL acceptance completed: {selected}. Extract, transform, Catalog and all three Athena reports succeeded.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--run-id", help="Resume a known manual or scheduled batch without starting a job")
    group.add_argument("--new-run", action="store_true", help="Explicitly start another paid batch")
    parser.add_argument("--timeout-seconds", type=int, default=7200)
    parser.add_argument("--receipt", type=Path, default=RECEIPT,
                        help="Local progress file; use a separate file for a freshly recreated stack")
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    try:
        complete(AWSClients(), args.receipt, args.run_id, args.new_run, args.timeout_seconds)
        return 0
    except (BotoCoreError, ClientError, ValueError, RuntimeError, TimeoutError, OSError) as exc:
        print(f"ETL acceptance stopped: {exc}", file=sys.stderr)
        print("No AWS run was cancelled. Resume the printed Run ID; do not use --new-run to retry a timeout.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
