resource "aws_security_group" "elastic_beanstalk" {
  name_prefix = "${var.project_name}-eb-"
  description = "Elastic Beanstalk application instances"
  vpc_id      = data.aws_vpc.default.id

  # The frontend now calls this backend directly over its public Elastic
  # Beanstalk HTTP URL (no CloudFront in front of it), so port 80 is public
  # ingress by design. Elastic Beanstalk also attaches its own
  # auto-generated security group (name pattern "awseb-*-AWSEBSecurityGroup-*")
  # to the instance, which Terraform does not own and which already allows
  # 0.0.0.0/0 on port 80.
  ingress {
    description = "Public HTTP - Elastic Beanstalk is reached directly, there is no CDN in front of it"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Outbound access for package and AWS API calls"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "database" {
  name_prefix = "${var.project_name}-rds-"
  description = "Private PostgreSQL access from Elastic Beanstalk only"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "PostgreSQL from Elastic Beanstalk instances"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.elastic_beanstalk.id]
  }

  egress {
    description = "Required response traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}
