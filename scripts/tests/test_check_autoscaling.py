"""Check the live-bootstrap gate without making AWS requests."""
import importlib.util
from pathlib import Path
import base64
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "aws/check-autoscaling-dev.py"
SPEC = importlib.util.spec_from_file_location("check_autoscaling_dev", SOURCE)
inspect = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inspect)


class AutoscalingGateTests(unittest.TestCase):
    def test_old_live_template_is_rejected_even_if_local_source_was_fixed(self):
        group = {"MinSize": 1, "DesiredCapacity": 2, "MaxSize": 4,
                 "AvailabilityZones": ["ap-southeast-1a", "ap-southeast-1b"],
                 "Tags": [{"Key": "k8s.io/cluster-autoscaler/enabled", "Value": "true"},
                          {"Key": "k8s.io/cluster-autoscaler/ecommerce-dev-k8s", "Value": "owned"}]}
        template = {"UserData": base64.b64encode(b"apt-get install -y awscli").decode(),
                    "MetadataOptions": {"HttpTokens": "required", "HttpPutResponseHopLimit": 2}}
        checks = inspect.inspect_group(group, template)
        self.assertTrue(checks["discovery_enabled"])
        self.assertFalse(checks["awscli_official_installer"])
        self.assertFalse(checks["aws_provider_identity"])
        self.assertFalse(checks["join_current_cluster"])


if __name__ == "__main__":
    unittest.main()
