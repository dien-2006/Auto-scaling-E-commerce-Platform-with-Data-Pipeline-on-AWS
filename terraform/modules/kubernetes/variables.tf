
variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "cluster_name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "control_plane_sg_id" {
  type = string
}

variable "worker_sg_id" {
  type = string
}

variable "control_plane_instance_profile_name" {
  type = string
}

variable "worker_instance_profile_name" {
  type = string
}

variable "control_plane_role_name" {
  type = string
}

variable "worker_role_name" {
  type = string
}

variable "control_plane_instance_type" {
  type    = string
  default = "t3.medium"
}

variable "worker_instance_type" {
  type    = string
  default = "t3.medium"
}

variable "worker_min_size" {
  type    = number
  default = 1
}

variable "worker_desired_capacity" {
  type    = number
  default = 2
}

variable "worker_max_size" {
  type    = number
  default = 4
}

variable "kubernetes_minor_version" {
  description = "Kubernetes package minor version"
  type        = string
  default     = "1.34"
}

variable "pod_cidr" {
  type    = string
  default = "10.244.0.0/16"
}

variable "root_volume_size" {
  type    = number
  default = 30
}

variable "common_tags" {
  type    = map(string)
  default = {}
}
