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
output "etl_extract_job_name" {
  value = module.etl.extract_job_name
}

output "etl_transform_job_name" {
  value = module.etl.transform_job_name
}

output "etl_glue_connection" {
  value = module.etl.glue_connection_name
}

output "etl_catalog_database" {
  value = module.etl.catalog_database_name
}

output "etl_athena_workgroup" {
  value = module.etl.athena_workgroup_name
}

output "etl_script_locations" {
  value = module.etl.script_locations
}
