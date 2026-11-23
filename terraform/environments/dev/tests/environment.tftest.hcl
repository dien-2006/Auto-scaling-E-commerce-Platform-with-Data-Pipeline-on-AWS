mock_provider "aws" {

  # IAM validates this computed output even when the AWS provider is mocked.
  mock_resource "aws_s3_bucket" {
    defaults = { arn = "arn:aws:s3:::example-dev-images" }
  }

  mock_resource "aws_iam_role" {
    defaults = { arn = "arn:aws:iam::123456789012:role/mock" }
  }
  mock_resource "aws_lb" {
    defaults = { arn = "arn:aws:elasticloadbalancing:ap-southeast-1:123456789012:loadbalancer/app/mock/0000000000000000" }
  }
  mock_resource "aws_lb_target_group" {
    defaults = { arn = "arn:aws:elasticloadbalancing:ap-southeast-1:123456789012:targetgroup/mock/0000000000000000" }
  }
  mock_resource "aws_lb_listener" {
    defaults = { arn = "arn:aws:elasticloadbalancing:ap-southeast-1:123456789012:listener/app/mock/0000000000000000/0000000000000000" }
  }
  mock_resource "aws_launch_template" {
    defaults = { id = "lt-0123456789abcdef0", latest_version = 1 }
  }
  mock_resource "aws_sns_topic" {
    defaults = { arn = "arn:aws:sns:ap-southeast-1:123456789012:mock" }
  }
  mock_resource "aws_kms_key" {
    defaults = {
      arn    = "arn:aws:kms:ap-southeast-1:123456789012:key/00000000-0000-0000-0000-000000000000"
      key_id = "00000000-0000-0000-0000-000000000000"
    }
  }

  mock_data "aws_caller_identity" {
    defaults = { account_id = "123456789012", arn = "arn:aws:iam::123456789012:root" }
  }
  mock_data "aws_region" {
    defaults = { region = "ap-southeast-1", name = "ap-southeast-1" }
  }
  mock_data "aws_iam_policy_document" {
    defaults = { json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}" }
  }
  mock_resource "aws_db_instance" {
    defaults = {
      master_user_secret = [{ secret_arn = "arn:aws:secretsmanager:ap-southeast-1:123456789012:secret:test-AbCdEf", secret_status = "active", kms_key_id = "arn:aws:kms:ap-southeast-1:123456789012:key/00000000-0000-0000-0000-000000000000" }]
    }
  }
}

run "environment_wiring" {
  command = apply

  assert {
    condition = (
      module.kubernetes.worker_capacity.minimum == 2 &&
      jsondecode(aws_iam_role.cluster_autoscaler.assume_role_policy).Statement[0].Principal.AWS == module.iam.control_plane_role_arn &&
      aws_iam_role_policy.control_plane_assume_autoscaler.role == module.iam.control_plane_role_name &&
      endswith(jsondecode(aws_iam_role_policy.cluster_autoscaler.policy).Statement[1].Resource, ":autoScalingGroupName/ecommerce-dev-worker-asg") &&
      jsondecode(aws_iam_role_policy.cluster_autoscaler.policy).Statement[1].Condition.StringEquals["autoscaling:ResourceTag/k8s.io/cluster-autoscaler/ecommerce-dev-k8s"] == "owned"
    )
    error_message = "Autoscaler must retain two workers and may change only the tagged dev ASG through its dedicated control-plane-assumed role."
  }

  assert {
    condition = (
      aws_iam_role_policy.control_plane_monitoring_secret.role == module.iam.control_plane_role_name &&
      jsondecode(aws_iam_role_policy.control_plane_monitoring_secret.policy).Statement[0].Condition.StringEquals["kms:EncryptionContext:PARAMETER_ARN"] == local.monitoring_parameter_arn
    )
    error_message = "Monitoring credential decryption must be restricted to its exact SSM parameter and the control plane."
  }

  assert {
    condition = (
      jsondecode(aws_iam_role.ebs_csi.assume_role_policy).Statement[0].Principal.AWS == module.iam.control_plane_role_arn &&
      aws_iam_role_policy.control_plane_assume_ebs_csi.role == module.iam.control_plane_role_name &&
      aws_iam_role_policy_attachment.ebs_csi.policy_arn == "arn:aws:iam::aws:policy/AmazonEBSCSIDriverPolicyV2"
    )
    error_message = "CSI must use its own role assumed by the trusted control plane, not the worker web role."
  }

  assert {
    condition     = length(module.network.private_subnet_ids) == 2 && length(module.network.public_subnet_ids) == 2
    error_message = "Environment must retain two public and two private subnets."
  }
  assert {
    condition     = length(module.network.nat_gateway_ids) == 1
    error_message = "NAT count must match the environment topology."
  }
  assert {
    condition     = module.kubernetes.cluster_name == "ecommerce-dev-k8s"
    error_message = "Environment must wire its own Kubernetes cluster."
  }
  assert {
    condition     = module.kubernetes.worker_asg_name == "ecommerce-dev-worker-asg"
    error_message = "ALB and monitoring must use the environment's worker ASG."
  }

  assert {
    condition     = module.kubernetes.worker_capacity.initial == 2 && module.kubernetes.worker_capacity.maximum == 4
    error_message = "Retain two initial workers and a maximum of four."
  }
  assert {
    condition     = output.db_address == output.rds_endpoint && output.db_port == output.rds_port && output.db_name == output.rds_database_name
    error_message = "Legacy database outputs must match module-backed outputs."
  }
}

# Regression: the previous validation accepted multiple but created no NATs.
run "reject_unsupported_nat_mode" {
  command = plan
  module {
    source = "../../modules/network"
  }
  variables {
    project_name         = "ecommerce"
    environment          = "test"
    vpc_cidr             = "10.30.0.0/16"
    availability_zones   = ["ap-southeast-1a", "ap-southeast-1b"]
    public_subnet_cidrs  = ["10.30.1.0/24", "10.30.2.0/24"]
    private_subnet_cidrs = ["10.30.11.0/24", "10.30.12.0/24"]
    nat_gateway_mode     = "multiple"
  }
  expect_failures = [var.nat_gateway_mode]
}

run "reject_more_than_two_az_entries" {
  command = plan
  module {
    source = "../../modules/network"
  }
  variables {
    project_name         = "ecommerce"
    environment          = "test"
    vpc_cidr             = "10.30.0.0/16"
    availability_zones   = ["ap-southeast-1a", "ap-southeast-1b", "ap-southeast-1a"]
    public_subnet_cidrs  = ["10.30.1.0/24", "10.30.2.0/24"]
    private_subnet_cidrs = ["10.30.11.0/24", "10.30.12.0/24"]
    nat_gateway_mode     = "none"
  }
  expect_failures = [var.availability_zones]
}
