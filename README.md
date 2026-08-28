# InfraLedger

A REST API for tracking cloud infrastructure costs, built as a hands-on way to learn production DevOps practices rather than following isolated tutorials.

Engineering teams register their cloud resources, InfraLedger pulls real pricing from AWS and flags what's sitting idle or running over budget.

## What it does

Teams register resources (EC2 instances, RDS databases, S3 buckets, etc.) through the API. InfraLedger looks up the actual AWS list price for each one via the AWS Pricing API, caches it locally with a TTL so it's not re-fetching on every request, and surfaces cost breakdowns by team and environment, plus flags for inactive or expensive resources.

Nothing about the pricing is hardcoded or estimated — it's the real API AWS themselves expose, with the same odd filtering requirements (region names instead of codes, tenancy/OS/capacity filters) you'd hit integrating with it in a real job.

## Stack

Flask API, SQLAlchemy/Alembic, PostgreSQL on RDS. Containerized with Docker, deployed to Amazon EKS. Every piece of infrastructure — VPC, subnets, IAM roles, RDS, ECR, EKS — is provisioned through Terraform with remote state in S3 and locking via DynamoDB. GitHub Actions handles lint/test/build/deploy on every push, authenticating to AWS through OIDC rather than stored access keys. Workload identity inside the cluster uses IRSA, so pods get their own scoped IAM permissions instead of inheriting whatever the node happens to have. Prometheus and Grafana cover metrics and dashboards.

| Layer | Technology |
|---|---|
| API | Python, Flask |
| Database | PostgreSQL (Amazon RDS), SQLAlchemy, Alembic |
| Cost data | AWS Pricing API via boto3 |
| Containers | Docker |
| Orchestration | Kubernetes (Amazon EKS) |
| Infrastructure | Terraform, AWS (VPC, IAM, RDS, ECR, EKS) |
| CI/CD | GitHub Actions, OIDC |
| Monitoring | Prometheus, Grafana |

## API

```
GET    /resources
GET    /resources/{id}
POST   /resources
PATCH  /resources/{id}
DELETE /resources/{id}

GET /costs
GET /costs/monthly
GET /costs/team/{team}
GET /costs/environment/{environment}

GET /resources/inactive
GET /resources/expensive
GET /dashboard

GET /health
GET /metrics
```

## Project layout

```
infraledger/
├── api/
│   ├── app/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── migrations/
│   ├── tests/
│   └── requirements.txt
│
├── terraform/
│   ├── bootstrap/
│   └── vpc/
│
├── kubernetes/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── service-account.yaml
│   └── migration-job.yaml
│
├── monitoring/
│   ├── prometheus/
│   └── grafana/
│
├── .github/workflows/
└── README.md
```

## Deployment

Originally ran on a single EC2 instance behind Nginx with Docker Compose. That got fully built and tested, then retired once the EKS deployment was proven out — running both indefinitely meant two independently-recreatable environments that could silently drift out of sync, which isn't worth the ongoing maintenance for what this project needs. The Compose/Nginx setup is still in the git history.

Now it's EKS end to end: push to main, CI builds and pushes the image to ECR, runs migrations as a Kubernetes Job, then rolls out the new image with a health-checked, zero-downtime deploy.


## Status

Actively built and maintained. See [ROADMAP.md](./ROADMAP.md) for what's done and what's still open — including things I've deliberately left as known gaps rather than pretending they're solved.

## License

MIT