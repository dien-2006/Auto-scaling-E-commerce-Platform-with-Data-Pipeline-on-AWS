# All providers are mocked: these checks do not create buckets, distributions or data.
mock_provider "aws" {
  mock_data "aws_caller_identity" {
    defaults = { account_id = "123456789012" }
  }
  mock_data "aws_region" {
    defaults = { region = "ap-southeast-1", name = "ap-southeast-1" }
  }
  mock_data "aws_iam_policy_document" {
    defaults = { json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}" }
  }
  mock_resource "aws_cloudfront_distribution" {
    defaults = { arn = "arn:aws:cloudfront::123456789012:distribution/EXAMPLE" }
  }
}

run "dev_presigned_post_uses_only_the_image_bucket" {
  command = apply
  module {
    source = "../../modules/storage"
  }
  variables {
    project_name         = "ecommerce"
    environment          = "dev"
    image_upload_origins = ["http://localhost:3001", "https://dev.example.com"]
  }

  assert {
    condition     = aws_s3_bucket_cors_configuration.images[0].bucket == aws_s3_bucket.main["images"].id
    error_message = "Image upload CORS must be attached to the image bucket, not the ETL bucket."
  }
  assert {
    condition = (
      toset(one(aws_s3_bucket_cors_configuration.images[0].cors_rule).allowed_methods) == toset(["POST", "GET", "HEAD"]) &&
      toset(one(aws_s3_bucket_cors_configuration.images[0].cors_rule).allowed_origins) == toset(["http://localhost:3001", "https://dev.example.com"])
    )
    error_message = "Presigned POST must work only for the explicitly configured browser origins."
  }
  assert {
    condition = (
      aws_s3_bucket_public_access_block.main["images"].block_public_acls &&
      aws_s3_bucket_public_access_block.main["images"].ignore_public_acls &&
      aws_s3_bucket_public_access_block.main["images"].block_public_policy &&
      aws_s3_bucket_public_access_block.main["images"].restrict_public_buckets
    )
    error_message = "Enabling browser CORS must not make the image bucket public."
  }
}

run "reject_wildcard_upload_origin" {
  command = plan
  module {
    source = "../../modules/storage"
  }
  variables {
    project_name         = "ecommerce"
    environment          = "dev"
    image_upload_origins = ["*"]
  }
  expect_failures = [var.image_upload_origins]
}

run "reject_upload_origin_with_path" {
  command = plan
  module {
    source = "../../modules/storage"
  }
  variables {
    project_name         = "ecommerce"
    environment          = "dev"
    image_upload_origins = ["https://dev.example.com/upload"]
  }
  expect_failures = [var.image_upload_origins]
}

run "reject_duplicate_upload_origins" {
  command = plan
  module {
    source = "../../modules/storage"
  }
  variables {
    project_name         = "ecommerce"
    environment          = "dev"
    image_upload_origins = ["http://localhost:3001", "http://localhost:3001"]
  }
  expect_failures = [var.image_upload_origins]
}

run "prod_rejects_plain_http_uploads" {
  command = plan
  module {
    source = "../../modules/storage"
  }
  variables {
    project_name         = "ecommerce"
    environment          = "prod"
    image_upload_origins = ["http://shop.example.com"]
  }
  expect_failures = [aws_s3_bucket_cors_configuration.images]
}

run "cdn_reads_only_verified_product_images_and_logos" {
  command = apply
  module {
    source = "../../modules/cloudfront"
  }
  variables {
    project_name              = "ecommerce"
    environment               = "dev"
    images_bucket_name        = "example-dev-images"
    images_bucket_arn         = "arn:aws:s3:::example-dev-images"
    images_bucket_domain_name = "example-dev-images.s3.ap-southeast-1.amazonaws.com"
  }

  # Inspect configured document inputs. The provider's JSON rendering is mocked;
  # this does not claim to validate a live IAM policy or live CDN behavior.
  assert {
    condition = toset(one([
      for statement in data.aws_iam_policy_document.cloudfront_read.statement : statement
      if statement.sid == "AllowCloudFrontReadImages"
    ]).resources) == toset([
      "arn:aws:s3:::example-dev-images/product-images/*",
      "arn:aws:s3:::example-dev-images/shop-logos/*"
    ])
    error_message = "CloudFront must not be granted access to staging uploads or the entire bucket."
  }
  assert {
    condition = anytrue([
      for statement in data.aws_iam_policy_document.cloudfront_read.statement :
      statement.sid == "AllowCloudFrontReadImages" && anytrue([
        for condition in statement.condition :
        condition.variable == "AWS:SourceArn" && contains(condition.values, aws_cloudfront_distribution.images.arn)
      ])
    ])
    error_message = "Image delivery must be restricted to this specific CloudFront distribution."
  }
  assert {
    condition     = aws_cloudfront_distribution.images.default_cache_behavior[0].response_headers_policy_id == "67f7725c-6f97-4210-82d7-5512b31e9d03"
    error_message = "The CDN must add the managed security response headers."
  }
  assert {
    condition = anytrue([
      for statement in data.aws_iam_policy_document.cloudfront_read.statement :
      statement.sid == "DenyInsecureTransport" && statement.effect == "Deny" &&
      anytrue([
        for condition in statement.condition :
        condition.variable == "aws:SecureTransport" && contains(condition.values, "false")
      ]) && anytrue([
        for condition in statement.condition :
        condition.variable == "aws:PrincipalIsAWSService" && contains(condition.values, "false")
      ])
    ])
    error_message = "The transport guard must deny plain HTTP without blocking AWS service principals."
  }
}
