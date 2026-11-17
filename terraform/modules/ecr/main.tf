
locals {
  name_prefix = "${var.project_name}/${var.environment}"

  repositories = toset([
    "frontend",
    "backend"
  ])
}

resource "aws_ecr_repository" "main" {
  for_each = local.repositories

  name = "${local.name_prefix}/${each.key}"

  image_tag_mutability = var.image_tag_mutability

  image_scanning_configuration {
    scan_on_push = var.scan_on_push
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  force_delete = false

  tags = merge(var.common_tags, {
    Name        = "${var.project_name}-${var.environment}-${each.key}"
    Application = each.key
  })
}
