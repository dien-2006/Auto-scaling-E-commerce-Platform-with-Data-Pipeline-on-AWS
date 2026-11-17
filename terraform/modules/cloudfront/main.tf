
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  origin_id   = "${local.name_prefix}-images-origin"
}

resource "aws_cloudfront_origin_access_control" "images" {
  name = "${local.name_prefix}-images-oac"

  description = "OAC for COCO product images"

  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "images" {
  enabled         = true
  is_ipv6_enabled = true

  comment     = "${local.name_prefix} product images"
  price_class = var.price_class

  origin {
    domain_name = var.images_bucket_domain_name
    origin_id   = local.origin_id

    origin_access_control_id = aws_cloudfront_origin_access_control.images.id
  }

  default_cache_behavior {
    target_origin_id = local.origin_id

    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = [
      "GET",
      "HEAD"
    ]

    cached_methods = [
      "GET",
      "HEAD"
    ]

    compress = true

    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-images-cdn"
  })
}
