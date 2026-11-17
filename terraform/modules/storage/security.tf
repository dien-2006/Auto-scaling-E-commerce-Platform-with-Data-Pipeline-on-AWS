
# Block all public access

resource "aws_s3_bucket_public_access_block" "main" {
  for_each = aws_s3_bucket.main

  bucket = each.value.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

# Default encryption using SSE-S3

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  for_each = aws_s3_bucket.main

  bucket = each.value.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Disable object ACLs and enforce bucket ownership

resource "aws_s3_bucket_ownership_controls" "main" {
  for_each = aws_s3_bucket.main

  bucket = each.value.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}
