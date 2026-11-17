variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "ap-southeast-1"
}
variable "acm_certificate_arn" {
  description = "ACM certificate ARN for production HTTPS"
  type        = string
}
