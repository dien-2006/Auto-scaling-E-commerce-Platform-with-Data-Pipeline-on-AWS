locals {
  name_prefix = "${var.project_name}-${var.environment}"

  nat_count = (
    var.nat_gateway_mode == "per_az" ? 2 :
    var.nat_gateway_mode == "single" ? 1 : 0
  )
}