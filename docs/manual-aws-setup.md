# Manual AWS setup

Use root only for initial MFA/contact/billing setup, create a small Budget and IAM Identity Center identity, then sign out; never create root keys. Create a unique encrypted S3 bucket, build `frontend/dist`, upload it, and configure demo website hosting (CloudFront is safer for production). Launch a small Amazon Linux EC2 with encrypted EBS, HTTP allowed, SSH restricted to your IP (or use Session Manager), and never expose 5432/8000. Attach the SSM/CloudWatch role, install Git/Docker, place a production `.env` on-host, and run production Compose. Verify `/health`, logs, and CPU alarm.

For cleanup, first empty all S3 object versions, then remove the bucket, terminate EC2, verify EBS/Elastic IP removal, remove CloudWatch logs, Budget, and project IAM roles. Stopping EC2 does not remove storage charges. Every destructive step needs explicit approval.
