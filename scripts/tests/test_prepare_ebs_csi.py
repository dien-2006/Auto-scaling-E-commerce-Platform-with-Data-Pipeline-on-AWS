import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "aws/prepare-ebs-csi-dev.py"
SPEC = importlib.util.spec_from_file_location("prepare_ebs_csi", SOURCE)
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


class CsiRenderTests(unittest.TestCase):
    def test_role_profile_and_controller_host_network_are_rendered_without_deployment(self):
        calls = []

        def command(args):
            calls.append(args)
            if args[0] == "aws":
                self.assertEqual(args[1:3], ["sts", "get-caller-identity"])
                return json.dumps({"Account": "858525799322"})
            if args[0] == "terraform":
                return "arn:aws:iam::858525799322:role/ecommerce-dev-ebs-csi"
            if args[0] == "helm":
                self.assertEqual(args[1], "template")
                self.assertIn("2.67.1", args)
                self.assertIn("--skip-tests", args)
                return "kind: Deployment\nmetadata:\n  name: ebs-csi-controller\n# v1.67.2\n"
            self.assertEqual(args[:2], ["kubectl", "kustomize"])
            directory = Path(args[2])
            customization = json.loads((directory / "kustomization.yaml").read_text())
            operations = json.loads(customization["patches"][0]["patch"])
            self.assertEqual(operations[0]["path"], "/spec/template/spec/hostNetwork")
            self.assertIs(operations[0]["value"], True)
            profile = json.loads((directory / "profile.json").read_text())["data"]["config"]
            self.assertIn("credential_source = Ec2InstanceMetadata", profile)
            self.assertNotIn("aws_access_key_id", profile)
            return "# rendered CSI manifest\n"

        with tempfile.TemporaryDirectory() as directory, \
                patch.object(renderer, "ROOT", Path(directory)), \
                patch.object(renderer, "command", side_effect=command), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(renderer.main(), 0)
            self.assertTrue((Path(directory) / "artifacts/deploy/dev/ebs-csi.yaml").is_file())
        self.assertEqual(len(calls), 4)

    def test_wrong_account_stops_before_terraform_or_helm(self):
        with patch.object(renderer, "command", return_value='{"Account":"000000000000"}') as command, \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(renderer.main(), 1)
            self.assertEqual(command.call_count, 1)

    def test_helm_tester_resources_are_rejected_before_saving_manifest(self):
        responses = [
            '{"Account":"858525799322"}',
            'arn:aws:iam::858525799322:role/ecommerce-dev-ebs-csi',
            'name: ebs-csi-controller\n# v1.67.2\nkind: Pod\nname: ebs-csi-driver-test\n',
        ]
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(renderer, "ROOT", Path(directory)), \
                patch.object(renderer, "command", side_effect=responses) as command, \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(renderer.main(), 1)
            self.assertEqual(command.call_count, 3)
            self.assertFalse((Path(directory) / "artifacts/deploy/dev/ebs-csi.yaml").exists())


if __name__ == "__main__":
    unittest.main()
