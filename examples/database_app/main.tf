resource "aws_db_instance" "database" { instance_class = "db.t3.micro" allocated_storage = 20 storage_type = "gp3" engine = "mysql" }

