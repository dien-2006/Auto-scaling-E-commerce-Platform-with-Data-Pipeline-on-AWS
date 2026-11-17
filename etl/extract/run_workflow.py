import argparse
import time

from common.aws_clients import AWSClients


TERMINAL_STATES = {"COMPLETED", "STOPPED", "ERROR"}
FAILED_ACTION_COUNTS = (
    "FailedActions", "TimeoutActions", "ErroredActions", "StoppedActions",
)


def validate_success(run, expected_jobs):
    """A completed workflow must contain successful runs of both pipeline jobs."""
    if run["Status"] != "COMPLETED":
        reason = run.get("ErrorMessage", "")
        raise RuntimeError(
            f"Workflow finished with status {run['Status']}: {reason}"
        )

    statistics = run.get("Statistics")
    if not statistics:
        raise RuntimeError("Workflow completed without action statistics")

    failures = {
        key: statistics.get(key, 0)
        for key in FAILED_ACTION_COUNTS
        if statistics.get(key, 0) > 0
    }
    if failures:
        raise RuntimeError(f"Workflow contains unsuccessful actions: {failures}")

    expected_jobs = set(expected_jobs)
    succeeded = statistics.get("SucceededActions", 0)
    if succeeded < len(expected_jobs) or succeeded != statistics.get("TotalActions"):
        raise RuntimeError("Workflow did not successfully finish all expected actions")

    successful_jobs = {
        node["Name"]
        for node in run.get("Graph", {}).get("Nodes", [])
        if node.get("Type") == "JOB"
        and any(
            job_run.get("JobRunState") == "SUCCEEDED"
            for job_run in node.get("JobDetails", {}).get("JobRuns", [])
        )
    }
    missing = expected_jobs - successful_jobs
    if missing:
        raise RuntimeError(
            f"Workflow is missing successful job runs: {', '.join(sorted(missing))}"
        )


def wait_for_workflow(glue, workflow, run_id, expected_jobs,
                      timeout_seconds=7200, poll_seconds=20):
    if timeout_seconds <= 0 or poll_seconds <= 0:
        raise ValueError("Workflow timeout and poll interval must be positive")
    deadline = time.monotonic() + timeout_seconds

    while True:
        run = glue.get_workflow_run(
            Name=workflow,
            RunId=run_id,
            IncludeGraph=True,
        )["Run"]
        status = run["Status"]
        print(f"Workflow status: {status}")
        if status in TERMINAL_STATES:
            validate_success(run, expected_jobs)
            print("Extract and transform both succeeded.")
            return run

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(
                f"Timed out watching workflow {workflow}, run {run_id}; "
                "the AWS run has not been stopped"
            )
        time.sleep(min(poll_seconds, remaining))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--watch", action="store_true", help="Monitor extract and transform to completion",
    )
    parser.add_argument(
        "--timeout-seconds", type=int, default=7200,
        help="Maximum watch duration; timing out does not stop the AWS run",
    )
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")

    aws = AWSClients()
    settings = aws.settings
    response = aws.glue.start_workflow_run(Name=settings.workflow)
    run_id = response["RunId"]
    print(f"Workflow: {settings.workflow}")
    print(f"Run ID: {run_id}")

    if args.watch:
        wait_for_workflow(
            aws.glue, settings.workflow, run_id,
            (settings.extract_job, settings.transform_job),
            timeout_seconds=args.timeout_seconds,
        )


if __name__ == "__main__":
    main()
