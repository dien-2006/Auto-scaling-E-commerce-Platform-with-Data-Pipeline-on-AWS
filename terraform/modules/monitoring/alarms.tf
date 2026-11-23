
# 1. Worker EC2 below minimum

resource "aws_cloudwatch_metric_alarm" "worker_capacity" {
  alarm_name        = "${local.name_prefix}-worker-capacity-low"
  alarm_description = "Worker instances below expected minimum"

  namespace   = "AWS/AutoScaling"
  metric_name = "GroupInServiceInstances"

  statistic          = "Minimum"
  period             = 60
  evaluation_periods = 3

  comparison_operator = "LessThanThreshold"
  threshold           = var.worker_min_size

  dimensions = {
    AutoScalingGroupName = var.worker_asg_name
  }

  treat_missing_data = "missing"
  alarm_actions      = var.alarm_actions

  tags = var.common_tags
}

# 2. Public web HTTP 5xx errors (legacy Terraform/AWS alarm names retained).

resource "aws_cloudwatch_metric_alarm" "backend_5xx" {
  alarm_name        = "${local.name_prefix}-backend-5xx"
  alarm_description = "Public web target returns too many HTTP 5xx responses"

  namespace   = "AWS/ApplicationELB"
  metric_name = "HTTPCode_Target_5XX_Count"

  statistic          = "Sum"
  period             = 300
  evaluation_periods = 2

  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = var.alb_5xx_threshold

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = var.web_target_group_arn_suffix
  }

  treat_missing_data = "notBreaching"
  alarm_actions      = var.alarm_actions

  tags = var.common_tags
}

# 3. Public web p95 latency; FastAPI request latency is measured by Prometheus.

resource "aws_cloudwatch_metric_alarm" "backend_latency" {
  alarm_name        = "${local.name_prefix}-backend-latency-high"
  alarm_description = "Public web target p95 response time too high"

  namespace   = "AWS/ApplicationELB"
  metric_name = "TargetResponseTime"

  extended_statistic = "p95"
  period             = 300
  evaluation_periods = 2

  comparison_operator = "GreaterThanThreshold"
  threshold           = var.backend_latency_threshold

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = var.web_target_group_arn_suffix
  }

  evaluate_low_sample_count_percentiles = "ignore"
  treat_missing_data                    = "notBreaching"
  alarm_actions                         = var.alarm_actions

  tags = var.common_tags
}

# 4. RDS high CPU

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name        = "${local.name_prefix}-rds-cpu-high"
  alarm_description = "RDS PostgreSQL CPU utilization too high"

  namespace   = "AWS/RDS"
  metric_name = "CPUUtilization"

  statistic          = "Average"
  period             = 300
  evaluation_periods = 3

  comparison_operator = "GreaterThanThreshold"
  threshold           = var.rds_cpu_threshold

  dimensions = {
    DBInstanceIdentifier = var.db_instance_identifier
  }

  treat_missing_data = "missing"
  alarm_actions      = var.alarm_actions

  tags = var.common_tags
}
