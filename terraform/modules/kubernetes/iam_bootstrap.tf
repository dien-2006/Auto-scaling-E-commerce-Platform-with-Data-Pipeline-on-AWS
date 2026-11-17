
locals {
  join_parameter_arn = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${local.join_parameter_name}"
}

data "aws_iam_policy_document" "control_plane_bootstrap" {
  statement {
    sid    = "PublishKubernetesJoinCommand"
    effect = "Allow"

    actions = [
      "ssm:PutParameter"
    ]

    resources = [
      local.join_parameter_arn
    ]
  }
}

resource "aws_iam_role_policy" "control_plane_bootstrap" {
  name = "${local.name_prefix}-publish-join"
  role = var.control_plane_role_name

  policy = data.aws_iam_policy_document.control_plane_bootstrap.json
}

data "aws_iam_policy_document" "worker_bootstrap" {
  statement {
    sid    = "ReadKubernetesJoinCommand"
    effect = "Allow"

    actions = [
      "ssm:GetParameter"
    ]

    resources = [
      local.join_parameter_arn
    ]
  }
}

resource "aws_iam_role_policy" "worker_bootstrap" {
  name = "${local.name_prefix}-read-join"
  role = var.worker_role_name

  policy = data.aws_iam_policy_document.worker_bootstrap.json
}
