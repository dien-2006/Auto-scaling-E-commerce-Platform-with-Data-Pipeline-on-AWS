"""Offline checks: mocks only; never call AWS, Terraform, Docker or SQL."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "aws/dev-stack.py"
SPEC = importlib.util.spec_from_file_location("dev_stack_test", SOURCE)
stack = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stack)


class DevStackTests(unittest.TestCase):
    def test_destroy_requires_explicit_data_deletion_before_any_command(self):
        with patch("sys.argv", ["dev-stack.py", "destroy"]), \
                patch.object(stack, "aws") as aws, \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            stack.main()
        aws.assert_not_called()

    def test_create_plan_refuses_replacement_update_or_delete(self):
        for actions in (["delete"], ["update"], ["delete", "create"], ["create", "delete"]):
            with self.subTest(actions=actions), self.assertRaises(stack.Failure):
                stack.validate_plan({"resource_changes": [{"address": "db", "change": {"actions": actions}}]}, False)
        stack.validate_plan({"resource_changes": [{"address": "db", "change": {"actions": ["create"]}}]}, False)

    def test_destroy_plan_cannot_create_or_update_anything(self):
        for actions in (["create"], ["update"], ["delete", "create"]):
            with self.subTest(actions=actions), self.assertRaises(stack.Failure):
                stack.validate_plan({"resource_changes": [{"address": "db", "change": {"actions": actions}}]}, True)

    def test_up_refuses_existing_stack_without_its_generation(self):
        with patch.object(stack, "preflight_rebuild"), \
                patch.object(stack, "tf", return_value=json.dumps({"values": {"root_module": {
                    "resources": [{"mode": "managed", "type": "aws_db_instance"}]
                }}})), patch.object(stack, "stage") as stage, self.assertRaises(stack.Failure):
            stack.up({})
        stage.assert_not_called()

    def test_up_refuses_incomplete_destroy_even_if_terraform_state_is_empty(self):
        with patch.object(stack, "preflight_rebuild"), patch.object(stack, "tf", return_value="{}"), \
                patch.object(stack, "stage") as stage, self.assertRaises(stack.Failure):
            stack.up({"mode": "destroying"})
        stage.assert_not_called()

    def test_wrong_rds_generation_stops_before_secret_tunnel_or_sql(self):
        with patch.object(stack, "aws", return_value={"DBInstances": [{"DbiResourceId": "new-id"}]}), \
                patch.object(stack, "run") as run, patch.object(stack.subprocess, "Popen") as tunnel, \
                self.assertRaises(stack.Failure):
            stack.import_new_database({"rds_resource_id": "old-id"})
        run.assert_not_called()
        tunnel.assert_not_called()

    def test_only_exact_cluster_csi_volumes_in_project_namespaces_are_owned(self):
        tags = {"kubernetes.io/cluster/" + stack.CLUSTER: "owned", "ebs.csi.aws.com/cluster": "true",
                "kubernetes.io/created-for/pvc/namespace": "monitoring"}
        volume = {"AvailabilityZone": "ap-southeast-1a", "Tags": [{"Key": k, "Value": v} for k, v in tags.items()]}
        self.assertTrue(stack.owned_volume(volume))
        for key in tags:
            bad = {**volume, "Tags": [t for t in volume["Tags"] if t["Key"] != key]}
            self.assertFalse(stack.owned_volume(bad))
        self.assertFalse(stack.owned_volume({**volume, "AvailabilityZone": "us-east-1a"}))

    def test_s3_cleanup_deletes_versions_and_markers_before_current_objects(self):
        bucket = sorted(stack.BUCKETS)[0]
        pages = [
            {},
            {"Versions": [{"Key": "logo/1.png", "VersionId": "old"}],
             "DeleteMarkers": [{"Key": "logo/1.png", "VersionId": "marker"}]},
            {}, {}, {},
        ]
        with patch.object(stack, "aws", side_effect=pages), \
                patch.object(stack, "delete_objects", return_value={}) as delete:
            stack.empty_bucket(bucket)
        self.assertEqual(delete.call_args.args, (bucket, [
            {"Key": "logo/1.png", "VersionId": "old"}, {"Key": "logo/1.png", "VersionId": "marker"}]))

    def test_delete_payload_uses_private_file_and_expected_owner(self):
        def aws(*args):
            self.assertIn(stack.ACCOUNT, args)
            path = Path(args[args.index("--delete") + 1].removeprefix("file://"))
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(path.read_text())["Objects"], [{"Key": "image"}])
            return {}
        with patch.object(stack, "aws", side_effect=aws):
            stack.delete_objects(sorted(stack.BUCKETS)[0], [{"Key": "image"}])

    def test_unrelated_buckets_and_repositories_cannot_be_emptied(self):
        with patch.object(stack, "aws") as aws:
            with self.assertRaises(stack.Failure):
                stack.empty_bucket("production-images")
            with self.assertRaises(stack.Failure):
                stack.empty_repo("ecommerce/prod/backend")
        aws.assert_not_called()

    def test_completed_stage_is_not_repeated_and_failed_stage_is_not_recorded(self):
        record = {"done": ["already"]}
        with patch.object(stack, "save") as save, contextlib.redirect_stdout(io.StringIO()):
            with patch.object(stack, "apply_plan") as action:
                stack.stage(record, "already", action)
                action.assert_not_called()
            def fail():
                raise stack.Failure("test failure")
            with self.assertRaises(stack.Failure):
                stack.stage(record, "failed", fail)
        self.assertNotIn("failed", record["done"])
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
