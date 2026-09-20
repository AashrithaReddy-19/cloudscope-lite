resource "aws_elastic_beanstalk_application" "backend" {
  name        = "${var.project_name}-${var.environment}"
  description = "CloudScope Lite FastAPI backend"
}

resource "aws_elastic_beanstalk_application_version" "backend" {
  name        = "${var.environment}-${substr(local.backend_bundle_hash, 0, 16)}"
  application = aws_elastic_beanstalk_application.backend.name
  bucket      = aws_s3_object.backend_bundle.bucket
  key         = aws_s3_object.backend_bundle.key

  # The name is content-addressed (see local.backend_bundle_hash), so a new
  # version is always distinct from the one the environment currently runs.
  # create_before_destroy guarantees the new version object exists before
  # the old one is removed, and the environment (below) only ever points at
  # an application version that has already been created.
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_elastic_beanstalk_environment" "backend" {
  name                = "${var.project_name}-${var.environment}"
  application         = aws_elastic_beanstalk_application.backend.name
  solution_stack_name = data.aws_elastic_beanstalk_solution_stack.docker.name
  version_label       = aws_elastic_beanstalk_application_version.backend.name

  setting {
    namespace = "aws:elasticbeanstalk:environment"
    name      = "EnvironmentType"
    value     = "SingleInstance"
  }

  setting {
    namespace = "aws:elasticbeanstalk:application"
    name      = "Application Healthcheck URL"
    value     = "/health"
  }

  setting {
    namespace = "aws:elasticbeanstalk:environment"
    name      = "ServiceRole"
    value     = aws_iam_role.elastic_beanstalk_service.arn
  }

  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "IamInstanceProfile"
    value     = aws_iam_instance_profile.elastic_beanstalk.name
  }

  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "InstanceType"
    value     = "t3.micro"
  }

  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "SecurityGroups"
    value     = aws_security_group.elastic_beanstalk.id
  }

  setting {
    namespace = "aws:ec2:vpc"
    name      = "VPCId"
    value     = data.aws_vpc.default.id
  }

  setting {
    namespace = "aws:ec2:vpc"
    name      = "Subnets"
    value     = join(",", data.aws_subnets.default.ids)
  }

  setting {
    namespace = "aws:ec2:vpc"
    name      = "AssociatePublicIpAddress"
    value     = "true"
  }

  setting {
    namespace = "aws:elasticbeanstalk:cloudwatch:logs"
    name      = "StreamLogs"
    value     = "true"
  }

  setting {
    namespace = "aws:elasticbeanstalk:cloudwatch:logs"
    name      = "RetentionInDays"
    value     = "7"
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "DB_HOST"
    value     = aws_db_instance.postgresql.address
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "JWT_SECRET"
    value     = random_password.jwt.result
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "DB_PORT"
    value     = tostring(aws_db_instance.postgresql.port)
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "DB_NAME"
    value     = var.database_name
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "DB_USERNAME"
    value     = var.database_username
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "DB_SECRET_ARN"
    value     = aws_db_instance.postgresql.master_user_secret[0].secret_arn
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "AWS_REGION"
    value     = var.aws_region
  }

  depends_on = [
    aws_iam_role_policy_attachment.elastic_beanstalk_service_health,
    aws_iam_role_policy_attachment.elastic_beanstalk_service_updates,
    aws_iam_role_policy_attachment.elastic_beanstalk_web_tier,
    aws_iam_role_policy.application,
  ]
}

resource "random_password" "jwt" {
  length  = 48
  special = true
}
