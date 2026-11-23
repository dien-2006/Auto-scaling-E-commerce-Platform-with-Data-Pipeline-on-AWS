
resource "aws_instance" "control_plane" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.control_plane_instance_type

  subnet_id = var.private_subnet_ids[0]

  vpc_security_group_ids = [
    var.control_plane_sg_id
  ]

  iam_instance_profile = var.control_plane_instance_profile_name

  associate_public_ip_address = false

  root_block_device {
    volume_size           = var.root_volume_size
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  user_data = join("\n", [
    "#!/bin/bash",
    templatefile("${path.module}/scripts/install-k8s.sh.tftpl", {
      kubernetes_minor_version = var.kubernetes_minor_version
    }),
    local.ecr_provider_bootstrap,
    local.node_identity_bootstrap,
    templatefile("${path.module}/scripts/control-plane.sh.tftpl", {
      cluster_name        = var.cluster_name
      pod_cidr            = var.pod_cidr
      aws_region          = var.aws_region
      join_parameter_name = local.join_parameter_name
    })
  ])

  user_data_replace_on_change = false

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }
  depends_on = [
    aws_iam_role_policy.control_plane_bootstrap
  ]

  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-control-plane"
    Role = "kubernetes-control-plane"
  })
}
