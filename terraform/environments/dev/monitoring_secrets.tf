locals {
  monitoring_parameter_name = "/ecommerce/dev/monitoring/secrets"
  monitoring_parameter_arn  = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.deployment.account_id}:parameter${local.monitoring_parameter_name}"
}

# Keep monitoring credentials separate from the backend Pod's runtime Secret.
resource "aws_iam_role_policy" "control_plane_monitoring_secret" {
  name = "ecommerce-dev-read-monitoring-secret"
  role = module.iam.control_plane_role_name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["kms:Decrypt"]
      Resource = aws_kms_key.deployment_secrets.arn
      Condition = {
        StringEquals = {
          "kms:ViaService"                     = "ssm.${var.aws_region}.amazonaws.com"
          "kms:EncryptionContext:PARAMETER_ARN" = local.monitoring_parameter_arn
        }
      }
    }]
  })
}
