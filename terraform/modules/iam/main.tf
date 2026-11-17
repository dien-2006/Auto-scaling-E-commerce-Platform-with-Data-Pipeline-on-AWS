# Tạo IAM Trust Policy
locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    effect = "Allow"

    actions = [
      "sts:AssumeRole"
    ]

    principals {
      type = "Service"

      identifiers = [
        "ec2.amazonaws.com"
      ]
    }
  }
}

# Tạo IAM Role cho Control Plane

resource "aws_iam_role" "control_plane" {
  name = "${local.name_prefix}-control-plane-role"

  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-control-plane-role"
  })
}

# Gắn SSM Policy cho Control Plane

resource "aws_iam_role_policy_attachment" "control_plane_ssm" {
  role = aws_iam_role.control_plane.name

  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Tạo Instance Profile cho Control Plane

resource "aws_iam_instance_profile" "control_plane" {
  name = "${local.name_prefix}-control-plane-profile"

  role = aws_iam_role.control_plane.name

  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-control-plane-profile"
  })
}

# Tạo IAM Role cho Worker EC2

resource "aws_iam_role" "worker" {
  name = "${local.name_prefix}-worker-role"

  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-worker-role"
  })
}

# Gắn SSM Policy cho Worker

resource "aws_iam_role_policy_attachment" "worker_ssm" {
  role = aws_iam_role.worker.name

  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Gắn ECR Pull Policy cho Worker

resource "aws_iam_role_policy_attachment" "worker_ecr_pull" {
  role = aws_iam_role.worker.name

  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPullOnly"
}

# Tạo Instance Profile cho Worker

resource "aws_iam_instance_profile" "worker" {
  name = "${local.name_prefix}-worker-profile"

  role = aws_iam_role.worker.name

  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-worker-profile"
  })
}

