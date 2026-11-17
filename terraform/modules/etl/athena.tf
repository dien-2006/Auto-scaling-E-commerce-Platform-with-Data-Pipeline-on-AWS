
resource "aws_athena_workgroup" "analytics" {
  name = "${local.name_prefix}-analytics"

  description = "Athena workgroup for COCO analytics"

  state         = "ENABLED"
  force_destroy = false

  configuration {
    enforce_workgroup_configuration = true

    publish_cloudwatch_metrics_enabled = true

    bytes_scanned_cutoff_per_query = 1073741824

    result_configuration {
      output_location = "s3://${var.etl_bucket_name}/athena-results/"

      expected_bucket_owner = data.aws_caller_identity.current.account_id

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }

  tags = var.common_tags
}
