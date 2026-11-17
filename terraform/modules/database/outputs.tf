
output "db_instance_id" {
  description = "RDS instance identifier"
  value       = aws_db_instance.postgresql.identifier
}

output "db_instance_arn" {
  description = "RDS instance ARN"
  value       = aws_db_instance.postgresql.arn
}

output "db_address" {
  description = "RDS hostname without port"
  value       = aws_db_instance.postgresql.address
}

output "db_port" {
  description = "PostgreSQL port"
  value       = aws_db_instance.postgresql.port
}

output "db_name" {
  description = "Initial PostgreSQL database"
  value       = aws_db_instance.postgresql.db_name
}

output "db_username" {
  description = "Master database username"
  value       = aws_db_instance.postgresql.username
}

output "db_subnet_group_name" {
  description = "Database subnet group"
  value       = aws_db_subnet_group.main.name
}

output "db_master_secret_arn" {
  description = "RDS managed master secret ARN"

  value = (
    aws_db_instance.postgresql.master_user_secret[0].secret_arn
  )
}
