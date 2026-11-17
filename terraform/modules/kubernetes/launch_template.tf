
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
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  user_data = base64encode(join("\n", [
    "#!/bin/bash",
    templatefile("${path.module}/scripts/install-k8s.sh.tftpl", {
      kubernetes_minor_version = var.kubernetes_minor_version
    }),
    templatefile("${path.module}/scripts/worker.sh.tftpl", {
      aws_region          = var.aws_region
      join_parameter_name = local.join_parameter_name
    })
  ]))

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
