mock_provider "aws" {
  # Mocked computed strings are not JSON by default. The provider validates the
  # trust-policy JSON even though this test only exercises image permissions.
  mock_data "aws_iam_policy_document" {
    defaults = {
      json = jsonencode({
        Version = "2012-10-17"
        Statement = [{
          Effect    = "Allow"
          Action    = "sts:AssumeRole"
          Principal = { Service = "ec2.amazonaws.com" }
        }]
      })
    }
  }
}

run "image_permissions_are_scoped" {
  command = plan

  module {
    source = "../../modules/iam"
  }

  variables {
    project_name                = "ecommerce"
    environment                 = "dev"
    enable_image_storage_access = true
    images_bucket_arn           = "arn:aws:s3:::example-dev-images"
  }

  assert {
    condition = toset(jsondecode(aws_iam_role_policy.worker_images[0].policy).Statement[0].Action) == toset([
      "s3:GetObject", "s3:PutObject"
    ])
    error_message = "The image policy must only allow GetObject/PutObject, without extra baseline privileges."
  }

  assert {
    condition = toset(jsondecode(aws_iam_role_policy.worker_images[0].policy).Statement[0].Resource) == toset([
      "arn:aws:s3:::example-dev-images/uploads/*",
      "arn:aws:s3:::example-dev-images/product-images/*",
      "arn:aws:s3:::example-dev-images/shop-logos/*"
    ])
    error_message = "Image access must stay within the three prefixes in the configured image bucket."
  }

  assert {
    condition     = aws_iam_role_policy.worker_images[0].role == "ecommerce-dev-worker-role"
    error_message = "Only the worker role receives the image policy."
  }

  assert {
    condition = (
      length(jsondecode(aws_iam_role_policy.worker_images[0].policy).Statement) == 2 &&
      toset(jsondecode(aws_iam_role_policy.worker_images[0].policy).Statement[1].Action) == toset(["s3:GetObject"]) &&
      toset(jsondecode(aws_iam_role_policy.worker_images[0].policy).Statement[1].Resource) == toset([
        "arn:aws:s3:::example-dev-images/ProductImages/1-Lumi Beauty/*",
        "arn:aws:s3:::example-dev-images/ProductImages/2-Miora Lifestyle/*",
        "arn:aws:s3:::example-dev-images/ProductImages/3-Nuvia Care Store/*",
        "arn:aws:s3:::example-dev-images/logo/1.png",
        "arn:aws:s3:::example-dev-images/logo/2.png",
        "arn:aws:s3:::example-dev-images/logo/3.png"
      ])
    )
    error_message = "Imported catalog access must be read-only and limited to the three shops and logos."
  }
}

run "image_permissions_disabled_by_default" {
  command = plan

  module {
    source = "../../modules/iam"
  }

  variables {
    project_name = "ecommerce"
    environment  = "prod"
  }

  assert {
    condition     = length(aws_iam_role_policy.worker_images) == 0
    error_message = "Shared worker image access must be explicitly enabled."
  }
}
