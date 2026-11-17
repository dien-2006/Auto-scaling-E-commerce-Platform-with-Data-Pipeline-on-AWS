
output "alb_sg_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

output "control_plane_sg_id" {
  description = "Kubernetes control plane SG ID"
  value       = aws_security_group.control_plane.id
}

output "worker_sg_id" {
  description = "Kubernetes worker SG ID"
  value       = aws_security_group.worker.id
}

output "rds_sg_id" {
  description = "RDS PostgreSQL SG ID"
  value       = aws_security_group.rds.id
}
