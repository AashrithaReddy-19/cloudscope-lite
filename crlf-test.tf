resource "aws_instance" "web_server" {
  instance_type = "t3.micro"

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
  }
}

resource "aws_ebs_volume" "application_data" {
  availability_zone = "us-east-1a"
  type              = "gp3"
  size              = 20
}

resource "aws_s3_bucket" "application_files" {
  bucket = "cloudscope-crlf-test"
}
