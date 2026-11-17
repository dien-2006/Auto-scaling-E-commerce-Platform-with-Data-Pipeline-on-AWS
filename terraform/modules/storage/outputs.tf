
output "images_bucket_name" {
  description = "S3 bucket for product images"
  value       = aws_s3_bucket.main["images"].bucket
}

output "images_bucket_arn" {
  description = "Product images bucket ARN"
  value       = aws_s3_bucket.main["images"].arn
}

output "images_bucket_regional_domain_name" {
  description = "Regional domain for CloudFront origin"
  value       = aws_s3_bucket.main["images"].bucket_regional_domain_name
}

output "etl_bucket_name" {
  description = "S3 bucket for ETL data"
  value       = aws_s3_bucket.main["etl"].bucket
}

output "etl_bucket_arn" {
  description = "ETL data bucket ARN"
  value       = aws_s3_bucket.main["etl"].arn
}

output "etl_prefixes" {
  description = "Logical prefixes for the data pipeline"

  value = {
    raw            = "raw/"
    silver         = "silver/"
    gold           = "gold/"
    temporary      = "tmp/"
    athena_results = "athena-results/"
  }
}
