
variable "project_name" {
  description = "Project name, e.g. coco"
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

variable "aws_region" {
  type = string
}

# Network

variable "vpc_id" {
  type = string
}

variable "glue_subnet_id" {
  description = "Private subnet for Glue JDBC connection"
  type        = string
}

variable "rds_security_group_id" {
  type = string
}

# Database

variable "db_host" {
  description = "PostgreSQL hostname, without port"
  type        = string
}

variable "db_port" {
  type    = number
  default = 5432
}

variable "db_name" {
  type = string
}

variable "db_secret_arn" {
  description = "Secrets Manager ARN for PostgreSQL credentials"
  type        = string
}

# S3 Data Lake

variable "etl_bucket_name" {
  type = string
}

variable "etl_bucket_arn" {
  type = string
}

# Glue

variable "glue_version" {
  type    = string
  default = "5.0"
}

variable "worker_type" {
  type    = string
  default = "G.1X"
}

variable "number_of_workers" {
  type    = number
  default = 2

  validation {
    condition     = var.number_of_workers >= 2
    error_message = "Use at least 2 workers for G.1X Spark jobs."
  }
}

variable "job_timeout" {
  description = "Glue Job timeout in minutes"
  type        = number
  default     = 30
}

variable "common_tags" {
  type    = map(string)
  default = {}
}
