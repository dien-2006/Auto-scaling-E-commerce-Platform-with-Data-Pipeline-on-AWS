variable "project_name" {
  description = "The name of the project"
  type        = string

}

variable "environment" {
  description = "The environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones to use for subnets"
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) == 2 && length(distinct(var.availability_zones)) == 2
    error_message = "You must provide exactly 2 distinct availability zones."
  }
}

variable "public_subnet_cidrs" {
  description = "List of CIDR blocks for public subnets"
  type        = list(string)

  validation {
    condition     = length(var.public_subnet_cidrs) == 2
    error_message = "You must provide exactly 2 CIDR blocks for public subnets."
  }
}

variable "private_subnet_cidrs" {
  description = "List of CIDR blocks for private subnets"
  type        = list(string)

  validation {
    condition     = length(var.private_subnet_cidrs) == 2
    error_message = "You must provide exactly 2 CIDR blocks for private subnets."
  }
}

variable "nat_gateway_mode" {
  description = "NAT Gateway mode: none, single, or per_az"
  type        = string
  default     = "none"

  validation {
    condition     = contains(["single", "per_az", "none"], var.nat_gateway_mode)
    error_message = "Use none, single, or per_az."
  }
}

variable "common_tags" {
  description = "Tags for all network resources"
  type        = map(string)
  default     = {}
}