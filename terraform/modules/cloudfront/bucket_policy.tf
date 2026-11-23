
data "aws_iam_policy_document" "cloudfront_read" {
  statement {
    sid    = "AllowCloudFrontReadImages"
    effect = "Allow"

    principals {
      type = "Service"

      identifiers = [
        "cloudfront.amazonaws.com"
      ]
    }

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${var.images_bucket_arn}/product-images/*",
      "${var.images_bucket_arn}/shop-logos/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"

      values = [
        aws_cloudfront_distribution.images.arn
      ]
    }
  }

  # Upload staging and any other prefixes remain inaccessible to CloudFront.
  # Exempt AWS service principals from transport conditions: their network
  # context can be redacted on service-to-service requests.
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = ["s3:*"]
    resources = [
      var.images_bucket_arn,
      "${var.images_bucket_arn}/*"
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }

    condition {
      test     = "Bool"
      variable = "aws:PrincipalIsAWSService"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "images" {
  bucket = var.images_bucket_name

  policy = data.aws_iam_policy_document.cloudfront_read.json
}
