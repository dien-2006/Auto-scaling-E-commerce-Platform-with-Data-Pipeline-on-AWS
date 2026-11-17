
resource "aws_autoscaling_attachment" "frontend" {
  autoscaling_group_name = var.worker_asg_name

  lb_target_group_arn = aws_lb_target_group.frontend.arn
}

resource "aws_autoscaling_attachment" "backend" {
  autoscaling_group_name = var.worker_asg_name

  lb_target_group_arn = aws_lb_target_group.backend.arn
}
