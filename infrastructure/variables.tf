variable "aws_region" {
  description = "AWS Region for all regional resources."
  type        = string
  default     = "ap-south-1"

  validation {
    condition     = length(trimspace(var.aws_region)) > 0
    error_message = "aws_region must not be empty."
  }
}

variable "project_name" {
  description = "Short lowercase project name used in resource names and tags."
  type        = string
  default     = "cloudscope-lite"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,31}$", var.project_name))
    error_message = "project_name must be 3-32 lowercase letters, digits, or hyphens and start with a letter."
  }
}

variable "environment" {
  description = "Deployment environment label."
  type        = string
  default     = "student-demo"

  validation {
    condition     = contains(["demo", "student-demo", "development", "staging", "production"], var.environment)
    error_message = "environment must be demo, student-demo, development, staging, or production."
  }
}

variable "frontend_bucket_prefix" {
  description = "Prefix for the globally unique public website bucket."
  type        = string
  default     = "cloudscope-lite-frontend"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{2,40}$", var.frontend_bucket_prefix))
    error_message = "frontend_bucket_prefix must be a valid lowercase S3 bucket prefix."
  }
}

variable "artifact_bucket_prefix" {
  description = "Prefix for the globally unique private Elastic Beanstalk artifact bucket."
  type        = string
  default     = "cloudscope-lite-artifacts"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{2,40}$", var.artifact_bucket_prefix))
    error_message = "artifact_bucket_prefix must be a valid lowercase S3 bucket prefix."
  }
}

variable "database_name" {
  description = "PostgreSQL database name."
  type        = string
  default     = "cloudscope"

  validation {
    condition     = can(regex("^[A-Za-z][A-Za-z0-9_]{0,62}$", var.database_name))
    error_message = "database_name must be a valid PostgreSQL identifier."
  }
}

variable "database_username" {
  description = "PostgreSQL master username. The password is generated and managed by RDS in Secrets Manager."
  type        = string
  default     = "cloudscope_admin"
  sensitive   = true

  validation {
    condition     = can(regex("^[A-Za-z][A-Za-z0-9_]{0,62}$", var.database_username))
    error_message = "database_username must be a valid PostgreSQL identifier."
  }
}

variable "database_instance_class" {
  description = "Small RDS instance class suitable for a temporary student demonstration."
  type        = string
  default     = "db.t4g.micro"
}

variable "budget_limit_usd" {
  description = "Low monthly AWS cost budget in USD."
  type        = number
  default     = 5

  validation {
    condition     = var.budget_limit_usd > 0
    error_message = "budget_limit_usd must be greater than zero."
  }
}

variable "create_budget" {
  description = "Whether Terraform should manage the CloudScope monthly budget. Disable when an equivalent manual budget exists."
  type        = bool
  default     = true
}

variable "budget_email" {
  description = "Email address that receives forecasted budget notifications."
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.budget_email))
    error_message = "budget_email must be a valid email address."
  }
}

variable "alarm_email" {
  description = "Optional email address for the Elastic Beanstalk health alarm. Leave null to create no subscription."
  type        = string
  default     = null
  sensitive   = true

  validation {
    condition     = var.alarm_email == null || can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.alarm_email))
    error_message = "alarm_email must be null or a valid email address."
  }
}
