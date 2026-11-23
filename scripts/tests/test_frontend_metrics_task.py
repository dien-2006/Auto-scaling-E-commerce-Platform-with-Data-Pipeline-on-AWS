"""Offline checks for the scope of frontend-only image deployment."""
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "aws/run-dev-task.py"
SPEC = importlib.util.spec_from_file_location("frontend_metrics_task", SOURCE)
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


class FrontendImageTests(unittest.TestCase):
    def test_frontend_tag_is_checked_in_ecr_and_only_frontend_is_updated(self):
        calls = []
        def aws(*args):
            calls.append(args)
            if args[:2] == ("sts", "get-caller-identity"):
                return {"Account": "858525799322"}
            if args[:2] == ("ecr", "describe-images"):
                self.assertIn("ecommerce/dev/frontend", args)
                self.assertIn("imageTag=dev-metrics-test", args)
                return {"imageDetails": [{}]}
            raise AssertionError(args)
        with patch.object(task, "aws", side_effect=aws), \
                patch.object(task, "instances", return_value=["i-control"]), \
                patch.object(task, "submit") as submit, \
                patch("sys.argv", ["run-dev-task", "frontend-image", "--tag", "dev-metrics-test"]), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(task.main(), 0)
        script = submit.call_args.args[1]
        self.assertIn("set image deployment/coco-frontend frontend=", script)
        self.assertNotIn("set image deployment/coco-backend", script)
        self.assertNotIn("get-parameter", script)
        self.assertNotIn("create secret", script)
        self.assertNotIn("autoscaling", script)
        self.assertEqual(len(calls), 2)

    def test_invalid_tag_is_rejected_before_ecr_or_ssm_calls(self):
        with patch.object(task, "aws", return_value={"Account": "858525799322"}) as aws, \
                patch.object(task, "submit") as submit, \
                patch("sys.argv", ["run-dev-task", "frontend-image", "--tag", "x;echo invalid"]), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(task.main(), 1)
        self.assertEqual(aws.call_count, 1)
        submit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
