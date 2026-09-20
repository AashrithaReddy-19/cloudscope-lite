resource "random_id" "frontend_suffix" {
  byte_length = 4
}

resource "random_id" "artifact_suffix" {
  byte_length = 4
}

locals {
  backend_bundle_path = "${path.module}/../cloudscope-backend.zip"
  backend_bundle_hash = filesha256(local.backend_bundle_path)
  backend_bundle_key  = "elasticbeanstalk/cloudscope-backend-${substr(local.backend_bundle_hash, 0, 16)}.zip"
}

resource "aws_s3_bucket" "frontend" {
  bucket = "${var.frontend_bucket_prefix}-${random_id.frontend_suffix.hex}"
}

resource "aws_s3_bucket_ownership_controls" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  versioning_configuration {
    status = "Enabled"
  }
}

# The React build is served by FastAPI/Elastic Beanstalk itself now (baked
# into the same Docker image as static files), not from this bucket. This
# bucket stays fully private with no bucket policy and no public access of
# any kind - it is reserved for possible future project use and holds no
# application data, database passwords, or user-uploaded Terraform files.
resource "aws_s3_bucket" "artifacts" {
  bucket = "${var.artifact_bucket_prefix}-${random_id.artifact_suffix.hex}"
}

resource "aws_s3_bucket_ownership_controls" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_object" "backend_bundle" {
  bucket      = aws_s3_bucket.artifacts.id
  key         = local.backend_bundle_key
  source      = local.backend_bundle_path
  source_hash = filebase64sha256(local.backend_bundle_path)

  depends_on = [
    aws_s3_bucket_ownership_controls.artifacts,
    aws_s3_bucket_public_access_block.artifacts,
    aws_s3_bucket_server_side_encryption_configuration.artifacts,
    aws_s3_bucket_versioning.artifacts,
  ]

  # The key is content-addressed (see local.backend_bundle_key), so a new
  # bundle is always a genuinely new object, never an in-place overwrite of
  # the one the running environment still references. create_before_destroy
  # ensures the new object exists in S3 before the old one is removed, so
  # there is never a moment with no valid bundle object present.
  lifecycle {
    create_before_destroy = true
  }
}
