# CloudScope Lite AWS infrastructure

This Terraform deployment uses the default VPC and its default subnets. It creates a single-instance Elastic Beanstalk Docker environment that serves both the React frontend and the FastAPI backend from one origin, and a private Single-AZ PostgreSQL RDS database. Elastic Beanstalk manages its underlying EC2 instance; this configuration intentionally contains no standalone `aws_instance`. There is no CloudFront and no S3 static website hosting - both were tried and dropped (CloudFront creation is blocked at the AWS account level; the S3-website alternative was replaced by this simpler single-origin design before it was ever applied).

`local.backend_bundle_path` points at `../cloudscope-backend.zip`, built by `scripts/build_beanstalk_bundle.ps1` from backend source, the pricing catalogue, and the frontend source (not a pre-built `dist/` - the Elastic Beanstalk Docker image builds React itself in a Node stage). Its instance role can retrieve only the RDS-managed database secret referenced by the environment (`DB_SECRET_ARN`) and read the specific S3 object holding that bundle. No database password is passed through Terraform outputs.

The instance role may call `pricing:DescribeServices`, `pricing:GetAttributeValues`, and `pricing:GetProducts`. The AWS Price List API is consumed on demand by application or catalogue-update code; it is an API, not a continuously running AWS resource.

Elastic Beanstalk's own HTTP listener on port 80 has no TLS certificate attached, so the public URL is HTTP only - an accepted trade-off documented in `docs/aws-deployment.md`. RDS is private, Single-AZ, encrypted, and accepts port 5432 only from the Elastic Beanstalk instance security group. Deletion protection and final snapshots are disabled only for this temporary student project.

Expected chargeable services include the Elastic Beanstalk-managed EC2 instance and EBS volume, RDS PostgreSQL instance and storage, S3 storage/requests, CloudWatch logs/metrics/alarms, Secrets Manager, and outbound data transfer. Elastic Beanstalk itself has no separate service charge, but its underlying resources do. The USD 5 budget is an alert and does not cap or stop spending.

After creating an uncommitted `terraform.tfvars`, the review-only command is:

```powershell
C:\Tools\Terraform\terraform.exe plan -var-file=terraform.tfvars -out=cloudscope.tfplan
```

Do not apply the plan without explicit approval.
