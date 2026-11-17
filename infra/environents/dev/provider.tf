terraform {
  required_version = ">= 0.12"
  required_providers {
    aws = {
        source = "hashicorp/aws"
        version = "~> 6.0"
    }
  }
}

provider "aws"{
    region = var.region
    default_tags {
        tags = {
            Project = "Coco"
            Environment = "Dev"
            ManagedBy = "Terraform"
        }
    }
}