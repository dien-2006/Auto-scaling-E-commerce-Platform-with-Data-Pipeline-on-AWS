
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

variable "noncurrent_version_days" {
  description = "Days to retain old object versions"
  type        = number
  default     = 30

  validation {
    condition     = var.noncurrent_version_days >= 1
    error_message = "Retention must be at least 1 day."
  }
}

variable "common_tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}
