
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
      "${var.images_bucket_arn}/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"

      values = [
        aws_cloudfront_distribution.images.arn
      ]
    }
  }
}

resource "aws_s3_bucket_policy" "images" {
  bucket = var.images_bucket_name

  policy = data.aws_iam_policy_document.cloudfront_read.json
}
