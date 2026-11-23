
variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs across two AZs"
  type        = list(string)
}

variable "alb_sg_id" {
  description = "ALB security group ID"
  type        = string
}

variable "worker_asg_name" {
  description = "Kubernetes Worker ASG name"
  type        = string
}

variable "frontend_node_port" {
  description = "Frontend NodePort"
  type        = number
  default     = 30080
}

variable "backend_node_port" {
  description = "Backend NodePort"
  type        = number
  default     = 30081
}

variable "frontend_health_path" {
  description = "Frontend health check path"
  type        = string
  default     = "/health/live"
}

variable "backend_health_path" {
  description = "Backend health check path"
  type        = string
  default     = "/health/ready"
}

variable "enable_https" {
  description = "Enable HTTPS listener"
  type        = bool
  default     = false
}

variable "certificate_arn" {
  description = "ACM certificate ARN"
  type        = string
  default     = null
}

variable "common_tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
