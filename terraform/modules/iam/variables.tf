
variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be dev or prod."
  }
}

variable "common_tags" {
  description = "Common tags for IAM resources"
  type        = map(string)
  default     = {}
}

variable "enable_image_storage_access" {
  description = "Grant shared worker-node image access; enable deliberately for dev, not per-Pod isolation."
  type        = bool
  default     = false
}

variable "images_bucket_arn" {
  description = "Exact application image bucket ARN; required when worker image access is enabled."
  type        = string
  default     = null

  validation {
    condition = var.images_bucket_arn == null ? true : can(
      regex("^arn:aws:s3:::[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.images_bucket_arn)
    )
    error_message = "Use one exact S3 bucket ARN, without wildcards or object paths."
  }
}
