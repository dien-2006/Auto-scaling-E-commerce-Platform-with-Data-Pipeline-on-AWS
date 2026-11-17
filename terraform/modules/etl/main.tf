
locals {
  name_prefix = "${var.project_name}-${var.environment}"

  jdbc_url = (
    "jdbc:postgresql://${var.db_host}:${var.db_port}/${var.db_name}?sslmode=require"
  )

  extract_script_key   = "scripts/extract.py"
  transform_script_key = "scripts/transform.py"

  catalog_database_name = replace(
    "${var.project_name}_${var.environment}_analytics",
    "-",
    "_"
  )
}

data "aws_caller_identity" "current" {}

data "aws_subnet" "glue" {
  id = var.glue_subnet_id
}
