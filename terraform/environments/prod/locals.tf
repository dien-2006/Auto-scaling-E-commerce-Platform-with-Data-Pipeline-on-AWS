
locals {
  project_name = "ecommerce"
  environment  = "prod"

  name_prefix = "${local.project_name}-${local.environment}"

  common_tags = {
    Project     = local.project_name
    Environment = local.environment
    ManagedBy   = "Terraform"
  }
}
