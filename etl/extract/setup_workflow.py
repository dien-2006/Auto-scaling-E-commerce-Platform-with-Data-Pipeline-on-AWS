
import argparse
import sys
import time

from botocore.exceptions import BotoCoreError, ClientError
from common.aws_clients import AWSClients


def ensure_workflow(glue, name):
    try:
        workflow = glue.get_workflow(Name=name)["Workflow"]
        if workflow.get("MaxConcurrentRuns") != 1:
            glue.update_workflow(Name=name, MaxConcurrentRuns=1)
        print(f"Workflow exists: {name}")

    except glue.exceptions.EntityNotFoundException:
        glue.create_workflow(
            Name=name,
            Description="COCO PostgreSQL Data Lake Pipeline",
            MaxConcurrentRuns=1,
        )
        print(f"Created workflow: {name}")


STABLE_TRIGGER_STATES = {"CREATED", "ACTIVATED", "DEACTIVATED"}
TRANSITIONAL_TRIGGER_STATES = {"CREATING", "UPDATING", "ACTIVATING", "DEACTIVATING"}


def wait_for_trigger(glue, name, ready_states=None, timeout_seconds=180, poll_seconds=2):
    """Wait for eventual creation/update/activation; never silently skip a transition."""
    if timeout_seconds <= 0 or poll_seconds <= 0:
        raise ValueError("Trigger timeout and poll interval must be positive")
    if ready_states is None:
        ready_states = STABLE_TRIGGER_STATES
    deadline = time.monotonic() + timeout_seconds
    last_state = "NOT_FOUND"

    while True:
        try:
            trigger = glue.get_trigger(Name=name)["Trigger"]
        except glue.exceptions.EntityNotFoundException:
            # Newly created triggers may not yet be visible to subsequent reads.
            last_state = "NOT_FOUND"
        else:
            last_state = trigger["State"]
            if last_state in ready_states:
                return trigger
            if last_state not in STABLE_TRIGGER_STATES | TRANSITIONAL_TRIGGER_STATES:
                raise RuntimeError(f"Trigger {name} has unexpected state {last_state}")

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"Trigger {name} did not reach {sorted(ready_states)}; state={last_state}")
        time.sleep(min(poll_seconds, remaining))


def ensure_trigger(glue, name, trigger_type, config, workflow):
    """
    Create or update a trigger.

    Existing triggers must belong to the expected
    workflow and have the expected type.
    """

    try:
        response = glue.get_trigger(Name=name)
        existing = response["Trigger"]

    except glue.exceptions.EntityNotFoundException:
        glue.create_trigger(
            Name=name,
            WorkflowName=workflow,
            Type=trigger_type,
            StartOnCreation=False,
            **config,
        )
        wait_for_trigger(glue, name)
        print(f"Created trigger: {name}")
        return

    existing = wait_for_trigger(glue, name)

    if existing.get("WorkflowName") != workflow:
        raise RuntimeError(
            f"Trigger {name} belongs to another workflow"
        )

    if existing["Type"] != trigger_type:
        raise RuntimeError(
            f"Unexpected trigger type for {name}"
        )

    # Only update a trigger when its definition differs.
    changed = any(
        existing.get(key) != value
        for key, value in config.items()
    )

    if changed:
        glue.update_trigger(
            Name=name,
            TriggerUpdate=config,
        )
        wait_for_trigger(glue, name)
        print(f"Updated trigger: {name}")
    else:
        print(f"Trigger unchanged: {name}")


def ensure_active(glue, name):
    trigger = wait_for_trigger(glue, name)
    if trigger["State"] == "ACTIVATED":
        return
    glue.start_trigger(Name=name)
    wait_for_trigger(glue, name, {"ACTIVATED"})
    print(f"Activated: {name}")


def ensure_disabled(glue, name):
    trigger = wait_for_trigger(glue, name)
    if trigger["State"] in {"CREATED", "DEACTIVATED"}:
        return
    glue.stop_trigger(Name=name)
    wait_for_trigger(glue, name, {"DEACTIVATED"})
    print(f"Deactivated: {name}")


def wait_for_trigger_deleted(glue, name, timeout_seconds=180):
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            glue.get_trigger(Name=name)
        except glue.exceptions.EntityNotFoundException:
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"Trigger {name} is still visible after deletion")
        time.sleep(min(2, remaining))


def ensure_start_trigger(glue, workflow, prefix, extract_job, schedule,
                         scheduled=False, replace=False):
    """A workflow gets ONE starting trigger. Replacement is explicit and guarded."""
    name = f"{prefix}-{'scheduled' if scheduled else 'manual'}-extract"
    other_name = f"{prefix}-{'manual' if scheduled else 'scheduled'}-extract"
    try:
        old = glue.get_trigger(Name=other_name)["Trigger"]
    except glue.exceptions.EntityNotFoundException:
        old = None
    if old is not None:
        expected_type = "ON_DEMAND" if scheduled else "SCHEDULED"
        if (old.get("WorkflowName") != workflow or old.get("Type") != expected_type or
                old.get("Actions") != [{"JobName": extract_job}]):
            raise RuntimeError(f"Refusing to replace unrelated trigger {other_name}")
        if not replace:
            raise RuntimeError(
                f"Workflow already has start trigger {other_name}. "
                "Use --replace-start-trigger to replace only this owned trigger; no job/data is deleted."
            )
        for page in glue.get_paginator("get_workflow_runs").paginate(Name=workflow):
            if any(run.get("Status") in {"RUNNING", "STOPPING"} for run in page.get("Runs", [])):
                raise RuntimeError("Workflow is active; refusing to replace its start trigger")
        ensure_disabled(glue, other_name)
        # Recheck after disabling the schedule so a run starting during that
        # transition cannot lose its originating trigger.
        for page in glue.get_paginator("get_workflow_runs").paginate(Name=workflow):
            if any(run.get("Status") in {"RUNNING", "STOPPING"} for run in page.get("Runs", [])):
                raise RuntimeError("Workflow started during schedule deactivation; wait for completion")
        glue.delete_trigger(Name=other_name)
        wait_for_trigger_deleted(glue, other_name)
        print(f"Removed owned start trigger: {other_name}")
    config = {"Actions": [{"JobName": extract_job}]}
    if scheduled:
        config["Schedule"] = schedule
    ensure_trigger(glue, name, "SCHEDULED" if scheduled else "ON_DEMAND", config, workflow)
    return name


def configure():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace-start-trigger", action="store_true",
                        help="Explicitly replace the owned inactive start trigger when changing mode; never deletes jobs/data")

    parser.add_argument(
        "--enable-schedule",
        action="store_true",
        help="Enable automatic daily ETL",
    )

    parser.add_argument(
        "--disable-schedule",
        action="store_true",
        help="Disable automatic ETL",
    )

    args = parser.parse_args()

    if args.enable_schedule and args.disable_schedule:
        parser.error(
            "Choose only one schedule action"
        )

    aws = AWSClients()
    glue = aws.glue
    settings = aws.settings

    if (args.enable_schedule and settings.environment == "dev" and
            settings.schedule != "cron(0 18 * * ? *)"):
        raise ValueError("Dev schedule must be 01:00 Vietnam: cron(0 18 * * ? *). Refresh the reviewed Terraform output/config first")

    # Verify Terraform-created Glue jobs.
    for job_name in (
        settings.extract_job,
        settings.transform_job,
    ):
        glue.get_job(JobName=job_name)

    ensure_workflow(glue, settings.workflow)

    prefix = f"coco-{settings.environment}"

    conditional_name = f"{prefix}-conditional-transform"

    # Scheduled and on-demand triggers cannot both start the same workflow.
    start_name = ensure_start_trigger(
        glue, settings.workflow, prefix, settings.extract_job, settings.schedule,
        scheduled=args.enable_schedule, replace=args.replace_start_trigger,
    )

    # 3. Conditional transform
    ensure_trigger(
        glue,
        conditional_name,
        "CONDITIONAL",
        {
            "Predicate": {
                "Logical": "AND",
                "Conditions": [
                    {
                        "LogicalOperator": "EQUALS",
                        "JobName": settings.extract_job,
                        "State": "SUCCEEDED",
                    }
                ]
            },
            "Actions": [
                {"JobName": settings.transform_job}
            ],
        },
        settings.workflow,
    )

    ensure_active(glue, conditional_name)

    if args.enable_schedule:
        ensure_active(glue, start_name)

    print("COCO workflow configuration completed.")


def main():
    try:
        configure()
        return 0
    except (BotoCoreError, ClientError, RuntimeError, ValueError, TimeoutError) as exc:
        print(f"Workflow setup failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
