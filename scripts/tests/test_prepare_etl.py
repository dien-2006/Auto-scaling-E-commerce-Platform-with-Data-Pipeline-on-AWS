import contextlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "aws/prepare-etl-dev.py"
SPEC = importlib.util.spec_from_file_location("prepare_etl_dev", SOURCE)
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)


class EtlConfigurationTests(unittest.TestCase):
    def test_missing_output_explains_the_real_error_without_writing_configuration(self):
        error = subprocess.CalledProcessError(1, ["terraform", "output"],
                                             stderr='Error: Output "etl_config" not found')
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(prepare, "ROOT", Path(directory)), \
                patch.object(prepare.subprocess, "run", side_effect=error), \
                contextlib.redirect_stderr(output):
            self.assertEqual(prepare.main(), 1)
            self.assertFalse((Path(directory) / "artifacts/deploy/dev/etl.env").exists())
        self.assertIn('Output "etl_config" not found', output.getvalue())
        self.assertIn("NEW plan", output.getvalue())

    def test_valid_applied_output_writes_private_configuration_only(self):
        config = {"COCO_ENV": "dev", "AWS_REGION": "ap-southeast-1",
                  "AWS_ACCOUNT_ID": "858525799322", "ETL_BUCKET": "test-data-lake",
                  "GLUE_SCHEDULE": "cron(0 18 * * ? *)"}
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(prepare, "ROOT", Path(directory)), \
                patch.object(prepare.subprocess, "run", return_value=subprocess.CompletedProcess(
                    ["terraform"], 0, stdout=json.dumps(config))), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(prepare.main(), 0)
            result = Path(directory) / "artifacts/deploy/dev/etl.env"
            self.assertEqual(stat.S_IMODE(result.stat().st_mode), 0o600)
            self.assertIn("GLUE_SCHEDULE='cron(0 18 * * ? *)'", result.read_text())

    def test_stale_schedule_does_not_overwrite_existing_configuration(self):
        config = {"COCO_ENV": "dev", "AWS_REGION": "ap-southeast-1",
                  "AWS_ACCOUNT_ID": "858525799322", "GLUE_SCHEDULE": "cron(0 1 * * ? *)"}
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(prepare, "ROOT", Path(directory)), \
                patch.object(prepare.subprocess, "run", return_value=subprocess.CompletedProcess(
                    ["terraform"], 0, stdout=json.dumps(config))), \
                contextlib.redirect_stderr(io.StringIO()):
            result = Path(directory) / "artifacts/deploy/dev/etl.env"
            result.parent.mkdir(parents=True)
            result.write_text("keep existing config\n")
            self.assertEqual(prepare.main(), 1)
            self.assertEqual(result.read_text(), "keep existing config\n")


if __name__ == "__main__":
    unittest.main()
