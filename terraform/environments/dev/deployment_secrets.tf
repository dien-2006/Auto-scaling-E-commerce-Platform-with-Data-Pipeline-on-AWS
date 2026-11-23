# Store deployment credentials outside SSM command payloads and Terraform state.
# The owner writes the SecureString value separately with this customer-managed key.
data "aws_caller_identity" "deployment" {}

locals {
  backend_env_parameter_name = "/ecommerce/dev/application/backend-env"
  backend_env_parameter_arn  = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.deployment.account_id}:parameter${local.backend_env_parameter_name}"
}

resource "aws_kms_key" "deployment_secrets" {
  description             = "Encrypt dev deployment credentials in SSM Parameter Store"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  tags                    = local.common_tags
}

resource "aws_kms_alias" "deployment_secrets" {
  name          = "alias/ecommerce-dev-deployment-secrets"
  target_key_id = aws_kms_key.deployment_secrets.key_id
}

resource "aws_iam_role_policy" "control_plane_deployment_secrets" {
  name = "ecommerce-dev-read-deployment-secret"
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
          "kms:EncryptionContext:PARAMETER_ARN" = local.backend_env_parameter_arn
        }
      }
    }]
  })
}

output "deployment_secret_kms_key_arn" {
  value = aws_kms_key.deployment_secrets.arn
}

output "backend_env_parameter_name" {
  value = local.backend_env_parameter_name
}
