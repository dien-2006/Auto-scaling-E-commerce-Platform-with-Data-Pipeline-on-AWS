
resource "aws_db_instance" "postgresql" {
  identifier = "${local.name_prefix}-postgresql"

  # Database engine
  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.db_instance_class

  # Initial database
  db_name  = var.db_name
  username = var.db_username
  port     = 5432

  # Password management
  manage_master_user_password = true

  # Storage
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  # Networking
  db_subnet_group_name = aws_db_subnet_group.main.name

  vpc_security_group_ids = [
    var.rds_sg_id
  ]

  publicly_accessible = false

  # High availability
  multi_az = var.multi_az

  # Automated backups
  backup_retention_period = var.backup_retention_period
  backup_window           = "03:00-04:00"

  # Maintenance
  maintenance_window         = "sun:05:00-sun:06:00"
  auto_minor_version_upgrade = false
  apply_immediately          = var.apply_immediately

  # Deletion safety
  deletion_protection = var.deletion_protection

  skip_final_snapshot = var.skip_final_snapshot

  final_snapshot_identifier = (
    var.skip_final_snapshot
    ? null
    : "${local.name_prefix}-postgresql-final"
  )

  # Monitoring
  monitoring_interval = 0

  # Resource tags
  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-postgresql"
  })

  lifecycle {
    precondition {
      condition = (
        var.max_allocated_storage == 0 ||
        var.max_allocated_storage >= var.allocated_storage
      )
      error_message = "Maximum storage must be >= allocated storage."
    }

    precondition {
      condition = (
        var.environment != "prod" ||
        (
          var.deletion_protection &&
          !var.skip_final_snapshot &&
          var.backup_retention_period >= 1
        )
      )
      error_message = "Prod requires deletion protection, final snapshot and backups."
    }
  }
}
