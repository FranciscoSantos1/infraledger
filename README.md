# InfraLedger

A production-inspired REST API built to learn modern DevOps practices by designing, deploying, monitoring and automating a cloud-native application.

InfraLedger lets engineering teams register cloud infrastructure resources, estimate their monthly costs, and identify unused or expensive resources before they become a problem.

## Highlights

- **Real cost data, not mocked.** Pulls live prices from the AWS Pricing API and caches them locally — the numbers are real.
- **Zero static AWS credentials, anywhere.** CI authenticates to AWS via GitHub OIDC federation; workloads authenticate via IAM roles (EC2/EKS instance roles) — no long-lived access keys stored anywhere in this repo or in CI.
- **Full infrastructure as code.** Every AWS resource — VPC, RDS, ECR, IAM, EKS — is provisioned through Terraform with remote state and locking (S3 + DynamoDB), not clicked together in a console.
- **Deployed on Kubernetes (Amazon EKS)**, with self-healing rolling deployments behind a Kubernetes Service.
- **Least-privilege IAM throughout**, scoped per workload rather than one broad credential shared everywhere.

---

## Why this project?

Most people learn Docker, Kubernetes, or Terraform through isolated tutorials.

InfraLedger takes a different approach: everything is integrated into one realistic application that evolved from a simple Flask API running locally into a production-style deployment on AWS — complete with Infrastructure as Code, CI/CD, and Kubernetes.

The goal is to simulate the technologies and workflows used by real DevOps teams, one phase at a time.

---

## How costs are calculated

Cost estimates aren't hardcoded. InfraLedger calls the **real AWS Pricing API** (via `boto3`) to fetch live list prices for the registered resources, caches them locally, and refreshes on a schedule — so the numbers reflect actual AWS pricing, not guesses.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| API | Flask |
| Database | PostgreSQL (Amazon RDS) |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Cost Data | AWS Pricing API (`boto3`) |
| Containerisation | Docker |
| Local Orchestration | Docker Compose |
| Infrastructure as Code | Terraform |
| Container Orchestration | Kubernetes (Amazon EKS) |
| Cloud | AWS (VPC, EC2, RDS, ECR, IAM, EKS) |
| CI/CD | GitHub Actions (OIDC-authenticated) |
| Version Control | Git |

---

## API