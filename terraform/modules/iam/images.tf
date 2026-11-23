# Refined from the IAM Policy Autopilot baseline supplied by the owner.
# Current bucket: SSE-S3, BucketOwnerEnforced; no KMS, ACL, tagging, or Object Lock calls.
# This is shared node access for dev, not an isolated Kubernetes workload identity.
resource "aws_iam_role_policy" "worker_images" {
  count = var.enable_image_storage_access ? 1 : 0

  name = "${local.name_prefix}-worker-images"
  role = aws_iam_role.worker.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "ReadWriteApplicationImageObjects"
      Effect = "Allow"
      Action = ["s3:GetObject", "s3:PutObject"]
      Resource = [
        "${var.images_bucket_arn}/uploads/*",
        "${var.images_bucket_arn}/product-images/*",
        "${var.images_bucket_arn}/shop-logos/*"
      ]
    }, {
      Sid    = "ReadOnlyImportedCatalog"
      Effect = "Allow"
      Action = ["s3:GetObject"]
      Resource = [
        "${var.images_bucket_arn}/ProductImages/1-Lumi Beauty/*",
        "${var.images_bucket_arn}/ProductImages/2-Miora Lifestyle/*",
        "${var.images_bucket_arn}/ProductImages/3-Nuvia Care Store/*",
        "${var.images_bucket_arn}/logo/1.png",
        "${var.images_bucket_arn}/logo/2.png",
        "${var.images_bucket_arn}/logo/3.png"
      ]
    }]
  })

  lifecycle {
    precondition {
      condition     = var.images_bucket_arn != null
      error_message = "Worker image access requires images_bucket_arn."
    }
  }
}
