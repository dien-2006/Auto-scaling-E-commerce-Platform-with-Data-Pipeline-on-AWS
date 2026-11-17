# Glue Extract Job
resource "aws_glue_job" "extract" {
  name        = "${local.name_prefix}-extract"
  description = "Extract PostgreSQL data into S3 Raw"

  role_arn = aws_iam_role.extract.arn

  glue_version      = var.glue_version
  worker_type       = var.worker_type
  number_of_workers = var.number_of_workers

  timeout         = var.job_timeout
  max_retries     = 0
  execution_class = "STANDARD"

  connections = [
    aws_glue_connection.postgresql.name
  ]

  execution_property {
    max_concurrent_runs = 1
  }

  command {
    name           = "glueetl"
    python_version = "3"

    script_location = "s3://${var.etl_bucket_name}/${local.extract_script_key}"
  }

  default_arguments = {
    "--job-language"        = "python"
    "--enable-metrics"      = "true"
    "--enable-job-insights" = "true"
    "--job-bookmark-option" = "job-bookmark-disable"

    "--AWS_REGION"    = var.aws_region
    "--JDBC_URL"      = local.jdbc_url
    "--DB_SECRET_ARN" = var.db_secret_arn
    "--S3_BUCKET"     = var.etl_bucket_name
    "--RAW_PREFIX"    = "raw/"
  }

  tags = var.common_tags

  depends_on = [
    aws_iam_role_policy_attachment.extract_service,
    aws_iam_role_policy.extract_data
  ]
}

# Glue Transform Job

resource "aws_glue_job" "transform" {
  name        = "${local.name_prefix}-transform"
  description = "Transform S3 Raw into Silver and Gold"

  role_arn = aws_iam_role.transform.arn

  glue_version      = var.glue_version
  worker_type       = var.worker_type
  number_of_workers = var.number_of_workers

  timeout         = var.job_timeout
  max_retries     = 0
  execution_class = "STANDARD"

  execution_property {
    max_concurrent_runs = 1
  }

  command {
    name           = "glueetl"
    python_version = "3"

    script_location = "s3://${var.etl_bucket_name}/${local.transform_script_key}"
  }

  default_arguments = {
    "--job-language"        = "python"
    "--enable-metrics"      = "true"
    "--enable-job-insights" = "true"
    "--job-bookmark-option" = "job-bookmark-disable"

    "--S3_BUCKET"     = var.etl_bucket_name
    "--RAW_PREFIX"    = "raw/"
    "--SILVER_PREFIX" = "silver/"
    "--GOLD_PREFIX"   = "gold/"
  }

  tags = var.common_tags

  depends_on = [
    aws_iam_role_policy_attachment.transform_service,
    aws_iam_role_policy.transform_data
  ]
}
