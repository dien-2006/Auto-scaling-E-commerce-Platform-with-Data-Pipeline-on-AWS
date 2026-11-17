locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

resource "aws_cloudwatch_log_group" "infrastructure" {
  name              = "/${var.project_name}/${var.environment}/infrastructure"
  retention_in_days = var.environment == "prod" ? 30 : 7
  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-infrastructure-logs"
  })
}
