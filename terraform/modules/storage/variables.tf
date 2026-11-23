
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

variable "image_upload_origins" {
  description = "Exact browser origins allowed to upload images; empty disables managed CORS."
  type        = list(string)
  default     = []

  validation {
    condition = alltrue([
      for origin in var.image_upload_origins :
      can(regex("^https?://[A-Za-z0-9.-]+(:[0-9]{1,5})?$", origin))
    ])
    error_message = "Use exact HTTP/HTTPS origins without wildcard, credentials, path or trailing slash."
  }

  validation {
    condition     = length(distinct(var.image_upload_origins)) == length(var.image_upload_origins)
    error_message = "Image upload origins must be unique."
  }
}
