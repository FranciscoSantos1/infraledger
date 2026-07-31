# InfraLedger

A production-inspired REST API built to learn modern DevOps practices by designing, deploying, monitoring and automating a cloud-native application.

InfraLedger lets engineering teams register cloud infrastructure resources, estimate their monthly costs, and identify unused or expensive resources before they become a problem.


## Why this project?

Most people learn Docker, Kubernetes, or Terraform through isolated tutorials.

InfraLedger takes a different approach: everything is integrated into one realistic application that evolves from a simple Flask API running locally into a production-style deployment on AWS — complete with Infrastructure as Code, CI/CD, monitoring, and Kubernetes.

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
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Cost Data | AWS Pricing API (`boto3`) |
| Containerisation | Docker |
| Local Orchestration | Docker Compose |
| Infrastructure as Code | Terraform |
| Kubernetes | k3s |
| Cloud | AWS |
| Monitoring | Prometheus + Grafana |
| CI/CD | GitHub Actions |
| Reverse Proxy | Nginx |
| Version Control | Git |

---

## Planned API

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

---

## Project Structure

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
├── docker/
├── terraform/
├── kubernetes/
│
├── monitoring/
│   ├── prometheus/
│   └── grafana/
│
├── .github/
│   └── workflows/
│
├── docs/
├── scripts/
│
├── README.md
└── ROADMAP.md
```

---

## Deployment Journey

```
Local Development → Flask API → Docker → Docker Compose → GitHub Actions
→ Terraform → AWS EC2 → k3s → Prometheus → Grafana
```

---

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- An AWS account (free tier is enough) with a read-only IAM user for the Pricing API
- Terraform (from Phase 6 onward)

---

## Status

🚧 Work in Progress — built incrementally as a learning platform for DevOps and Cloud Engineering.

Full breakdown of milestones in [`ROADMAP.md`](./ROADMAP.md).

---

## License

MIT