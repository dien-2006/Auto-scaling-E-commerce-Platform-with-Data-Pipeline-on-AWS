# Tạo 4 Security Groups

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg"
  description = "ALB security group"
  vpc_id      = var.vpc_id

  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-alb-sg"
  })
}

resource "aws_security_group" "control_plane" {
  name        = "${local.name_prefix}-control-plane-sg"
  description = "Kubernetes control plane security group"
  vpc_id      = var.vpc_id

  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-control-plane-sg"
  })
}

resource "aws_security_group" "worker" {
  name        = "${local.name_prefix}-worker-sg"
  description = "Kubernetes worker security group"
  vpc_id      = var.vpc_id

  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-worker-sg"
  })
}

resource "aws_security_group" "rds" {
  name        = "${local.name_prefix}-rds-sg"
  description = "RDS PostgreSQL security group"
  vpc_id      = var.vpc_id

  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-rds-sg"
  })
}

# 4.2. ALB Security Group Rules

resource "aws_vpc_security_group_ingress_rule" "alb_https" {
  security_group_id = aws_security_group.alb.id

  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"

  description = "HTTPS from Internet"
}

resource "aws_vpc_security_group_egress_rule" "alb_frontend" {
  security_group_id = aws_security_group.alb.id

  referenced_security_group_id = aws_security_group.worker.id

  from_port   = var.frontend_node_port
  to_port     = var.frontend_node_port
  ip_protocol = "tcp"

  description = "ALB to frontend NodePort"
}

resource "aws_vpc_security_group_egress_rule" "alb_backend" {
  security_group_id = aws_security_group.alb.id

  referenced_security_group_id = aws_security_group.worker.id

  from_port   = var.backend_node_port
  to_port     = var.backend_node_port
  ip_protocol = "tcp"

  description = "ALB to backend NodePort"
}

# 4.3. Kubernetes Worker Security Group Rules

resource "aws_vpc_security_group_ingress_rule" "worker_frontend" {
  security_group_id = aws_security_group.worker.id

  referenced_security_group_id = aws_security_group.alb.id

  from_port   = var.frontend_node_port
  to_port     = var.frontend_node_port
  ip_protocol = "tcp"

  description = "Frontend traffic from ALB"
}

resource "aws_vpc_security_group_ingress_rule" "worker_backend" {
  security_group_id = aws_security_group.worker.id

  referenced_security_group_id = aws_security_group.alb.id

  from_port   = var.backend_node_port
  to_port     = var.backend_node_port
  ip_protocol = "tcp"

  description = "Backend traffic from ALB"
}

resource "aws_vpc_security_group_ingress_rule" "worker_kubelet" {
  security_group_id = aws_security_group.worker.id

  referenced_security_group_id = aws_security_group.control_plane.id

  from_port   = 10250
  to_port     = 10250
  ip_protocol = "tcp"

  description = "Kubelet from control plane"
}

resource "aws_vpc_security_group_ingress_rule" "worker_internal" {
  security_group_id = aws_security_group.worker.id

  referenced_security_group_id = aws_security_group.worker.id

  ip_protocol = "-1"

  description = "Internal worker node communication"
}

# 4.4. Kubernetes Control Plane Security Group Rules

resource "aws_vpc_security_group_ingress_rule" "control_plane_api_from_worker" {
  security_group_id = aws_security_group.control_plane.id

  referenced_security_group_id = aws_security_group.worker.id

  from_port   = 6443
  to_port     = 6443
  ip_protocol = "tcp"

  description = "Kubernetes API from workers"
}

resource "aws_vpc_security_group_ingress_rule" "control_plane_internal" {
  security_group_id = aws_security_group.control_plane.id

  referenced_security_group_id = aws_security_group.control_plane.id

  ip_protocol = "-1"

  description = "Internal control plane communication"
}

resource "aws_vpc_security_group_ingress_rule" "control_plane_vxlan" {
  security_group_id = aws_security_group.control_plane.id

  referenced_security_group_id = aws_security_group.worker.id

  from_port   = 8472
  to_port     = 8472
  ip_protocol = "udp"

  description = "Flannel VXLAN from workers"
}

resource "aws_vpc_security_group_ingress_rule" "worker_vxlan" {
  security_group_id = aws_security_group.worker.id

  referenced_security_group_id = aws_security_group.control_plane.id

  from_port   = 8472
  to_port     = 8472
  ip_protocol = "udp"

  description = "Flannel VXLAN from control plane"
}

# 4.5. RDS PostgreSQL Security Group Rules

resource "aws_vpc_security_group_ingress_rule" "rds_postgresql" {
  security_group_id = aws_security_group.rds.id

  referenced_security_group_id = aws_security_group.worker.id

  from_port   = 5432
  to_port     = 5432
  ip_protocol = "tcp"

  description = "PostgreSQL from Kubernetes workers"
}

# 4.6. Outbound Rules cho Kubernetes

resource "aws_vpc_security_group_egress_rule" "control_plane_outbound" {
  security_group_id = aws_security_group.control_plane.id

  cidr_ipv4   = "0.0.0.0/0"
  ip_protocol = "-1"

  description = "Control plane outbound traffic"
}

resource "aws_vpc_security_group_egress_rule" "worker_outbound" {
  security_group_id = aws_security_group.worker.id

  cidr_ipv4   = "0.0.0.0/0"
  ip_protocol = "-1"

  description = "Worker outbound traffic"
}


resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id

  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 80
  to_port     = 80
  ip_protocol = "tcp"

  description = "Allow HTTP from Internet"
}
