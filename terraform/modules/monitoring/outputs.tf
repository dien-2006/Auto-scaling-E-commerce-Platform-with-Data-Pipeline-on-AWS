
output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "log_group_name" {
  description = "Infrastructure log group"
  value       = aws_cloudwatch_log_group.infrastructure.name
}

output "alarm_arns" {
  description = "CloudWatch alarm ARNs"

  value = {
    worker_capacity = aws_cloudwatch_metric_alarm.worker_capacity.arn
    backend_5xx     = aws_cloudwatch_metric_alarm.backend_5xx.arn
    backend_latency = aws_cloudwatch_metric_alarm.backend_latency.arn
    rds_cpu         = aws_cloudwatch_metric_alarm.rds_cpu.arn
  }
}
