variable "instance_type" { default = "t3.micro" }
resource "aws_instance" "web" { instance_type = var.instance_type root_volume_size_gb = 8 tags = { Environment = "demo" } }
resource "aws_ebs_volume" "data" { size = 20 type = "gp3" }
resource "aws_s3_bucket" "assets" { estimated_storage_gb = 50 }

