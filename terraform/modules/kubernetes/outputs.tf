
output "cluster_name" {
  value = var.cluster_name
}

output "control_plane_instance_id" {
  value = aws_instance.control_plane.id
}

output "control_plane_private_ip" {
  value = aws_instance.control_plane.private_ip
}

output "worker_asg_name" {
  value = aws_autoscaling_group.worker.name
}

output "worker_launch_template_id" {
  value = aws_launch_template.worker.id
}

output "worker_bootstrap_base64" {
  description = "Current source bootstrap; evaluated with terraform console, not an old applied user_data attribute"
  value       = local.worker_user_data_base64
}

output "join_parameter_name" {
  value = local.join_parameter_name
}

output "worker_capacity" {
  value = {
    minimum = aws_autoscaling_group.worker.min_size
    initial = var.worker_desired_capacity
    maximum = aws_autoscaling_group.worker.max_size
  }
}
