# CrossSell IQ – System Design Document

## 1. Overview
CrossSell IQ is a real-time machine learning platform that predicts cross-sell propensity for Netflix users. It ingests user-movie rating data, engineers features, trains an XGBoost model with hyperparameter tuning, and serves predictions via a FastAPI REST API. Agents receive prioritized recommendations through a glassmorphic dashboard.

## 2. Architecture Diagram
[Netflix Prize Data] ? [Feature Pipeline] ? [Feature Store (SQLite/PostgreSQL)]
?
[Feedback Loop] ? [FastAPI Serving] ? [Model Registry (MLflow)]
?
[Retraining Trigger] ? [Optuna Hyperparameter Tuning] ? [Deploy New Model]
?
[Prometheus Metrics] [SHAP Explanations] [A/B Testing]

## 3. Component Details

### Data Pipeline
- **Source:** Netflix Prize dataset (100M ratings, 480K users)
- **Processing:** Pandas-based feature engineering (RFM, behavioral flags)
- **Validation:** Pandera schema checks before training
- **Store:** SQLite (dev) / PostgreSQL (prod) with versioned feature tables

### Model Training
- **Algorithm:** XGBoost Classifier
- **Hyperparameter Tuning:** Optuna (20 trials, Bayesian optimization)
- **Explainability:** SHAP TreeExplainer
- **Registry:** MLflow with staging/production stages

### Serving
- **Framework:** FastAPI (async, OpenAPI 3.0)
- **Authentication:** JWT with role-based access
- **Rate Limiting:** Token bucket per IP
- **Caching:** Redis for repeated predictions
- **Real-time:** WebSocket for dashboard updates

### Monitoring
- **Metrics:** Prometheus (request count, latency, prediction volume)
- **Alerting:** Prometheus AlertManager rules for high error rate, latency, drift
- **Logging:** Structlog with JSON output, rotated file logs
- **Tracing:** OpenTelemetry (optional)

### Deployment
- **Containers:** Docker, multi-stage builds
- **Orchestration:** Kubernetes with HPA (3–10 replicas)
- **Ingress:** Nginx with TLS termination
- **CI/CD:** GitHub Actions (test ? build ? deploy ? health check)

## 4. Key Design Decisions
- **SQLite for dev, PostgreSQL for prod** – no external dependencies for local demos
- **Optuna over GridSearch** – faster convergence, better metrics
- **Single-page dashboard** – reduces complexity while maintaining professional UX
- **BackgroundTasks over Celery** – no Redis dependency for feedback loop

## 5. Failure Modes & Mitigations
| Failure | Mitigation |
|---------|------------|
| Model returns NaN | Fallback predictor with heuristic rules |
| Feature store unavailable | Cache last-known features in memory |
| High prediction latency | Redis caching, batch prediction endpoint |
| Data drift >30% | Automatic retraining triggered via feedback loop |
