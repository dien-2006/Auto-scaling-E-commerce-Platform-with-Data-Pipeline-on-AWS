
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

output "public_image_prefixes" {
  description = "Only verified image prefixes may be served through this distribution."
  value       = ["product-images/", "shop-logos/"]
}
