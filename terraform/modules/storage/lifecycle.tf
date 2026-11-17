
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  for_each = aws_s3_bucket.main

  bucket = each.value.id

  # Abort incomplete multipart uploads
  rule {
    id     = "abort-incomplete-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  # Remove old noncurrent object versions
  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_days
    }
  }

  # Only for ETL bucket
  dynamic "rule" {
    for_each = each.key == "etl" ? [1] : []

    content {
      id     = "expire-temporary-data"
      status = "Enabled"

      filter {
        prefix = "tmp/"
      }

      expiration {
        days = 7
      }
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.main
  ]
}
