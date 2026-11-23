import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "aws/repair-node-identity.py"
SPEC = importlib.util.spec_from_file_location("coco_node_identity", SOURCE)
identity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(identity)


class NodeIdentityTests(unittest.TestCase):
    def run_repair(self, existing_provider=None, other_ip=False):
        records = [{"id": "i-0123456789abcdef0", "ip": "10.10.11.104",
                    "az": "ap-southeast-1a", "type": "t3.medium"}]
        node = {"metadata": {"name": "ip-10-10-11-104", "labels": {}},
                "spec": {"providerID": existing_provider},
                "status": {"addresses": [{"type": "InternalIP",
                          "address": "10.10.12.999" if other_ip else records[0]["ip"]}]}}
        calls = []

        def kubectl(args, **kwargs):
            calls.append(args)
            if args[1:3] == ["get", "nodes"] and "-o" in args:
                return json.dumps({"items": [node]})
            return ""

        code = identity.repair_script(records).split("python3 <<'COCO_IDENTITY_REPAIR'\n", 1)[1]
        code = code.rsplit("COCO_IDENTITY_REPAIR", 1)[0]
        with patch("subprocess.check_output", side_effect=kubectl):
            try:
                exec(compile(code, "<SSM identity repair>", "exec"), {})
            except SystemExit:
                return calls, False
        return calls, True

    def test_patch_uses_verified_ec2_identity(self):
        calls, success = self.run_repair()
        self.assertTrue(success)
        patches = [args for args in calls if args[1] == "patch"]
        self.assertEqual(len(patches), 1)
        payload = json.loads(patches[0][-1])
        self.assertEqual(payload["spec"]["providerID"],
                         "aws:///ap-southeast-1a/i-0123456789abcdef0")
        self.assertEqual(payload["metadata"]["labels"]["topology.kubernetes.io/zone"],
                         "ap-southeast-1a")

    def test_conflicting_identity_or_ip_never_patches(self):
        for options in ({"existing_provider": "aws:///wrong/i-wrong"}, {"other_ip": True}):
            with self.subTest(options=options):
                calls, success = self.run_repair(**options)
                self.assertFalse(success)
                self.assertFalse(any(args[1] == "patch" for args in calls))


if __name__ == "__main__":
    unittest.main()
