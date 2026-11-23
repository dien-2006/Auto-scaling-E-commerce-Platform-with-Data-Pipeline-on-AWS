
output "glue_security_group_id" {
  value = aws_security_group.glue.id
}

output "glue_connection_name" {
  value = aws_glue_connection.postgresql.name
}

output "extract_job_name" {
  value = aws_glue_job.extract.name
}

output "transform_job_name" {
  value = aws_glue_job.transform.name
}

output "extract_role_arn" {
  value = aws_iam_role.extract.arn
}

output "transform_role_arn" {
  value = aws_iam_role.transform.arn
}

output "catalog_database_name" {
  value = aws_glue_catalog_database.analytics.name
}

output "athena_workgroup_name" {
  value = aws_athena_workgroup.analytics.name
}

output "etl_bucket_name" {
  value = var.etl_bucket_name
}

output "aws_account_id" {
  value = data.aws_caller_identity.current.account_id
}

output "script_locations" {
  value = {
    extract   = "s3://${var.etl_bucket_name}/${local.extract_script_key}"
    transform = "s3://${var.etl_bucket_name}/${local.transform_script_key}"
  }
}
