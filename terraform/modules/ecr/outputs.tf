
output "frontend_repository_url" {
  description = "Frontend ECR repository URI"
  value       = aws_ecr_repository.main["frontend"].repository_url
}

output "backend_repository_url" {
  description = "Backend ECR repository URI"
  value       = aws_ecr_repository.main["backend"].repository_url
}

output "frontend_repository_arn" {
  description = "Frontend ECR repository ARN"
  value       = aws_ecr_repository.main["frontend"].arn
}

output "backend_repository_arn" {
  description = "Backend ECR repository ARN"
  value       = aws_ecr_repository.main["backend"].arn
}

output "repository_urls" {
  description = "All ECR repository URLs"

  value = {
    for name, repo in aws_ecr_repository.main :
    name => repo.repository_url
  }
}

output "repository_arns" {
  description = "All ECR repository ARNs"

  value = {
    for name, repo in aws_ecr_repository.main :
    name => repo.arn
  }
}
