
variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "images_bucket_name" {
  description = "Private S3 images bucket name"
  type        = string
}

variable "images_bucket_arn" {
  description = "Private S3 images bucket ARN"
  type        = string
}

variable "images_bucket_domain_name" {
  description = "Regional domain of the images bucket"
  type        = string
}

variable "price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
}

variable "common_tags" {
  type    = map(string)
  default = {}
}
