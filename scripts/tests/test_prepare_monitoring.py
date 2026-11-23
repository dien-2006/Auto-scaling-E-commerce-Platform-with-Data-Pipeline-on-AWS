import contextlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "aws/prepare-monitoring-dev.py"
SPEC = importlib.util.spec_from_file_location("prepare_monitoring", SOURCE)
monitoring = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(monitoring)
CONFIG = """global:
  smtp_smarthost: smtp.mailer.test:587
  smtp_from: alerts@mailer.test
  smtp_auth_username: alerts@mailer.test
  smtp_auth_password_file: /etc/alertmanager/secrets/alertmanager-smtp-auth/password
  smtp_require_tls: true
receivers:
  - name: team-email
    email_configs:
      - to: ops@mailer.test
"""


class MonitoringPreparationTests(unittest.TestCase):
    def test_reuse_renders_without_prompting_or_changing_passwords(self):
        payload = {"alertmanager.yaml": CONFIG, "smtp-password": "private-smtp-password",
                   "grafana-user": "admin", "grafana-password": "private-grafana-password"}
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            (destination / "alertmanager.yaml").write_text(CONFIG)
            (destination / "monitoring-secrets.json").write_text(json.dumps(payload))
            with patch.object(monitoring, "DESTINATION", destination), \
                    patch.object(monitoring.sys, "argv", ["prepare-monitoring-dev.py", "--reuse-credentials"]), \
                    patch.object(monitoring, "command", side_effect=[
                        '{"Account":"858525799322"}', '# helm render', '# custom resources',
                    ]), patch("builtins.input") as prompt, \
                    patch.object(monitoring.getpass, "getpass") as password, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(monitoring.main(), 0)
            self.assertEqual(json.loads((destination / "monitoring-secrets.json").read_text()), payload)
            prompt.assert_not_called()
            password.assert_not_called()

    def test_credentials_remain_private_and_preparation_does_not_store_or_deploy(self):
        password, smtp = "unit-test-only-password", "smtp-test-only-password"
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            (destination / "alertmanager.yaml").write_text(CONFIG)
            with patch.object(monitoring, "DESTINATION", destination), \
                    patch.object(monitoring.sys, "argv", ["prepare-monitoring-dev.py"]), \
                    patch.object(monitoring, "command", side_effect=[
                        '{"Account":"858525799322"}', '# helm render', '# custom resources',
                    ]) as commands, \
                    patch("builtins.input", return_value="admin"), \
                    patch.object(monitoring.getpass, "getpass", side_effect=[password, password, smtp]), \
                    contextlib.redirect_stdout(output):
                self.assertEqual(monitoring.main(), 0)
            private_file = destination / "monitoring-secrets.json"
            self.assertEqual(stat.S_IMODE(private_file.stat().st_mode), 0o600)
            self.assertEqual(json.loads(private_file.read_text())["smtp-password"], smtp)
            calls = [call.args[0] for call in commands.call_args_list]
            self.assertEqual(calls[0][1:3], ["sts", "get-caller-identity"])
            self.assertEqual(calls[1][:2], ["helm", "template"])
            self.assertEqual(calls[2][:2], ["kubectl", "kustomize"])
            self.assertNotIn(password, output.getvalue())
            self.assertNotIn(smtp, output.getvalue())

    def test_rejects_placeholder_or_inline_secret(self):
        for config in (CONFIG.replace("mailer.test", "example.com"),
                       CONFIG + "  smtp_auth_password: must-not-inline\n",
                       CONFIG.replace("smtp_require_tls: true", "smtp_require_tls: false")):
            with self.subTest(config=config), self.assertRaises(ValueError):
                monitoring.validate_config(config)

    def test_store_uses_private_file_and_correct_parameter_not_command_line_passwords(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            (destination / "alertmanager.yaml").write_text(CONFIG)
            payload = {"alertmanager.yaml": CONFIG, "smtp-password": "private-smtp-password",
                       "grafana-user": "admin", "grafana-password": "private-grafana-password"}
            (destination / "monitoring-secrets.json").write_text(json.dumps(payload))
            output = io.StringIO()
            with patch.object(monitoring, "DESTINATION", destination), \
                    patch.object(monitoring.sys, "argv", ["prepare-monitoring-dev.py", "--store"]), \
                    patch.object(monitoring, "command", side_effect=[
                        '{"Account":"858525799322"}',
                        'arn:aws:kms:ap-southeast-1:858525799322:key/00000000-0000-0000-0000-000000000000',
                        '{"Version":1}',
                    ]) as commands, contextlib.redirect_stdout(output):
                self.assertEqual(monitoring.main(), 0)
            call = commands.call_args_list[-1].args[0]
            self.assertIn("/ecommerce/dev/monitoring/secrets", call)
            self.assertIn("SecureString", call)
            self.assertTrue(call[call.index("--value") + 1].startswith("file://"))
            self.assertNotIn(payload["smtp-password"], " ".join(call) + output.getvalue())


if __name__ == "__main__":
    unittest.main()
