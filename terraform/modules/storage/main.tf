
data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  buckets = {
    images = "product-images"
    etl    = "data-lake"
  }
}

resource "aws_s3_bucket" "main" {
  for_each = local.buckets

  bucket = lower(
    "${local.name_prefix}-${each.value}-${data.aws_caller_identity.current.account_id}-${data.aws_region.current.region}"
  )

  force_destroy = false

  tags = merge(var.common_tags, {
    Name    = "${local.name_prefix}-${each.value}"
    Purpose = each.key
  })
}
