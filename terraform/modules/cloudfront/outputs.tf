
output "distribution_id" {
  value = aws_cloudfront_distribution.images.id
}

output "distribution_arn" {
  value = aws_cloudfront_distribution.images.arn
}

output "domain_name" {
  value = aws_cloudfront_distribution.images.domain_name
}

output "base_url" {
  value = "https://${aws_cloudfront_distribution.images.domain_name}"
}
