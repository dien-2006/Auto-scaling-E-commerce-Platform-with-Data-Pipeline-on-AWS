import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

source = Path(__file__).resolve().parents[1] / "aws/prepare-dev-release.py"
spec = importlib.util.spec_from_file_location("prepare_release", source)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleasePreparationTests(unittest.TestCase):
    def test_render_preserves_secrets_and_never_leaks_them(self):
        outputs = {name: {"value": value} for name, value in {
            "images_bucket_name": "ecommerce-dev-product-images-858525799322-ap-southeast-1",
            "alb_dns_name": "dev.example.elb.amazonaws.com",
            "cloudfront_images_url": "https://cdn.example.cloudfront.net",
            "rds_master_secret_arn": "test-only-secret-arn",
            "rds_endpoint": "dev.example.rds.amazonaws.com",
            "rds_port": 5432, "rds_database_name": "coco_marketplace",
            "ecr_backend_url": "858525799322.dkr.ecr.ap-southeast-1.amazonaws.com/ecommerce/dev/backend",
            "ecr_frontend_url": "858525799322.dkr.ecr.ap-southeast-1.amazonaws.com/ecommerce/dev/frontend",
        }.items()}

        def command(args):
            if args[0] == "terraform":
                return json.dumps(outputs)
            if args[1] == "sts":
                return json.dumps({"Account": "858525799322"})
            if args[1] == "secretsmanager":
                return json.dumps({"SecretString": json.dumps({
                    "username": "test-only-user", "password": "test-only-rds-password"
                })})
            if "metrics-server/dev" in args[-1]:
                return "kind: Deployment\nmetadata: {name: metrics-server}\n"
            return (
                "image: ACCOUNT_ID.dkr.ecr.ap-southeast-1.amazonaws.com/ecommerce/dev/backend:v1.0.0\n"
                "origin: http://REPLACE_WITH_DEV_ALB\ncdn: https://REPLACE_WITH_CLOUDFRONT\n"
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = root / ".env"
            env.write_text(
                "MARKETPLACE_SMTP_HOST=smtp.example.com\nMARKETPLACE_SMTP_USERNAME=test-user\n"
                "MARKETPLACE_SMTP_PASSWORD=test-only-smtp-password\n"
                "MARKETPLACE_OTP_FROM_EMAIL=alerts@example.com\nAWS_SECRET_ACCESS_KEY=never-copy-this\n"
            )
            destination = root / "release"
            captured = io.StringIO()
            with patch.object(release, "ROOT", root), patch.object(release, "DESTINATION", destination), \
                 patch.object(release, "command", side_effect=command), contextlib.redirect_stdout(captured):
                release.prepare("dev-test", env)
                first = release.env_values(destination / "backend-secret.env")
                release.prepare("dev-test-2", env)
                second = release.env_values(destination / "backend-secret.env")
            self.assertEqual(first["MARKETPLACE_JWT_SECRET"], second["MARKETPLACE_JWT_SECRET"])
            self.assertEqual((destination / "backend-secret.env").stat().st_mode & 0o777, 0o600)
            self.assertNotIn("AWS_SECRET_ACCESS_KEY", second)
            self.assertNotIn("test-only-rds-password", captured.getvalue())
            self.assertNotIn("test-only-smtp-password", captured.getvalue())
            self.assertNotIn(first["MARKETPLACE_JWT_SECRET"], captured.getvalue())
            self.assertNotIn("ACCOUNT_ID", (destination / "application.yaml").read_text())
            self.assertIn(":dev-test-2", (destination / "application.yaml").read_text())


if __name__ == "__main__":
    unittest.main()
