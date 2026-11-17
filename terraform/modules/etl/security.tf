
resource "aws_security_group" "glue" {
  name        = "${local.name_prefix}-glue-sg"
  description = "Security group for AWS Glue jobs"
  vpc_id      = var.vpc_id

  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-glue-sg"
  })
}

# Allow Spark components to communicate with each other
resource "aws_vpc_security_group_ingress_rule" "self_tcp" {
  security_group_id = aws_security_group.glue.id

  referenced_security_group_id = aws_security_group.glue.id

  ip_protocol = "tcp"
  from_port   = 0
  to_port     = 65535

  description = "Glue Spark internal communication"
}

# Allow outbound traffic from Glue
resource "aws_vpc_security_group_egress_rule" "outbound" {
  security_group_id = aws_security_group.glue.id

  ip_protocol = "-1"
  cidr_ipv4   = "0.0.0.0/0"

  description = "Glue outbound access"
}

# Allow Glue to connect to PostgreSQL
resource "aws_vpc_security_group_ingress_rule" "rds_from_glue" {
  security_group_id = var.rds_security_group_id

  referenced_security_group_id = aws_security_group.glue.id

  ip_protocol = "tcp"
  from_port   = var.db_port
  to_port     = var.db_port

  description = "PostgreSQL access from AWS Glue"
}
