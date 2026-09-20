resource "aws_db_subnet_group" "default" {
  name_prefix = "${var.project_name}-"
  description = "Default VPC subnets for CloudScope PostgreSQL"
  subnet_ids  = data.aws_subnets.default.ids
}

resource "aws_db_instance" "postgresql" {
  identifier_prefix = "${var.project_name}-"

  engine         = "postgres"
  instance_class = var.database_instance_class

  allocated_storage     = 20
  max_allocated_storage = 30
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name                     = var.database_name
  username                    = var.database_username
  manage_master_user_password = true
  port                        = 5432

  multi_az                = false
  publicly_accessible     = false
  deletion_protection     = false
  skip_final_snapshot     = true
  backup_retention_period = 1

  db_subnet_group_name   = aws_db_subnet_group.default.name
  vpc_security_group_ids = [aws_security_group.database.id]

  auto_minor_version_upgrade = true
  apply_immediately          = true
}
