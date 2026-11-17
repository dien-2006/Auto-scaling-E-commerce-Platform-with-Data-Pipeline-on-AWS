
variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment: dev or prod"
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be dev or prod."
  }
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for DB subnet group"
  type        = list(string)

  validation {
    condition     = length(var.private_subnet_ids) >= 2
    error_message = "At least two subnets are required."
  }
}

variable "rds_sg_id" {
  description = "RDS Security Group ID"
  type        = string
}

variable "db_name" {
  description = "Initial PostgreSQL database name"
  type        = string
  default     = "coco_marketplace"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "coco_admin"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.small"
}

variable "engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = null
}

variable "allocated_storage" {
  description = "Initial storage size in GiB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum storage size in GiB"
  type        = number
  default     = 100
}

variable "multi_az" {
  description = "Enable Multi-AZ"
  type        = bool
  default     = false
}

variable "backup_retention_period" {
  description = "Automated backup retention in days"
  type        = number
  default     = 1
}

variable "deletion_protection" {
  description = "Prevent accidental DB deletion"
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot on deletion"
  type        = bool
  default     = true
}

variable "apply_immediately" {
  description = "Apply RDS modifications immediately"
  type        = bool
  default     = false
}

variable "common_tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
