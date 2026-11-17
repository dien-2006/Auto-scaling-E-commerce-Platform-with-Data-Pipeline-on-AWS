
locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

resource "aws_db_subnet_group" "main" {
  name = "${local.name_prefix}-db-subnet-group"

  description = "Private subnets for COCO PostgreSQL"

  subnet_ids = var.private_subnet_ids

  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-db-subnet-group"
  })
}
