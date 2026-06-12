# 🚀 NBA Cross-Sell Intelligence Engine

**Full-Stack AI/ML Project** — Predictive customer modeling for upselling and cross-selling, powered by XGBoost, SHAP, and real-time agent activation.

## 🏗 Architecture
- **Frontend:** React + Material UI + Recharts
- **Backend:** FastAPI + PostgreSQL + Redis
- **ML:** XGBoost + K-Prototypes + SHAP + MLflow
- **Infrastructure:** Docker Compose

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

### Option 1: Docker (Recommended)
```bash
# Clone and navigate to project
cd cross_sell_engine

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Access:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000/docs
# - MLflow: http://localhost:5000
### Mutation Testing
Mutation testing is configured via `mutmut`. On Windows, please run inside WSL:
`mutmut run --paths-to-mutate app/ml/predictor.py`
