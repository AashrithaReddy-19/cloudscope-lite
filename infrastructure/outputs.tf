output "frontend_bucket_name" {
  description = "Private, reserved S3 bucket, not used to serve the frontend. React is now built into and served by the Elastic Beanstalk backend itself - see backend_url."
  value       = aws_s3_bucket.frontend.id
}

output "artifact_bucket_name" {
  description = "Private S3 bucket containing the Elastic Beanstalk deployment bundle."
  value       = aws_s3_bucket.artifacts.id
}

output "backend_bundle_key" {
  description = "Content-addressed object key for the Elastic Beanstalk deployment bundle."
  value       = aws_s3_object.backend_bundle.key
}

output "backend_url" {
  description = "Elastic Beanstalk backend URL."
  value       = "http://${aws_elastic_beanstalk_environment.backend.cname}"
}

output "elastic_beanstalk_environment_name" {
  description = "Elastic Beanstalk environment name."
  value       = aws_elastic_beanstalk_environment.backend.name
}

output "database_endpoint" {
  description = "Private RDS endpoint and port; contains no password."
  value       = aws_db_instance.postgresql.endpoint
}

output "budget_name" {
  description = "AWS Budget name when Terraform management is enabled; otherwise null."
  value       = var.create_budget ? aws_budgets_budget.monthly[0].name : null
}

output "cloudwatch_log_group_name" {
  description = "Application CloudWatch log-group name."
  value       = aws_cloudwatch_log_group.application.name
}
