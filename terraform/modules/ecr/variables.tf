
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

variable "image_tag_mutability" {
  description = "MUTABLE or IMMUTABLE image tags"
  type        = string
  default     = "IMMUTABLE"

  validation {
    condition = contains(
      ["MUTABLE", "IMMUTABLE"],
      var.image_tag_mutability
    )
    error_message = "Use MUTABLE or IMMUTABLE."
  }
}

variable "scan_on_push" {
  description = "Enable basic image scanning on push"
  type        = bool
  default     = true
}

variable "untagged_image_days" {
  description = "Days before deleting untagged images"
  type        = number
  default     = 7

  validation {
    condition     = var.untagged_image_days >= 1
    error_message = "Must be at least 1 day."
  }
}

variable "max_tagged_images" {
  description = "Maximum number of tagged images to retain"
  type        = number
  default     = 15

  validation {
    condition     = var.max_tagged_images >= 1
    error_message = "Must retain at least 1 image."
  }
}

variable "common_tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}
