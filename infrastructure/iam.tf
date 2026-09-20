data "aws_iam_policy_document" "elastic_beanstalk_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["elasticbeanstalk.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "elastic_beanstalk_service" {
  name_prefix        = "${var.project_name}-eb-service-"
  assume_role_policy = data.aws_iam_policy_document.elastic_beanstalk_assume_role.json
}

resource "aws_iam_role_policy_attachment" "elastic_beanstalk_service_health" {
  role       = aws_iam_role.elastic_beanstalk_service.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSElasticBeanstalkEnhancedHealth"
}

resource "aws_iam_role_policy_attachment" "elastic_beanstalk_service_updates" {
  role       = aws_iam_role.elastic_beanstalk_service.name
  policy_arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkManagedUpdatesCustomerRolePolicy"
}

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "elastic_beanstalk_instance" {
  name_prefix        = "${var.project_name}-eb-instance-"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

resource "aws_iam_role_policy_attachment" "elastic_beanstalk_web_tier" {
  role       = aws_iam_role.elastic_beanstalk_instance.name
  policy_arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkWebTier"
}

resource "aws_iam_instance_profile" "elastic_beanstalk" {
  name_prefix = "${var.project_name}-eb-"
  role        = aws_iam_role.elastic_beanstalk_instance.name
}

data "aws_iam_policy_document" "application" {
  statement {
    sid = "ReadApplicationBundle"
    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
    ]
    resources = [aws_s3_object.backend_bundle.arn]
  }

  statement {
    sid       = "ReadManagedDatabaseSecret"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_db_instance.postgresql.master_user_secret[0].secret_arn]
  }

  statement {
    sid = "QueryAwsPublicPricing"
    actions = [
      "pricing:DescribeServices",
      "pricing:GetAttributeValues",
      "pricing:GetProducts",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "application" {
  name_prefix = "${var.project_name}-application-"
  role        = aws_iam_role.elastic_beanstalk_instance.id
  policy      = data.aws_iam_policy_document.application.json
}
