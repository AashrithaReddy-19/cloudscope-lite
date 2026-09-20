# Safe AWS deployment

## Current status (2026-09-20)

**Neither CloudFront nor S3 website hosting is part of this project.** Every CloudFront creation attempt (most recently request ID `627749c2-c9c3-4028-943a-1a0f77dda5a4`) failed with an AWS account-level restriction that never cleared. An S3-static-website alternative was drafted next but was deliberately not applied and has since been reverted: the final decision is a **single Elastic Beanstalk deployment that serves both the React frontend and the FastAPI backend from one origin**. The Docker image built by Elastic Beanstalk is multi-stage: a Node stage builds the React production bundle, and the Python/FastAPI runtime stage serves those static files directly (mounted at `/assets`, with `index.html` as the SPA fallback for any unmatched non-`/api` path) alongside the existing `/api/*` and `/health` routes. There is no cross-origin call anywhere in production, so the CloudFront-only origin-verification middleware and its custom header requirement have been removed entirely, and CORS is a local-development-only convenience (production never needs it, since the frontend and API share one origin).

Deployed in account `083414537001` (`ap-south-1`) via the `cloudscope-admin` profile: Elastic Beanstalk environment `cloudscope-lite-demo` (Green/Ok/Ready) serving the full application, a private RDS PostgreSQL instance, a private backend-artifact S3 bucket, a second S3 bucket kept fully private as a reserved project bucket (holds no application data), IAM roles/instance profile, CloudWatch logs/alarm, an SNS alarm topic, and a $5 AWS Budget.

## Prerequisites and security

Use the `cloudscope-admin` profile only after rotating any previously exposed access key. Confirm that STS identifies IAM user `CloudScopeDeployment`, never root. Keep `terraform.tfvars`, state, plans, `.env` files, deployment bundles, access keys, database credentials, JWT secrets, and notification emails out of Git. Terraform state is sensitive because generated values such as the JWT secret and references to the RDS-managed secret are represented there.

Terraform 1.16.2 is installed at `C:\Tools\Terraform\terraform.exe`. Restart VS Code if the updated user PATH is not visible to existing terminals.

## Validate and review

From `infrastructure`:

```powershell
C:\Tools\Terraform\terraform.exe fmt -recursive
C:\Tools\Terraform\terraform.exe init -backend=false
C:\Tools\Terraform\terraform.exe validate
$env:AWS_PROFILE = "cloudscope-admin"
$env:AWS_REGION = "ap-south-1"
$env:AWS_DEFAULT_REGION = "ap-south-1"
C:\Tools\Terraform\terraform.exe plan -var-file="terraform.tfvars" -out="cloudscope.tfplan"
C:\Tools\Terraform\terraform.exe show cloudscope.tfplan
```

A plan is analysis only. Never apply it until the exact approval phrase required by the project has been provided and the identity, region, and zero-destroy result have been rechecked.

## Backend bundle (now includes the frontend source)

Run `scripts/build_beanstalk_bundle.ps1` locally before validation or planning. It creates the ignored `cloudscope-backend.zip` from an explicit allowlist: the multi-stage Elastic Beanstalk Dockerfile, `start.sh`, backend application modules/migrations/requirements, the saved pricing catalogue, and the **frontend source** (`package.json`, `package-lock.json`, `index.html`, `tsconfig.json`, `vite.config.mjs`, `src/`) — never `frontend/dist` or `frontend/node_modules`, since the image builds React itself. It excludes environment files, credentials, Terraform files/state, Git metadata, Node dependencies, virtual environments, Python caches, databases, and tests.

Terraform creates a dedicated, globally unique private artifact bucket, blocks all public access, enables AES256 server-side encryption and versioning, then uploads the ZIP with `aws_s3_object`. A content hash changes the object key and Elastic Beanstalk application-version label whenever the bundle changes. Elastic Beanstalk then builds the Docker image from that bundle: a Node stage runs `npm ci && npm run build` (no `VITE_API_URL` is ever set - the app always calls a plain relative `/api/...`), and the Python stage copies the resulting `dist/` into `/app/static`, which FastAPI serves. There is no separate frontend upload step and nothing to approve for it.

The configured application bundle retrieves the RDS-managed password through `DB_SECRET_ARN`. FastAPI and Alembic import the same database module and therefore use the same Secrets Manager-derived PostgreSQL URL. The startup script retries the migration for up to five minutes while RDS becomes ready; Uvicorn starts only after migration success. It listens on `0.0.0.0:8000`, while Elastic Beanstalk's reverse proxy provides public HTTP access without opening port 8000 in the security group.

## Database migrations

The backend container runs `alembic upgrade head` before Uvicorn. Before any approved AWS deployment, review the migration and take any required backup. Do not run production migrations during plan-only preparation. RDS is encrypted, private, Single-AZ, and demo-only settings disable deletion protection and the final snapshot.

## HTTP-only limitation (accepted trade-off)

**The public URL is plain HTTP.** Elastic Beanstalk's own listener on port 80 has no TLS certificate attached (a certificate would require a custom domain and ACM, which this project intentionally avoids). This is an explicit, accepted trade-off for a temporary student demonstration, not an oversight: the original plan (CloudFront, which would have added the AWS-managed HTTPS certificate) is blocked by an AWS account-level restriction outside this project's control. Do not treat this as production-grade; do not submit real credentials or sensitive data through it.

## Verification after a separately approved apply

Verify the Elastic Beanstalk URL serves the React app at `/`, a client-side route also returns the app (SPA fallback), `/health` returns 200, an unknown `/api/*` path returns a JSON 404 (never the React page), RDS connectivity, migration revision, CloudWatch log delivery and environment-health alarm, and Budget notifications. AWS Budgets are alerts, not hard spending limits.

## Cost warnings

Chargeable services include the Elastic Beanstalk-managed EC2 instance/EBS storage, RDS PostgreSQL and storage, Secrets Manager, S3 storage/requests, CloudWatch logs/alarm, SNS email delivery where applicable, and data transfer. SNS email subscriptions require recipient confirmation after creation. Budget notifications may also require email verification; a budget warns about spend but does not stop resources. The Price List API is called on demand by catalogue-update code and is not a continuously running resource. The application normally reads its dated saved catalogue and treats missing pricing as an error.

## Cleanup

Cleanup requires separate explicit approval. Before any destroy, save required data, review a destroy plan, empty all versions from both S3 buckets, and decide whether an RDS final snapshot is required. Verify removal of the Elastic Beanstalk environment/application, RDS instance, S3 objects/buckets, security groups, IAM roles, CloudWatch logs/alarm, SNS topic, Budget, and Secrets Manager secret scheduling. Remove the deployment access key after the demonstration. Never assume stopping an EC2 instance removes EBS or database charges.
