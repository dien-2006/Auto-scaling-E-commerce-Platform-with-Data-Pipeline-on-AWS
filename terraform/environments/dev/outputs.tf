output "vpc_id" {
  value = module.network.vpc_id
}

output "public_subnet_ids" {
  value = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  value = module.network.private_subnet_ids
}

output "nat_gateway_ids" {
  value = module.network.nat_gateway_ids
}
output "alb_dns_name" {
  value = module.alb.alb_dns_name
}
output "kubernetes_control_plane_ip" {
  value = module.kubernetes.control_plane_private_ip
}

output "kubernetes_worker_asg" {
  value = module.kubernetes.worker_asg_name
}


output "rds_endpoint" {
  description = "PostgreSQL hostname"
  value       = module.database.db_address
}

output "rds_port" {
  description = "PostgreSQL port"
  value       = module.database.db_port
}

output "rds_database_name" {
  description = "Database name"
  value       = module.database.db_name
}

output "rds_master_secret_arn" {
  description = "Master credentials secret ARN"
  value       = module.database.db_master_secret_arn
}

output "images_bucket_name" {
  value = module.storage.images_bucket_name
}

output "images_bucket_region" {
  value = var.aws_region
}

output "image_prefixes" {
  value = module.storage.image_prefixes
}

output "image_upload_origins" {
  value = module.storage.image_upload_origins
}

output "etl_bucket_name" {
  value = module.storage.etl_bucket_name
}

output "etl_config" {
  description = "Non-secret ETL settings consumed by the owner-run dev scripts"
  value = {
    COCO_ENV           = local.environment
    AWS_REGION         = var.aws_region
    AWS_ACCOUNT_ID     = module.etl.aws_account_id
    ETL_BUCKET         = module.etl.etl_bucket_name
    GLUE_EXTRACT_JOB   = module.etl.extract_job_name
    GLUE_TRANSFORM_JOB = module.etl.transform_job_name
    GLUE_WORKFLOW      = "${local.project_name}-${local.environment}-pipeline"
    ATHENA_DATABASE    = module.etl.catalog_database_name
    ATHENA_WORKGROUP   = module.etl.athena_workgroup_name
    GLUE_SCHEDULE      = "cron(0 18 * * ? *)" # 01:00 Asia/Ho_Chi_Minh the following day
  }
}
output "ecr_frontend_url" {
  value = module.ecr.frontend_repository_url
}

output "ecr_backend_url" {
  value = module.ecr.backend_repository_url
}
output "cloudfront_images_url" {
  value = module.cloudfront.base_url
}
output "cloudwatch_dashboard_name" {
  value = module.monitoring.dashboard_name
}


# Backwards-compatible aliases for callers using these output names.
output "db_address" {
  value = module.database.db_address
}
output "db_port" {
  value = module.database.db_port
}
output "db_name" {
  value = module.database.db_name
}
output "db_master_secret_arn" {
  value = module.database.db_master_secret_arn
}
