
locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

resource "aws_lb" "main" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    var.alb_sg_id
  ]

  subnets = var.public_subnet_ids

  enable_deletion_protection = var.environment == "prod"

  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-alb"
  })

  lifecycle {
    precondition {
      condition = (
        !var.enable_https ||
        (
          var.certificate_arn != null &&
          try(length(trimspace(var.certificate_arn)) > 0, false)
        )
      )
      error_message = "HTTPS requires a valid ACM certificate ARN."
    }
  }
}
