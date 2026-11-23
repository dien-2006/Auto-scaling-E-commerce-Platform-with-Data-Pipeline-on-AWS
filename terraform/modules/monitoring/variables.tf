
variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "worker_asg_name" {
  description = "Kubernetes Worker ASG name"
  type        = string
}

variable "worker_min_size" {
  description = "Minimum Worker EC2 count"
  type        = number
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix for CloudWatch dimensions"
  type        = string
}

variable "web_target_group_arn_suffix" {
  description = "Public Next.js target group; backend service requests are observed by Prometheus."
  type        = string
}

variable "db_instance_identifier" {
  description = "RDS PostgreSQL identifier"
  type        = string
}

variable "rds_cpu_threshold" {
  type    = number
  default = 80
}

variable "alb_5xx_threshold" {
  type    = number
  default = 10
}

variable "backend_latency_threshold" {
  description = "Public web p95 latency threshold in seconds (legacy variable name retained)"
  type        = number
  default     = 2
}

variable "alarm_actions" {
  description = "SNS topic ARNs or other alarm action ARNs"
  type        = list(string)
  default     = []
}

variable "common_tags" {
  type    = map(string)
  default = {}
}
