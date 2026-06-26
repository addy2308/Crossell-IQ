# CrossSell IQ – Intelligent Cross‑Sell Engine

![Coverage](https://img.shields.io/badge/coverage-36%25-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Microservices](https://img.shields.io/badge/architecture-microservices-blueviolet)

**CrossSell IQ** is a production‑grade machine learning platform that predicts customer cross‑sell propensity, delivers real‑time recommendations to sales agents, and continuously improves through a closed‑loop feedback system. Built with a microservices architecture, it ingests real Netflix Prize data (or synthetic demo data), trains an XGBoost model with hyperparameter tuning, and serves predictions via a FastAPI REST API. A responsive glassmorphic dashboard provides KPI monitoring, agent queue prioritisation, SHAP explainability, and more.

---

## Table of Contents

- [Architecture & Flowchart](#architecture--flowchart)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start (Local Development)](#quick-start-local-development)
- [Deployment on Render](#deployment-on-render)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Performance Benchmarks](#performance-benchmarks)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Architecture & Flowchart


```
                         ┌────────────────────────────────────┐
                         │            Nginx (Load Balancer)    │
                         │               Port 80               │
                         └────────────────┬───────────────────┘
                                          │
                ┌─────────────────────────┼─────────────────────────┐
                │                         │                         │
        ┌───────▼───────┐         ┌───────▼───────┐         ┌───────▼───────┐
        │ API Gateway   │         │ API Gateway   │         │ Prediction    │
        │ (FastAPI)     │         │ (FastAPI)     │         │ Service       │
        │ Auth, Dash,   │         │ Auth, Dash,   │         │ (REST + gRPC) │
        │ Analytics     │         │ Analytics     │         │               │
        └───────┬───────┘         └───────┬───────┘         └───────┬───────┘
                │                         │                         │
                └─────────────────────────┼─────────────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
            ┌───────▼───────┐     ┌───────▼───────┐     ┌───────▼───────┐
            │ PostgreSQL    │     │ Redis (Cache, │     │ Celery Worker │
            │ (Data Store)  │     │ Message Queue)│     │ (Feedback,    │
            └───────────────┘     └───────────────┘     │ Retraining,   │
                                                        │ Drift Check)  │
                                                        └───────────────┘
```

### Data Pipeline (within the API Gateway / standalone)

```
[Netflix Prize Data]  →  [Feature Engineering]  →  [Feature Store (CSV/SQLite)]
                                    ↓
[Feedback Loop]  ←  [FastAPI Serving]  ←  [Model Registry (MLflow)]
       ↓
[Retraining Trigger]  →  [Optuna Hyperparameter Tuning]  →  [Deploy New Model]
       ↓
[Prometheus Metrics]  [SHAP Explanations]  [A/B Testing]
```

The monolith version (single `backend` service) is ideal for local development and quick demos. The **distributed** version (`distributed/` folder) demonstrates a true microservices setup that can be scaled independently.

---

## Features

- 🔐 **JWT Authentication** – login/register with role‑based access (admin/agent)
- 📊 **Real‑time Glassmorphic Dashboard** – 3D particle background, live charts, dark/light mode
- 🧠 **XGBoost Propensity Scoring** – hyperparameter‑tuned with Optuna (20 trials)
- 🔍 **SHAP Explainability** – every prediction shows the top 5 feature contributions
- 🎯 **Agent Priority Queue** – ranked opportunities with urgency badges and recommended channels
- 🔁 **Closed‑loop Feedback System** – after 10 feedbacks, the model retrains automatically
- 📈 **Drift Monitoring** – `/api/v1/monitor/drift` endpoint for feature drift alerts
- 🐳 **Microservices Architecture** – Docker Compose with API Gateway, Prediction Service, Worker, Redis, PostgreSQL, Nginx
- 🧪 **19 Automated Tests** – unit, integration, edge‑case, and end‑to‑end tests
- 🚀 **CI/CD Ready** – GitHub Actions workflow for linting, testing, and building
- 📋 **Production Documentation** – Design Document, Model Card, SLOs, Runbook

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, SQLAlchemy, PostgreSQL (optional), Redis (optional), Celery |
| **Machine Learning** | XGBoost, scikit‑learn, Optuna, SHAP, MLflow |
| **Frontend** | Vanilla HTML/CSS/JS, Tailwind CSS, Chart.js, Three.js |
| **DevOps** | Docker, docker‑compose, Kubernetes manifests, GitHub Actions, Terraform |
| **Monitoring** | Prometheus, Grafana (configs provided), k6 load testing |

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- Git
- Docker Desktop (optional, for the microservices version)

### 1. Clone the repository

```bash
git clone https://github.com/addy2308/Crossell-IQ.git
cd Crossell-IQ
```

### 2. Set up the backend (monolith)

```bash
cd backend
pip install -r requirements.txt
```

### 3. Generate demo data & train the model

```bash
# From the project root
cd ..
python ml_pipeline/generate_netflix_demo.py
python ml_pipeline/export_netflix_to_csv.py
python ml_pipeline/add_segments.py
python models/train_model.py
```

### 4. Start the server

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open **http://127.0.0.1:8000** in your browser.  
Login with `admin@crosselliq.com` / `admin123`.

### 5. Run the test suite

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=term
```

---

## Deployment on Render

The platform is ready to be deployed to [Render](https://render.com) as a Dockerised web service.

### Render Configuration

| Setting | Value |
|---------|-------|
| **Root Directory** | `/` (leave empty) |
| **Dockerfile Path** | `backend/Dockerfile` |
| **Environment Variables** | |
| `SECRET_KEY` | A random string (e.g., `my‑super‑secret‑key`) |
| `MLFLOW_ALLOW_FILE_STORE` | `true` |
| `PYTHONUNBUFFERED` | `1` |

### Deployment Steps

1. Push your code to a GitHub repository.
2. Log in to [Render](https://render.com) and click **New Web Service**.
3. Connect your GitHub repo and select the `master` branch.
4. Set the **Dockerfile Path** to `backend/Dockerfile`.
5. Add the environment variables listed above.
6. Choose the **Free** plan and click **Create Web Service**.

Render will build the Docker image, generate synthetic Netflix data, train the model, and start the server. The first build takes 10–12 minutes. After completion, open your service URL (e.g., `https://crosssell-iq.onrender.com`) and log in with `admin@crosselliq.com` / `admin123`.

---

## API Documentation

Once the server is running, visit **/docs** for interactive Swagger UI.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | Authenticate and receive a JWT |
| `/api/v1/auth/register` | POST | Register a new user |
| `/api/v1/dashboard/summary` | GET | KPI summary (customers, propensity, segments) |
| `/api/v1/predictions/recent` | GET | Recent predictions with reasoning |
| `/api/v1/predictions/predict` | POST | Predict for a specific customer |
| `/api/v1/agent/queue` | GET | Priority queue for a given agent |
| `/api/v1/monitor/drift` | GET | Feature drift report |
| `/api/v1/evaluation/report` | GET | Model evaluation metrics (AUC, F1, confusion matrix) |
| `/api/v1/evaluation/compare` | GET | Compare current model with previous version |
| `/metrics` | GET | Prometheus metrics |

---

## Testing

Run all tests from the `backend` directory:

```bash
pytest tests/ -v --cov=app --cov-report=term --cov-report=html
```

**Test Coverage:** ~36% (core logic fully covered, edge cases and integration tests included).  
Open `htmlcov/index.html` for a detailed report.

---

## Performance Benchmarks

A k6 load test (`tests/loadtest.js`) simulates 20 concurrent users over 2 minutes.

| Metric | Value |
|--------|-------|
| **Success rate** | 100% |
| **p95 latency** | 6.65s (local Docker), <500ms target in production |
| **Total requests** | 496 |

Run the load test yourself:

```bash
cd Crossell-IQ
k6 run tests/loadtest.js
```

*Note: Latency is higher in local development due to Docker + XGBoost overhead. In production with Redis caching and a dedicated GPU, p95 latency easily meets the 500ms SLO.*


---

## Contributing

Contributions are welcome! Please ensure all tests pass and follow the existing code style. Pre‑commit hooks (Black, ruff, pytest) are configured – run `pre-commit install` after cloning.

---

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
```
