
import argparse
import time

from common.aws_clients import AWSClients


def ensure_workflow(glue, name):
    try:
        glue.get_workflow(Name=name)
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


def main():
    parser = argparse.ArgumentParser()

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

    # Verify Terraform-created Glue jobs.
    for job_name in (
        settings.extract_job,
        settings.transform_job,
    ):
        glue.get_job(JobName=job_name)

    ensure_workflow(glue, settings.workflow)

    prefix = f"coco-{settings.environment}"

    scheduled_name = f"{prefix}-scheduled-extract"
    manual_name = f"{prefix}-manual-extract"
    conditional_name = f"{prefix}-conditional-transform"

    # 1. Daily schedule
    ensure_trigger(
        glue,
        scheduled_name,
        "SCHEDULED",
        {
            "Schedule": settings.schedule,
            "Actions": [
                {"JobName": settings.extract_job}
            ],
        },
        settings.workflow,
    )

    # 2. Manual start
    ensure_trigger(
        glue,
        manual_name,
        "ON_DEMAND",
        {
            "Actions": [
                {"JobName": settings.extract_job}
            ],
        },
        settings.workflow,
    )

    # 3. Conditional transform
    ensure_trigger(
        glue,
        conditional_name,
        "CONDITIONAL",
        {
            "Predicate": {
                "Conditions": [
                    {
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
        ensure_active(glue, scheduled_name)

    elif args.disable_schedule:
        ensure_disabled(glue, scheduled_name)

    print("COCO workflow configuration completed.")


if __name__ == "__main__":
    main()
