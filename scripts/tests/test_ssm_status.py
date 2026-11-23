import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch

source = Path(__file__).resolve().parents[1] / "aws/run-dev-task.py"
spec = importlib.util.spec_from_file_location("run_dev_task", source)
task = importlib.util.module_from_spec(spec)
spec.loader.exec_module(task)


class TaskStatusTests(unittest.TestCase):
    def outcome(self, statuses, parent_status, count=2):
        def aws(*args):
            if args[0] == "sts":
                return {"Account": "858525799322"}
            if args[1] == "list-command-invocations":
                return {"CommandInvocations": [
                    {"InstanceId": "test-node-" + str(index), "Status": status}
                    for index, status in enumerate(statuses)
                ]}
            return {"Commands": [{"Status": parent_status, "TargetCount": count}]}

        with patch.object(task, "aws", side_effect=aws), \
             patch.object(task.sys, "argv", ["run-dev-task.py", "status", "test-only-id"]), \
             contextlib.redirect_stdout(io.StringIO()):
            return task.main()

    def test_missing_worker_is_not_success(self):
        self.assertEqual(self.outcome(["Success"], "InProgress"), 2)
        self.assertEqual(self.outcome([], "Success", count=0), 2)

    def test_all_targets_must_succeed(self):
        self.assertEqual(self.outcome(["Success", "Success"], "Success"), 0)
        self.assertEqual(self.outcome(["Success", "Failed"], "Failed"), 1)


if __name__ == "__main__":
    unittest.main()
