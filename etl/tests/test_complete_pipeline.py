"""Acceptance orchestration regression checks. All AWS interactions are mocked."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

with patch("dotenv.load_dotenv", return_value=False):
    from orchestration import complete_pipeline as pipeline
    from extract import setup_workflow


class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.directory = self.enterContext(tempfile.TemporaryDirectory())
        self.path = Path(self.directory) / "run.json"
        self.settings = SimpleNamespace(environment="dev", account_id="858525799322",
                                        region="ap-southeast-1", workflow="dev-flow",
                                        extract_job="extract", transform_job="transform")
        self.aws = SimpleNamespace(settings=self.settings, glue=Mock())

    def test_receipt_survives_restart_and_never_starts_duplicate_job(self):
        pipeline.save_run(self.path, self.settings, "wr_saved")
        self.assertEqual(pipeline.select_run(self.aws, self.path), "wr_saved")
        self.aws.glue.start_workflow_run.assert_not_called()
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_receipt_cannot_be_reused_for_another_environment(self):
        pipeline.save_run(self.path, self.settings, "wr_saved")
        record = json.loads(self.path.read_text())
        record["account"] = "123456789012"
        self.path.write_text(json.dumps(record))
        with self.assertRaises(ValueError):
            pipeline.select_run(self.aws, self.path)
        self.aws.glue.start_workflow_run.assert_not_called()

    def test_new_batch_is_blocked_while_another_run_is_active(self):
        self.aws.glue.get_trigger.return_value = {"Trigger": {
            "Type": "ON_DEMAND", "WorkflowName": "dev-flow", "Actions": [{"JobName": "extract"}],
        }}
        self.aws.glue.get_paginator.return_value.paginate.return_value = [
            {"Runs": [{"WorkflowRunId": "wr_running", "Status": "RUNNING"}]},
        ]
        with self.assertRaisesRegex(RuntimeError, "--run-id wr_running"):
            pipeline.select_run(self.aws, self.path, new_run=True)
        self.aws.glue.start_workflow_run.assert_not_called()

    def test_explicit_scheduled_batch_resume_does_not_require_manual_trigger(self):
        self.assertEqual(pipeline.select_run(self.aws, self.path, run_id="wr_scheduled"), "wr_scheduled")
        self.aws.glue.get_workflow_run.assert_called_once_with(
            Name="dev-flow", RunId="wr_scheduled", IncludeGraph=False,
        )
        self.aws.glue.get_trigger.assert_not_called()
        self.aws.glue.start_workflow_run.assert_not_called()

    def test_failed_transform_cannot_publish_or_start_report_queries(self):
        pipeline.save_run(self.path, self.settings, "wr_failed")
        with patch.object(pipeline, "wait_for_workflow", side_effect=RuntimeError("transform failed")), \
                patch.object(pipeline, "publish_batch") as publish, \
                patch.object(pipeline, "execute_query") as query:
            with self.assertRaisesRegex(RuntimeError, "transform failed"):
                pipeline.complete(self.aws, self.path)
        publish.assert_not_called()
        query.assert_not_called()

    def test_success_publishes_same_batch_then_checks_all_three_reports(self):
        pipeline.save_run(self.path, self.settings, "wr_success")
        with patch.object(pipeline, "wait_for_workflow") as wait, \
                patch.object(pipeline, "publish_batch") as publish, \
                patch.object(pipeline, "execute_query", side_effect=["q1", "q2", "q3"]) as query, \
                patch.object(pipeline, "wait_for_query", return_value={}) as wait_query, \
                patch.object(pipeline, "print_results") as results:
            pipeline.complete(self.aws, self.path)
        self.assertEqual(wait.call_args.args[2], "wr_success")
        publish.assert_called_once_with(self.aws, "wr_success")
        self.assertEqual(query.call_count, 3)
        self.assertEqual(wait_query.call_count, 3)
        self.assertEqual(results.call_count, 3)

    def test_old_dev_schedule_is_blocked_before_mutating_aws(self):
        self.settings.schedule = "cron(0 1 * * ? *)"
        with patch.object(setup_workflow, "AWSClients", return_value=self.aws), \
                patch("sys.argv", ["setup_workflow", "--enable-schedule"]), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(setup_workflow.main(), 1)
        self.assertEqual(self.aws.glue.mock_calls, [])


if __name__ == "__main__":
    unittest.main()
