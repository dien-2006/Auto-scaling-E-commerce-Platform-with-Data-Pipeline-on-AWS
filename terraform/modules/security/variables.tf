
variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID from network module"
  type        = string
}

variable "frontend_node_port" {
  description = "Frontend Kubernetes NodePort"
  type        = number
  default     = 30080
}

variable "backend_node_port" {
  description = "Backend Kubernetes NodePort"
  type        = number
  default     = 30081
}

variable "common_tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}
