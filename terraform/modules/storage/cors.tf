# Browser -> S3 presigned POST. CORS does not grant S3 permissions.
# Manage one CORS resource per bucket; do not apply to the ETL bucket.
resource "aws_s3_bucket_cors_configuration" "images" {
  count = length(var.image_upload_origins) > 0 ? 1 : 0

  bucket = aws_s3_bucket.main["images"].id

  cors_rule {
    id              = "browser-image-upload"
    allowed_origins = var.image_upload_origins
    allowed_methods = ["POST", "GET", "HEAD"]
    allowed_headers = ["content-type"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }

  lifecycle {
    precondition {
      condition = var.environment != "prod" || alltrue([
        for origin in var.image_upload_origins : startswith(origin, "https://")
      ])
      error_message = "Production image upload origins must use HTTPS."
    }
  }
}
