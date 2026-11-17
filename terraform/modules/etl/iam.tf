# Trust Policy và IAM Roles
data "aws_iam_policy_document" "glue_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "extract" {
  name = "${local.name_prefix}-glue-extract-role"

  assume_role_policy = data.aws_iam_policy_document.glue_assume_role.json

  tags = var.common_tags
}

resource "aws_iam_role" "transform" {
  name = "${local.name_prefix}-glue-transform-role"

  assume_role_policy = data.aws_iam_policy_document.glue_assume_role.json

  tags = var.common_tags
}

resource "aws_iam_role_policy_attachment" "extract_service" {
  role = aws_iam_role.extract.name

  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy_attachment" "transform_service" {
  role = aws_iam_role.transform.name

  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# IAM Policy cho Extract Job

data "aws_iam_policy_document" "extract_data" {
  statement {
    sid = "ListETLBucket"

    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation"
    ]

    resources = [
      var.etl_bucket_arn
    ]
  }

  statement {
    sid = "ReadExtractScript"

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${var.etl_bucket_arn}/${local.extract_script_key}"
    ]
  }

  statement {
    sid = "WriteRawData"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject"
    ]

    resources = [
      "${var.etl_bucket_arn}/raw/*",
      "${var.etl_bucket_arn}/tmp/*"
    ]
  }

  statement {
    sid = "ReadPostgresSecret"

    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ]

    resources = [
      var.db_secret_arn
    ]
  }
}

resource "aws_iam_role_policy" "extract_data" {
  name = "${local.name_prefix}-extract-data-policy"
  role = aws_iam_role.extract.name

  policy = data.aws_iam_policy_document.extract_data.json
}
# IAM Policy cho Transform Job

data "aws_iam_policy_document" "transform_data" {
  statement {
    sid = "ListETLBucket"

    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation"
    ]

    resources = [
      var.etl_bucket_arn
    ]
  }

  statement {
    sid = "ReadTransformScript"

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${var.etl_bucket_arn}/${local.transform_script_key}"
    ]
  }

  statement {
    sid = "ReadRawData"

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${var.etl_bucket_arn}/raw/*"
    ]
  }

  statement {
    sid = "WriteSilverGoldData"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject"
    ]

    resources = [
      "${var.etl_bucket_arn}/silver/*",
      "${var.etl_bucket_arn}/gold/*",
      "${var.etl_bucket_arn}/tmp/*"
    ]
  }
}

resource "aws_iam_role_policy" "transform_data" {
  name = "${local.name_prefix}-transform-data-policy"
  role = aws_iam_role.transform.name

  policy = data.aws_iam_policy_document.transform_data.json
}
