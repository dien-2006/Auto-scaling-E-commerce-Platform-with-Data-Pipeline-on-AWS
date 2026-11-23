mock_provider "aws" {
  mock_resource "aws_lb" {
    defaults = { arn = "arn:aws:elasticloadbalancing:ap-southeast-1:123456789012:loadbalancer/app/test/0000000000000000" }
  }
  mock_resource "aws_lb_target_group" {
    defaults = { arn = "arn:aws:elasticloadbalancing:ap-southeast-1:123456789012:targetgroup/backend/0000000000000000" }
  }
  mock_resource "aws_lb_listener" {
    defaults = { arn = "arn:aws:elasticloadbalancing:ap-southeast-1:123456789012:listener/app/test/0000000000000000/0000000000000000" }
  }
}

variables {
  project_name      = "ecommerce"
  environment       = "dev"
  vpc_id            = "vpc-0123456789abcdef0"
  public_subnet_ids = ["subnet-0123456789abcdef0", "subnet-0123456789abcdef1"]
  alb_sg_id         = "sg-0123456789abcdef0"
  worker_asg_name   = "ecommerce-dev-worker-asg"
}

run "browser_api_uses_next_http" {
  command = apply
  module {
    source = "../../modules/alb"
  }
  override_resource {
    target = aws_lb_target_group.frontend
    values = { arn = "arn:aws:elasticloadbalancing:ap-southeast-1:123456789012:targetgroup/frontend/0000000000000001" }
  }
  assert {
    condition = (
      aws_lb_target_group.frontend.arn != aws_lb_target_group.backend.arn &&
      one(aws_lb_listener_rule.backend_http[0].action).target_group_arn == aws_lb_target_group.frontend.arn
    )
    error_message = "Browser API traffic must reach Next.js rather than bypass the proxy."
  }
}

run "browser_api_uses_next_https" {
  command = apply
  module {
    source = "../../modules/alb"
  }
  variables {
    enable_https    = true
    certificate_arn = "arn:aws:acm:ap-southeast-1:123456789012:certificate/00000000-0000-0000-0000-000000000000"
  }
  override_resource {
    target = aws_lb_target_group.frontend
    values = { arn = "arn:aws:elasticloadbalancing:ap-southeast-1:123456789012:targetgroup/frontend/0000000000000001" }
  }
  assert {
    condition = (
      aws_lb_target_group.frontend.arn != aws_lb_target_group.backend.arn &&
      one(aws_lb_listener_rule.backend_https[0].action).target_group_arn == aws_lb_target_group.frontend.arn
    )
    error_message = "HTTPS browser API traffic must also reach Next.js."
  }
}
