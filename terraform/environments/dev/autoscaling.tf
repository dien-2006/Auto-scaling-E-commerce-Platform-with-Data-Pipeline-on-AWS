# kubeadm dev runs the controller on the trusted control plane. This is a
# node trust boundary (as with CSI), not EKS IRSA/Pod Identity.
# Runtime action list follows the published upstream v1.34 AWS permissions:
# https://github.com/kubernetes/autoscaler/blob/cluster-autoscaler-1.34.6/cluster-autoscaler/cloudprovider/aws/README.md#iam-policy
# Write access is restricted to the one dev ASG and its discovery tags.
resource "aws_iam_role" "cluster_autoscaler" {
  name = "ecommerce-dev-cluster-autoscaler"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { AWS = module.iam.control_plane_role_arn }
    }]
  })
  tags = local.common_tags
}

resource "aws_iam_role_policy" "cluster_autoscaler" {
  name = "ecommerce-dev-worker-scaling"
  role = aws_iam_role.cluster_autoscaler.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadWorkerCapacity"
        Effect = "Allow"
        Action = [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeAutoScalingInstances",
          "autoscaling:DescribeLaunchConfigurations",
          "autoscaling:DescribeScalingActivities",
          "ec2:DescribeImages",
          "ec2:DescribeInstanceTypes",
          "ec2:DescribeLaunchTemplateVersions",
          "ec2:GetInstanceTypesFromInstanceRequirements"
        ]
        Resource = "*"
      },
      {
        Sid      = "ScaleOnlyDevWorkers"
        Effect   = "Allow"
        Action   = ["autoscaling:SetDesiredCapacity", "autoscaling:TerminateInstanceInAutoScalingGroup"]
        Resource = "arn:aws:autoscaling:${var.aws_region}:${data.aws_caller_identity.deployment.account_id}:autoScalingGroup:*:autoScalingGroupName/ecommerce-dev-worker-asg"
        Condition = {
          StringEquals = {
            "autoscaling:ResourceTag/k8s.io/cluster-autoscaler/enabled"           = "true"
            "autoscaling:ResourceTag/k8s.io/cluster-autoscaler/ecommerce-dev-k8s" = "owned"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "control_plane_assume_autoscaler" {
  name = "ecommerce-dev-assume-cluster-autoscaler"
  role = module.iam.control_plane_role_name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sts:AssumeRole"]
      Resource = aws_iam_role.cluster_autoscaler.arn
    }]
  })
}

output "cluster_autoscaler_role_arn" {
  value = aws_iam_role.cluster_autoscaler.arn
}
