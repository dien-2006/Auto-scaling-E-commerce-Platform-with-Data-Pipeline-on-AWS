variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "ap-southeast-1"
}

variable "image_upload_origins" {
  description = "Dev browser origins for S3 image uploads; add the HTTPS dev website when available."
  type        = list(string)
  default     = ["http://localhost:3001"]
}
