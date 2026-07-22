# Infrastructure Cost Tracker

A REST API for tracking and analysing cloud infrastructure costs across teams and environments. Built for DevOps and SRE teams who need visibility into cloud spend without relying solely on provider dashboards.

---

## The problem it solves

Cloud bills are unpredictable. Resources get provisioned, forgotten, and left running. Teams don't know what they're spending until the invoice arrives. This API gives engineering teams a central place to register their cloud resources, log cost entries, and surface expensive or inactive resources before they become a problem.

---

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | Flask |
| ORM | Flask-SQLAlchemy |
| Database | PostgreSQL |
| Validation | Marshmallow |
| Auth | Flask-JWT-Extended |
| Containerisation | Docker + docker-compose |
| Orchestration | k3s (self-managed, single-node) |
| IaC | Terraform |
| Cloud | AWS (EC2 + RDS, free-tier) |
| Monitoring | Prometheus + Grafana |
| CI/CD | GitHub Actions |

> **Why not EKS?** The EKS control plane costs $0.10/hour with no free tier, ever (~$73/month). Running [k3s](https://k3s.io/) — a lightweight, production-real Kubernetes distribution — on a single free-tier EC2 instance gives the same `kubectl`/manifest experience without AWS billing for the control plane.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│                  GitHub Actions              │
│   (build → push to ECR → SSH deploy on push) │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│      EC2 t3.micro — single-node k3s          │
│          (public subnet, no NAT)             │
│                                             │
│  ┌──────────────┐    ┌──────────────────┐   │
│  │  Flask API   │    │   Prometheus     │   │
│  │  (pod x1)    │───▶│   + Grafana      │   │
│  └──────┬───────┘    │   (on-demand)    │   │
│         │            └──────────────────┘   │
└─────────┼─────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│         RDS PostgreSQL db.t3.micro           │
│              (single-AZ, free-tier)          │
└─────────────────────────────────────────────┘
          ▲
          │ provisioned by
┌─────────────────────────────────────────────┐
│                 Terraform                    │
│  (VPC, public subnet, EC2, RDS, SGs, IAM)   │
└─────────────────────────────────────────────┘
```

All resources above stay within the AWS free tier for the first 12 months of the account. A `t3.micro` has 1GB RAM, so the Flask app runs as a single replica and Prometheus/Grafana are spun up on demand for a demo rather than left running continuously.

---

## Data model

```
resources
├── id
├── name              e.g. "prod-db-01"
├── type              ec2 / rds / s3 / etc
├── provider          aws / gcp / azure
├── environment       prod / staging / dev
├── team              backend / data / platform
├── owner             email or name
├── region            e.g. eu-west-1
├── is_active         bool
└── created_at

cost_entries
├── id
├── resource_id       FK → resources.id
├── amount            estimated cost
├── currency          EUR / USD
├── period_start      billing period start
├── period_end        billing period end
└── recorded_at
```

One resource has many cost entries — the cost history builds up over time so you can spot trends.

---

## API endpoints

### Health
```
GET  /health                      → API status check
```

### Resources
```
POST   /resources                 → register a new cloud resource
GET    /resources                 → list all resources (filter by team, env, type)
GET    /resources/{id}            → get one resource + cost history
PUT    /resources/{id}            → update resource metadata
DELETE /resources/{id}            → decommission a resource
```

### Costs
```
POST   /resources/{id}/costs      → log a cost entry for a resource
GET    /resources/{id}/costs      → get cost history for a resource
```

### Reports
```
GET    /reports/summary           → total spend grouped by team / environment
GET    /reports/flagged           → resources over cost threshold or inactive
```

---

## Running locally

### Prerequisites
- Docker and docker-compose installed
- Python 3.11+

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/cost-tracker.git
cd cost-tracker
```

### 2. Set up environment variables
```bash
cp .env.example .env
```

Edit `.env` with your values:
```
DATABASE_URL=postgresql://postgres:password@db:5432/costtracker
JWT_SECRET_KEY=your-secret-key-here
```

### 3. Start with Docker
```bash
docker compose up --build
```

The API will be available at `http://localhost:5000`

### 4. Test the health endpoint
```bash
curl http://localhost:5000/health
```

---

## Running tests
```bash
docker compose exec app pytest
```

---

## Deployment

Infrastructure is provisioned with Terraform: a VPC with a **public subnet only** (no NAT Gateway — it bills hourly even when idle), one EC2 `t3.micro` running k3s, and an RDS `db.t3.micro` Postgres instance. k3s is installed on the EC2 instance automatically via a Terraform `user_data` script.

### Prerequisites
- AWS CLI configured (`aws configure`)
- Terraform installed
- kubectl installed (for talking to the k3s cluster remotely)

### Provision infrastructure
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### Deploy to Kubernetes
```bash
kubectl apply -f k8s/
```

### CI/CD
Every push to `main` triggers the GitHub Actions pipeline which:
1. Runs tests
2. Builds and pushes the Docker image to ECR
3. SSHes into the EC2 instance and runs `kubectl apply` against the local k3s cluster

---

## Monitoring

Prometheus scrapes metrics from `/metrics` every 15 seconds. Grafana dashboards show:
- Total spend by team and environment
- Number of active vs inactive resources
- API request rate and latency
- Cost trends over time

Access Grafana at `http://YOUR_EC2_PUBLIC_IP:3000` (default credentials in `k8s/grafana-secret.yaml`). Since the instance is `t3.micro` (1GB RAM), start Prometheus/Grafana only while actively demoing — running them alongside the app continuously will exhaust memory.

---

## Project structure

```
cost-tracker/
├── app/
│   ├── __init__.py
│   ├── models.py              database models
│   ├── database.py            SQLAlchemy setup
│   └── routes/
│       ├── resources.py       resource CRUD endpoints
│       ├── costs.py           cost entry endpoints
│       └── reports.py         summary and flagged reports
├── k8s/
│   ├── deployment.yaml        Flask app deployment
│   ├── postgres.yaml          PostgreSQL StatefulSet
│   ├── prometheus.yaml        Prometheus config
│   └── grafana.yaml           Grafana deployment
├── terraform/
│   ├── main.tf                VPC (public subnet only), EC2, RDS, security groups
│   ├── user_data.sh           installs k3s on the EC2 instance at boot
│   ├── variables.tf
│   └── outputs.tf
├── .github/
│   └── workflows/
│       └── deploy.yml         CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## What I learned building this

- Designing a relational data model with foreign keys and one-to-many relationships
- Containerising a Flask app and connecting it to a Postgres container via Docker networking
- Provisioning cloud infrastructure as code with Terraform
- Deploying to Kubernetes on AWS EKS
- Setting up Prometheus metrics and Grafana dashboards
- Automating deployments with GitHub Actions CI/CD

---

## Roadmap / stretch goals

- [ ] Connect to AWS Cost Explorer API to pull real costs automatically
- [ ] Celery background job to flag zombie resources daily
- [ ] Slack webhook notifications for flagged resources
- [ ] Multi-currency support with live exchange rates
- [ ] Cost forecasting based on historical trends

---

## Author

Built as a portfolio project while learning DevOps and infrastructure engineering.
Targeting SRE and platform engineering roles in Portugal.