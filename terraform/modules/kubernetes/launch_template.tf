
locals {
  # Also exposed for the owner-run, existing-cluster bootstrap update. No join
  # token is embedded: each new worker reads the current SSM parameter itself.
  worker_user_data_base64 = base64encode(join("\n", [
    "#!/bin/bash",
    templatefile("${path.module}/scripts/install-k8s.sh.tftpl", {
      kubernetes_minor_version = var.kubernetes_minor_version
    }),
    local.ecr_provider_bootstrap,
    local.node_identity_bootstrap,
    templatefile("${path.module}/scripts/worker.sh.tftpl", {
      aws_region               = var.aws_region
      join_parameter_name      = local.join_parameter_name
      control_plane_private_ip = aws_instance.control_plane.private_ip
    })
  ]))
}

resource "aws_launch_template" "worker" {
  name_prefix = "${local.name_prefix}-worker-"

  image_id      = data.aws_ami.ubuntu.id
  instance_type = var.worker_instance_type

  vpc_security_group_ids = [
    var.worker_sg_id
  ]

  iam_instance_profile {
    name = var.worker_instance_profile_name
  }

  block_device_mappings {
    device_name = "/dev/sda1"

    ebs {
      volume_size           = var.root_volume_size
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = var.worker_imds_hop_limit
  }

  user_data = local.worker_user_data_base64

  tag_specifications {
    resource_type = "instance"

    tags = merge(var.common_tags, {
      Name = "${local.name_prefix}-worker"
      Role = "kubernetes-worker"
    })
  }

  tags = merge(var.common_tags, {
    Name = "${local.name_prefix}-worker-template"
  })
}
