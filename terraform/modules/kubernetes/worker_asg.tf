
resource "aws_autoscaling_group" "worker" {
  name = "${local.name_prefix}-worker-asg"

  min_size         = var.worker_min_size
  desired_capacity = var.worker_desired_capacity
  max_size         = var.worker_max_size

  vpc_zone_identifier = var.private_subnet_ids

  health_check_type         = "EC2"
  health_check_grace_period = 600

  launch_template {
    id      = aws_launch_template.worker.id
    version = aws_launch_template.worker.latest_version
  }

  tag {
    key                 = "Name"
    value               = "${local.name_prefix}-worker"
    propagate_at_launch = true
  }

  tag {
    key                 = "k8s.io/cluster-autoscaler/enabled"
    value               = "true"
    propagate_at_launch = true
  }

  tag {
    key                 = "k8s.io/cluster-autoscaler/${var.cluster_name}"
    value               = "owned"
    propagate_at_launch = true
  }

  lifecycle {
    ignore_changes = [desired_capacity]
  }
  enabled_metrics = [
    "GroupDesiredCapacity",
    "GroupInServiceInstances",
    "GroupTotalInstances"
  ]

  metrics_granularity = "1Minute"

  depends_on = [
    aws_instance.control_plane,
    aws_iam_role_policy.control_plane_bootstrap,
    aws_iam_role_policy.worker_bootstrap
  ]
}
