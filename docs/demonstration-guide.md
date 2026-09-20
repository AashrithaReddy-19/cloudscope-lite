# Faculty demonstration guide

## Current status

The application is deployed and healthy on AWS as a single Elastic Beanstalk environment: FastAPI serves both the API and the built React app from one origin (HTTP only). CloudFront was dropped after its creation was permanently blocked by an AWS account-level restriction, and a separate S3-website frontend was considered and then also dropped in favor of this simpler single-origin design — see `docs/aws-deployment.md`. Run this script against the Elastic Beanstalk URL once deployed, or `http://localhost:3000` (`npm run dev`) against the local backend beforehand.

## Sequence (5-7 minutes)

1. **Motivate the problem** (30s): Terraform lets you provision AWS resources with no idea what they'll cost until the bill arrives. CloudScope Lite estimates cost *before* `terraform apply` ever runs, without executing any of the submitted Terraform.
2. **Show the sample input** (30s): open `examples/basic_web_app/main.tf` — one `aws_instance`, one `aws_ebs_volume`, one `aws_s3_bucket`.
3. **Register and sign in** (30s).
4. **Create a project** (30s): pick a region (`ap-south-1` or `us-east-1`, both fully priced) and a simulated monthly budget.
5. **Submit the analysis** (45s): paste or upload the sample `.tf` file, pick a workload scenario, run it.
6. **Walk the results** (90s): per-resource cost table with rate/unit/formula, the pricing effective date and source, low/medium/high workload comparison tabs, the PASS/WARNING/FAIL budget verdict, and the explainable recommendations (each with its own rationale, not just a number).
7. **Show a WARNING/FAIL** (45s): lower the project's budget and re-run, or open `examples/over_budget_app/main.tf`, to show the same analysis crossing into WARNING/FAIL.
8. **Show an unsupported resource** (20s): mention that any resource type outside `aws_instance`/`aws_ebs_volume`/`aws_s3_bucket`/`aws_db_instance` is flagged as an explicit warning, never silently skipped or priced as zero.
9. **Downloads and history** (30s): download the JSON and CSV reports; show the saved-analyses list persists across a logout/login (PostgreSQL, not browser state).
10. **Forecast and anomalies** (45s): upload `sample_data/historical_costs.csv`, show the moving-average/linear-regression forecast and the IQR/rolling z-score anomaly flags, noting the stated data-sufficiency limitations.
11. **CI/CD angle** (20s): run `python scripts/cost_check.py --terraform examples/basic_web_app/main.tf --budget 20 --region ap-south-1`, point out the exit code (0 pass/warning, 1 enforced fail, 2 invalid input) — this is how a pipeline would gate a deploy on estimated cost.
12. **Close with the AWS architecture** (30s): one Elastic Beanstalk environment serving React and FastAPI together from a multi-stage Docker build, private RDS, a completely private S3 bucket for backend deployment artifacts (plus a second private bucket reserved for future use), IAM least-privilege roles, CloudWatch + SNS + Budget for the *real* AWS account spend — distinct from the simulated per-project budget the analysis itself checks. Mention honestly that the public URL is HTTP only (no TLS certificate is attached), which is why this is a demo architecture, not a production one.

## Talking point: two different budgets

Be explicit that there are two unrelated budgets in play: the **simulated monthly project budget** a user sets per project (checked by the cost analysis, PASS/WARNING/FAIL) versus the **real AWS account Budget** (`cloudscope-lite-demo-monthly`, $5/month) that emails an alert if actual AWS spend approaches it. The first is a teaching tool inside the app; the second is a real safety net for this AWS account and does not stop spending on its own.
