import base64
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

source = Path(__file__).resolve().parents[1] / "k8s/ecr-credential-provider.py"
spec = importlib.util.spec_from_file_location("coco_ecr_provider", source)
provider = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)


class CredentialProviderTests(unittest.TestCase):
    def request(self, image="858525799322.dkr.ecr.ap-southeast-1.amazonaws.com/ecommerce/dev/backend:v1"):
        return {"kind": "CredentialProviderRequest",
                "apiVersion": "credentialprovider.kubelet.k8s.io/v1", "image": image}

    def test_scoped_response_uses_temporary_ecr_token(self):
        calls = []

        def aws(args, **kwargs):
            calls.append((args, kwargs))
            return SimpleNamespace(stdout=json.dumps({"authorizationData": [{
                "proxyEndpoint": "https://858525799322.dkr.ecr.ap-southeast-1.amazonaws.com",
                "authorizationToken": base64.b64encode(b"AWS:test-only-password").decode(),
            }]}))

        with patch.object(provider.shutil, "which", return_value="/usr/local/bin/aws"):
            result = provider.credentials(self.request(), run=aws)
        self.assertEqual(result["kind"], "CredentialProviderResponse")
        self.assertEqual(result["cacheDuration"], "10m")
        self.assertEqual(list(result["auth"]), ["858525799322.dkr.ecr.ap-southeast-1.amazonaws.com"])
        self.assertEqual(calls[0][0][1:3], ["ecr", "get-authorization-token"])
        self.assertIn("858525799322", calls[0][0])
        self.assertIn("ap-southeast-1", calls[0][0])

    def test_rejects_untrusted_registry_or_protocol_without_aws_call(self):
        for image in ("evil.example/repo:v1", "858525799322.dkr.ecr.ap-southeast-1.amazonaws.com.evil/repo:v1"):
            with self.subTest(image=image), self.assertRaises(ValueError):
                provider.credentials(self.request(image))
        request = self.request()
        request["apiVersion"] = "untrusted/v1"
        with self.assertRaises(ValueError):
            provider.credentials(request)


if __name__ == "__main__":
    unittest.main()
