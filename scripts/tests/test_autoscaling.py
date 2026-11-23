"""Offline autoscaling safety gates. No AWS, Terraform, kubectl or test workloads run."""
import base64
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load("prepare_autoscaling", "scripts/aws/prepare-autoscaling-dev.py")
guard = load("guard_autoscaling", "scripts/aws/guard-autoscaling-plan.py")
protection = load("protect_autoscaling", "scripts/k8s/protect-scaling-baseline.py")


def node(name, zone, instance, annotations=None):
    return {"metadata": {"name": name, "creationTimestamp": "2026-11-22T00:00:00Z",
                         "labels": {"topology.kubernetes.io/zone": zone}, "annotations": annotations or {}},
            "spec": {"providerID": f"aws:///{zone}/{instance}"},
            "status": {"conditions": [{"type": "Ready", "status": "True"}]}}


def group():
    return {"AutoScalingGroupName": "ecommerce-dev-worker-asg", "MinSize": 1, "MaxSize": 4,
            "DesiredCapacity": 2, "AvailabilityZones": ["ap-southeast-1a", "ap-southeast-1b"],
            "LaunchTemplate": {"LaunchTemplateId": "lt-0123456789abcdef0", "Version": "$Latest"},
            "Tags": [{"Key": "k8s.io/cluster-autoscaler/enabled", "Value": "true"},
                     {"Key": "k8s.io/cluster-autoscaler/ecommerce-dev-k8s", "Value": "owned"}],
            "Instances": [{"InstanceId": instance, "AvailabilityZone": zone,
                           "LifecycleState": "InService", "HealthStatus": "Healthy"}
                          for instance, zone in [("i-first", "ap-southeast-1a"), ("i-second", "ap-southeast-1b")]]}


class PlanGateTests(unittest.TestCase):
    def test_targeted_plan_cannot_hide_control_plane_update_or_resource_replacement(self):
        for address, actions in [("module.kubernetes.aws_instance.control_plane", ["update"]),
                                 ("aws_iam_role.cluster_autoscaler", ["delete", "create"]),
                                 ("module.database.aws_db_instance.this", ["update"])]:
            with self.subTest(address=address), self.assertRaises(ValueError):
                guard.validate({"resource_changes": [{"address": address, "change": {"actions": actions}}]})

    def test_only_the_three_iam_resources_are_accepted(self):
        guard.validate({"resource_changes": [{"address": name, "change": {"actions": ["create"]}}
                                             for name in guard.ALLOWED]})


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.nodes = [node("a", "ap-southeast-1a", "i-first"), node("b", "ap-southeast-1b", "i-second")]

    def test_two_zones_and_pvc_node_are_preserved(self):
        inventory = group()
        self.nodes.append(node("extra", "ap-southeast-1a", "i-extra"))
        self.nodes[-1]["metadata"]["creationTimestamp"] = "2026-11-22T01:00:00Z"
        inventory["Instances"].append({"InstanceId": "i-extra", "AvailabilityZone": "ap-southeast-1a",
                                       "LifecycleState": "InService", "HealthStatus": "Healthy"})
        pods = [{"spec": {"nodeName": "extra", "volumes": [{"persistentVolumeClaim": {"claimName": "prometheus"}}]}}]
        baseline, protected = protection.select_protected(self.nodes, pods, inventory)
        self.assertEqual(baseline, {"a", "b"})
        self.assertEqual(protected, {"a", "b", "extra"})

    def test_foreign_node_or_missing_az_blocks_patches(self):
        self.nodes[0]["spec"]["providerID"] = "aws:///ap-southeast-1a/i-unrelated"
        with self.assertRaises(ValueError):
            protection.select_protected(self.nodes, [], group())

    def test_protected_baseline_is_reused_on_repeat_install(self):
        self.nodes[0]["metadata"]["annotations"][protection.BASELINE] = "true"
        baseline, protected = protection.select_protected(self.nodes, [], group())
        self.assertEqual(baseline, {"a", "b"})
        self.assertEqual(protected, baseline)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.inventory = group()
        source = ("#!/bin/bash\nawscli.amazonaws.com/awscli-exe-linux-x86_64.zip\n"
                  "COCO_AWS_NODE_ARGS=--provider-id=aws:///AZ/ID\ncoco-ecr-credential-provider\n"
                  "kubeadm join 10.10.11.127:6443 token\nworker_joined\n"
                  "pkgs.k8s.io/core:/stable:/v1.34/\n")
        self.config = {"bootstrap": base64.b64encode(source.encode()).decode(),
                       "template_id": "lt-0123456789abcdef0", "control_plane_ip": "10.10.11.127"}
        self.old = {"VersionNumber": 1, "LaunchTemplateData": {"UserData": "", "ImageId": "ami-existing",
                    "MetadataOptions": {"HttpTokens": "required", "HttpPutResponseHopLimit": 1}}}
        self.calls = []

    def aws(self, *args):
        self.calls.append(args)
        if args[:2] == ("ec2", "describe-instances"):
            return {"Reservations": [{"Instances": [{"PrivateIpAddress": "10.10.11.127"}]}]}
        if args[:2] == ("ec2", "create-launch-template-version"):
            data = json.loads(args[args.index("--launch-template-data") + 1])
            self.assertEqual(set(data), {"UserData", "MetadataOptions"})
            self.assertEqual(args[args.index("--source-version") + 1], "1")
            return {"LaunchTemplateVersion": {"VersionNumber": 2}}
        if args[:2] == ("autoscaling", "update-auto-scaling-group"):
            self.assertNotIn("--desired-capacity", args)
            self.assertNotIn("--vpc-zone-identifier", args)
            self.assertIn('"Version": "2"', args[args.index("--launch-template") + 1])
            return {}
        raise AssertionError(args)

    def context(self):
        self.enterContext(patch.object(prepare, "current_group", return_value=copy.deepcopy(self.inventory)))
        self.enterContext(patch.object(prepare, "current_template", return_value=copy.deepcopy(self.old)))
        self.enterContext(patch.object(prepare, "source_bootstrap", return_value=self.config))
        self.enterContext(patch.object(prepare, "aws", side_effect=self.aws))

    def test_preview_has_no_mutating_aws_calls(self):
        self.context()
        prepare.bootstrap()
        self.assertEqual([call[:2] for call in self.calls], [("ec2", "describe-instances")])

    def test_submit_changes_future_workers_only_and_does_not_start_instance_refresh(self):
        self.context()
        prepare.bootstrap(submit=True)
        self.assertEqual([call[:2] for call in self.calls], [
            ("ec2", "describe-instances"), ("ec2", "create-launch-template-version"),
            ("autoscaling", "update-auto-scaling-group"),
        ])

    def test_wrong_account_stops_before_any_preparation(self):
        with patch.object(prepare, "aws", return_value={"Account": "000000000000"}) as aws, \
                patch("sys.argv", ["prepare-autoscaling-dev.py"]), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(prepare.main(), 1)
            self.assertEqual(aws.call_count, 1)

    def test_terraform_console_evaluates_source_bootstrap_not_old_state_attribute(self):
        calls = []
        def command(args, input_text=None):
            calls.append((args, input_text))
            return json.dumps(json.dumps(self.config))
        with patch.object(prepare, "command", side_effect=command):
            self.assertEqual(prepare.source_bootstrap(), self.config)
        self.assertIn("worker_bootstrap_base64", calls[0][1])
        self.assertNotIn("plan", calls[0][0])

    def test_empty_cli_update_response_is_valid(self):
        with patch.object(prepare, "command", return_value=""):
            self.assertEqual(prepare.aws("autoscaling", "update-auto-scaling-group"), {})

    def test_wrong_control_plane_ip_prevents_template_or_asg_mutation(self):
        self.config["control_plane_ip"] = "10.10.11.99"
        self.context()
        with self.assertRaisesRegex(ValueError, "Control-plane IP"):
            prepare.bootstrap(submit=True)
        self.assertEqual([call[:2] for call in self.calls], [("ec2", "describe-instances")])

    def test_render_uses_the_applied_role_without_deploying_kubernetes_resources(self):
        inventory = group()
        inventory["MinSize"] = 2
        version = copy.deepcopy(self.old)
        version["LaunchTemplateData"]["UserData"] = self.config["bootstrap"]
        version["LaunchTemplateData"]["MetadataOptions"]["HttpPutResponseHopLimit"] = 2
        source = (ROOT / "k8s/autoscaling/cluster-autoscaler-dev.yaml").read_text()
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(prepare, "ROOT", Path(directory)), \
                patch.object(prepare, "command", return_value=prepare.ROLE) as command, \
                patch.object(prepare, "current_group", return_value=inventory), \
                patch.object(prepare, "current_template", return_value=version):
            template = Path(directory) / "k8s/autoscaling/cluster-autoscaler-dev.yaml"
            template.parent.mkdir(parents=True)
            template.write_text(source)
            prepare.render()
            output = (Path(directory) / "artifacts/deploy/dev/cluster-autoscaler.yaml").read_text()
        self.assertIn(prepare.ROLE, output)
        self.assertNotIn("REPLACE_AUTOSCALER_ROLE_ARN", output)
        self.assertIn("AWS_SDK_LOAD_CONFIG", output)
        self.assertEqual(command.call_count, 1)


if __name__ == "__main__":
    unittest.main()
