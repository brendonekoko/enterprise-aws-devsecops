Enterprise AWS DevSecOps Platform — Financial Transaction Processing API
An AWS-hosted, containerized financial transaction API built to demonstrate infrastructure as code, continuous integration, secure remote deployments, operational monitoring, and deployment recovery planning.
> **Project scope:** Engineering portfolio/lab environment with fictional account and transaction data. This is not a production banking system.
Overview
The application is a Python FastAPI service that exposes account, transfer, transaction-history, and health-check endpoints. The supporting infrastructure is managed with Terraform, application images are built locally with Podman and run on EC2 with Docker, and versioned image archives are transferred using Amazon S3. AWS Systems Manager (SSM) executes remote deployment commands on the EC2 host. Amazon CloudWatch provides infrastructure metrics, alarms, and container log collection.
Technology stack
Area	Tools and services
Application	Python, FastAPI, pytest
Infrastructure as Code	Terraform
Cloud	AWS EC2, VPC networking, IAM, S3, Systems Manager
Containers	Podman (local builds), Docker (EC2 runtime)
Continuous Integration	GitHub Actions, pytest, pip-audit, Docker build
Observability	CloudWatch Agent, CloudWatch Metrics, Alarms, Logs
Operating system	Red Hat Enterprise Linux (development), Linux on EC2
System architecture
```text
Developer / RHEL VM
    |
    |  FastAPI source + pytest + Terraform
    |  Podman builds versioned image
    v
Amazon S3 (versioned image archive names)
    |
    |  EC2 IAM role permits GetObject
    v
AWS EC2 (inside Terraform-managed VPC)
    |  AWS Systems Manager executes deployment commands
    |  Docker runs financial-api on 127.0.0.1:8000
    |  /health validates deployment
    |  Previous v2 container retained for recovery
    v
CloudWatch Agent / Logs / Metrics / Alarm

GitHub Actions: tests -> dependency audit -> container build (CI)
```
Network note: The deployed application is bound to `127.0.0.1:8000` on EC2. It is not presented here as a publicly accessible production API.
API functionality
Endpoint	Purpose
`GET /health`	Application health check
`/accounts`	Account operations
`/accounts/{id}`	Retrieve an account
`/transfer`	Transfer processing
`/transactions`	Transaction history
The API uses fictional, in-memory data. Data does not persist across container restarts; a durable database is a future enhancement.
CI workflow
The GitHub Actions workflow is configured to:
Set up Python 3.11 and run automated tests with pytest.
Audit Python dependencies with pip-audit.
Build a Docker image to validate container packaging.
Validation: Six pytest tests passed during local development (one warning). The CI workflow is configured, but automated deployment from GitHub Actions has not yet been connected; CD is performed separately through AWS SSM.
Deployment process
Build the application image locally with Podman and export it as a tar archive.
Upload the versioned archive to an S3 bucket.
Use an EC2 IAM role with restricted S3 object-read access.
Use AWS Systems Manager to load and validate the new image on EC2.
Test the candidate release on a separate localhost port before promotion.
Stop and rename the current container as a backup, start the new version on the primary localhost port, and run a `/health` check.
On health-check failure, the deployment command includes logic to restore the prior container.
Verified v3 deployment
Release: Financial API `3.0.0`
Image: `localhost/financial-api:v3`
Host: AWS EC2 in `us-east-2`
Deployment mechanism: AWS Systems Manager `AWS-RunShellScript`
Deployment result: `Status: Success`, `DEPLOYMENT_SUCCESS_V3`, empty error output
Health check: Passed after version promotion
Previous release: v2 container preserved as `financial-api-v2-backup`
Important limitation: Rollback logic has been implemented but has not yet been failure-injection tested. This is a successful controlled version promotion, not a claim of a fully validated zero-downtime or automated production release system.
Monitoring and operations
Installed and configured the CloudWatch Agent.
Published a custom `FinancialAPI` / `mem_used_percent` metric.
Created `financial-api-high-memory` alarm at an 80% threshold over five one-minute evaluation periods.
Forwarded Docker JSON container logs to CloudWatch Logs.
Used SSM to run operational checks without opening inbound SSH for deployment.
Engineering challenges and resolutions
IAM access to deployment artifacts: Investigated an S3 authorization failure and updated the Terraform-managed EC2 role policy to allow reads of the versioned `financial-api-*.tar` objects.
Insufficient temporary storage: An SSM deployment attempt encountered `No space left on device` while downloading an image archive. Removed the incomplete temporary archive, checked disk utilization, and reused the image already loaded on the instance rather than disrupting the running v2 service.
Deployment validation: Tested v3 on a separate localhost port, confirmed `/health`, and then promoted it to the primary container name and port with the previous version preserved as a backup.
Current limitations and next steps
Add persistent storage and database migrations for transaction data.
Connect GitHub Actions to an authenticated deployment stage for end-to-end CI/CD.
Exercise rollback using an intentionally unhealthy release and document the recovery results.
Add integration/load testing, stronger application authentication and authorization, and security hardening before any real-world deployment.
Create and publish a project-specific architecture diagram and operational runbook.
Portfolio evidence
Recommended screenshots for this repository and a LinkedIn project post:
Terraform-managed AWS networking / VPC resource map.
GitHub Actions CI workflow results after a successful run is verified.
CloudWatch metric, alarm, and logs.
Successful SSM v3 deployment output and running container verification.
> **Cost awareness:** EC2 and other AWS resources may continue incurring charges while running, even if the local development VM is shut down.
