
resource "aws_glue_connection" "postgresql" {
  name = "${local.name_prefix}-postgresql-jdbc"

  connection_type = "JDBC"

  connection_properties = {
    JDBC_CONNECTION_URL = local.jdbc_url
    SECRET_ID           = var.db_secret_arn
    JDBC_ENFORCE_SSL    = "true"
  }

  physical_connection_requirements {
    availability_zone = data.aws_subnet.glue.availability_zone

    subnet_id = var.glue_subnet_id

    security_group_id_list = [
      aws_security_group.glue.id
    ]
  }

  tags = var.common_tags

  depends_on = [
    aws_vpc_security_group_ingress_rule.self_tcp,
    aws_vpc_security_group_ingress_rule.rds_from_glue
  ]
}
