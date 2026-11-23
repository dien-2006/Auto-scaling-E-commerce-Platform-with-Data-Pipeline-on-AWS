# Self-managed kubeadm dev: only the trusted control plane may assume this role.
# No EBS permissions are attached to the web worker instance role.
resource "aws_iam_role" "ebs_csi" {
  name = "ecommerce-dev-ebs-csi"
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

resource "aws_iam_role_policy_attachment" "ebs_csi" {
  role       = aws_iam_role.ebs_csi.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEBSCSIDriverPolicyV2"
}

resource "aws_iam_role_policy" "control_plane_assume_ebs_csi" {
  name = "ecommerce-dev-assume-ebs-csi"
  role = module.iam.control_plane_role_name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sts:AssumeRole"]
      Resource = aws_iam_role.ebs_csi.arn
    }]
  })
}

output "ebs_csi_role_arn" {
  description = "Dev CSI role assumed using the trusted control-plane instance credentials"
  value       = aws_iam_role.ebs_csi.arn
}
