
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${local.name_prefix}-infrastructure"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          title  = "Kubernetes Worker ASG"
          region = var.aws_region
          period = 60
          stat   = "Average"

          metrics = [
            [
              "AWS/AutoScaling",
              "GroupDesiredCapacity",
              "AutoScalingGroupName",
              var.worker_asg_name
            ],
            [
              "AWS/AutoScaling",
              "GroupInServiceInstances",
              "AutoScalingGroupName",
              var.worker_asg_name
            ]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          title  = "Backend HTTP 5xx"
          region = var.aws_region
          period = 60
          stat   = "Sum"

          metrics = [
            [
              "AWS/ApplicationELB",
              "HTTPCode_Target_5XX_Count",
              "LoadBalancer",
              var.alb_arn_suffix,
              "TargetGroup",
              var.backend_target_group_arn_suffix
            ]
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          title  = "Backend Response Time"
          region = var.aws_region
          period = 60
          stat   = "p95"

          metrics = [
            [
              "AWS/ApplicationELB",
              "TargetResponseTime",
              "LoadBalancer",
              var.alb_arn_suffix,
              "TargetGroup",
              var.backend_target_group_arn_suffix
            ]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6

        properties = {
          title  = "RDS PostgreSQL CPU"
          region = var.aws_region
          period = 60
          stat   = "Average"

          metrics = [
            [
              "AWS/RDS",
              "CPUUtilization",
              "DBInstanceIdentifier",
              var.db_instance_identifier
            ]
          ]
        }
      }
    ]
  })
}
