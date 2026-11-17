
resource "aws_glue_catalog_database" "analytics" {
  name = local.catalog_database_name

  description = "COCO analytics metadata catalog"

  location_uri = "s3://${var.etl_bucket_name}/gold/"

  tags = var.common_tags
}
