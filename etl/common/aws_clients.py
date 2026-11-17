
import boto3

from botocore.config import Config
from common.config import get_settings


class AWSClients:
    def __init__(self):
        self.settings = get_settings()

        options = {
            "region_name": self.settings.region,
        }

        if self.settings.profile:
            options["profile_name"] = self.settings.profile

        self.session = boto3.Session(**options)

        config = Config(
            retries={
                "mode": "standard",
                "max_attempts": 3,
            }
        )

        self.sts = self.session.client("sts", config=config)

        identity = self.sts.get_caller_identity()

        if identity["Account"] != self.settings.account_id:
            raise RuntimeError(
                "AWS account mismatch: "
                f"{identity['Account']} != "
                f"{self.settings.account_id}"
            )

        self.identity = identity

        self.s3 = self.session.client("s3", config=config)
        self.glue = self.session.client("glue", config=config)
        self.athena = self.session.client("athena", config=config)

        print(
            f"AWS: {identity['Account']} | "
            f"{self.settings.region} | "
            f"COCO {self.settings.environment}"
        )
