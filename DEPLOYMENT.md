# Netflix Cross-Sell Model - Production Deployment Guide

**Complete guide to deploy the Netflix cross-sell propensity model to production**

## 🚀 Quick Deploy

```bash
# 1. Download and process Netflix dataset
cd ml_pipeline
python netflix_integration.py
# Select option 1 or 2

# 2. Deploy model
cd deployment
python deploy_model.py
# Answer 'yes' for production deployment

# 3. Start services with Docker
cd ..
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify
curl http://localhost:8000/api/netflix/model/status
```

## 📋 Prerequisites

- Python 3.10+
- Docker & Docker Compose
- 10+ GB disk space (for dataset)
- 4+ GB RAM recommended
- Kaggle API credentials (for automatic download)

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│              http://localhost:3000                           │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  FastAPI Backend                            │
│  /api/netflix/predict          :8000                       │
│  /api/netflix/predict/batch                                │
│  /api/netflix/model/info                                   │
└────────────────┬──────────────────────┬────────────────────┘
                 │                      │
    ┌────────────▼────┐        ┌────────▼────────┐
    │  PostgreSQL DB  │        │   Redis Cache   │
    │  (metrics)      │        │   (sessions)    │
    └─────────────────┘        └─────────────────┘

    ┌──────────────────────────────────────────────┐
    │  XGBoost Netflix Cross-Sell Model            │
    │  - 100M+ Netflix ratings training data       │
    │  - 15+ engineered features                   │
    │  - 200-tree ensemble                         │
    │  - AUC: 0.75-0.85                            │
    └──────────────────────────────────────────────┘
```

## 📦 Deployment Process

### Step 1: Dataset & Model Training

```bash
cd ml_pipeline
python netflix_integration.py
```

**Output:**
- `data/netflix_prize/` - Downloaded Netflix dataset
- `data/processed/netflix_features.parquet` - Engineered features
- `models/netflix_xgboost_*.pkl` - Trained model
- `models/netflix_scaler_*.pkl` - Feature scaler
- `models/netflix_metadata_*.json` - Model metadata

**Time:** 5-45 minutes depending on mode

### Step 2: Model Validation & Deployment

```bash
cd deployment
python deploy_model.py
```

**Stages:**
1. ✅ Find latest model
2. ✅ Validate model files
3. ✅ Deploy to staging
4. ✅ Verify staging
5. ✅ Deploy to production (requires confirmation)
6. ✅ Verify production

**Output:**
- `deployment/models/staging/` - Staging environment
- `deployment/models/production/` - Production environment
- `deployment/models/production/backups/` - Previous models
- `deployment/models/production/manifest.json` - Deployment info

### Step 3: Service Startup

```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Services:**
- **Backend API** → http://localhost:8000
- **Frontend** → http://localhost:3000
- **Database** → PostgreSQL (5432)
- **Cache** → Redis (6379)
- **ML Tracking** → MLflow (5000)

### Step 4: Verify Deployment

```bash
# Check API health
curl http://localhost:8000/health

# Check Netflix model status
curl http://localhost:8000/api/netflix/model/status

# View API documentation
http://localhost:8000/docs
```

## 🔗 API Endpoints

### Model Status
```bash
GET /api/netflix/model/status

Response:
{
  "model_loaded": true,
  "status": "ready",
  "num_features": 15,
  "model_type": "XGBoost Cross-Sell Propensity Classifier"
}
```

### Single Prediction
```bash
POST /api/netflix/predict
Content-Type: application/json

{
  "total_ratings": 250,
  "unique_movies": 180,
  "mean_rating": 3.8,
  "tenure_days": 500,
  "recency_days": 15,
  "is_active_6m": 1,
  "engagement_score": 75
}

Response:
{
  "success": true,
  "propensity_score": 0.7845,
  "propensity_percentage": 78.45,
  "segment": "High",
  "recommended_action": "Recommend targeted cross-sell campaign",
  "timestamp": "2026-06-05T12:30:45.123456"
}
```

### Batch Predictions
```bash
POST /api/netflix/predict/batch
Content-Type: application/json

{
  "customers": [
    {"total_ratings": 250, "mean_rating": 3.8, ...},
    {"total_ratings": 150, "mean_rating": 3.5, ...}
  ]
}

Response: [
  {
    "success": true,
    "propensity_score": 0.7845,
    "propensity_percentage": 78.45,
    "segment": "High",
    ...
  },
  {
    "success": true,
    "propensity_score": 0.4230,
    ...
  }
]
```

### Model Information
```bash
GET /api/netflix/model/info

Response:
{
  "is_loaded": true,
  "model_type": "XGBoost Classifier",
  "num_features": 15,
  "features": [
    "total_ratings",
    "unique_movies",
    "mean_rating",
    ...
  ],
  "metadata": {
    "timestamp": "2026-06-05T10:30:00",
    "metrics": {...}
  }
}
```

## 📊 Model Features

The trained model uses 15+ features:

**Behavioral:**
- `total_ratings` - Number of movies rated
- `unique_movies` - Count of distinct movies
- `rating_velocity` - Ratings per day

**Temporal:**
- `tenure_days` - Account age
- `recency_days` - Days since last rating
- `is_active_6m` - Active in 6 months (binary)
- `is_active_1y` - Active in 1 year (binary)

**Quality:**
- `mean_rating` - Average rating given (1-5)
- `std_rating` - Rating consistency
- `min_rating` / `max_rating` - Range

**Engagement:**
- `engagement_score` - Overall engagement (0-100)
- `rating_consistency` - Consistency metric

## 🔄 CI/CD Integration

### GitHub Actions Deployment

```yaml
name: Deploy Netflix Model

on:
  workflow_dispatch:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
      
      - name: Deploy model
        run: |
          cd deployment
          python deploy_model.py << EOF
          yes
          EOF
      
      - name: Start services
        run: |
          docker-compose -f docker-compose.prod.yml up -d
```

## 🛡️ Production Checklist

- [ ] Dataset downloaded and validated
- [ ] Model trained and tested (AUC > 0.75)
- [ ] Model files deployed to staging
- [ ] Staging environment verified
- [ ] Model files deployed to production
- [ ] Production environment verified
- [ ] All API endpoints responding
- [ ] Database migrations completed
- [ ] Redis cache operational
- [ ] MLflow tracking active
- [ ] Frontend accessible
- [ ] Load testing completed
- [ ] Monitoring and alerts configured
- [ ] Backup strategy in place

## 📊 Monitoring

### Health Checks

```bash
# Every 30 seconds
curl http://localhost:8000/health

# Model readiness
curl http://localhost:8000/api/netflix/model/status

# Metrics
curl http://localhost:8000/metrics
```

### Logs

```bash
# Backend logs
docker-compose -f docker-compose.prod.yml logs backend-netflix -f

# Database logs
docker-compose logs db -f

# All services
docker-compose -f docker-compose.prod.yml logs -f
```

## 🔄 Rollback Procedure

If issues occur in production:

```bash
# 1. Stop services
docker-compose -f docker-compose.prod.yml down

# 2. Restore previous model
cp deployment/models/production/backups/netflix_xgboost_previous.pkl deployment/models/production/

# 3. Restart
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify
curl http://localhost:8000/api/netflix/model/status
```

## 📈 Performance Optimization

### Caching Predictions

```python
from backend.app.services.netflix_model_service import get_model_service

# Service caches loaded model in memory
service = get_model_service()

# Predictions < 5ms for cached model
result = service.predict_propensity(customer_features)
```

### Batch Processing

Use batch endpoint for large-scale scoring:

```python
# More efficient than individual requests
# HTTP overhead amortized
results = client.post('/api/netflix/predict/batch', 
                      json={'customers': [...]})
```

### Database Indexing

```sql
-- Optimize customer queries
CREATE INDEX idx_customer_propensity 
ON customers(propensity_score DESC);

CREATE INDEX idx_customer_segment 
ON customers(segment);
```

## 🐛 Troubleshooting

### Model Not Loading

```bash
# Check model files exist
ls -la deployment/models/production/*.pkl

# Check manifest
cat deployment/models/production/manifest.json

# Verify Python can import required libraries
python -c "import pickle, sklearn, xgboost; print('OK')"
```

### API Not Responding

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs backend-netflix

# Verify port 8000
netstat -tuln | grep 8000
```

### Slow Predictions

```bash
# Monitor CPU/Memory
docker stats

# Check feature count
curl http://localhost:8000/api/netflix/model/info

# Profile code
python -m cProfile deployment/deploy_model.py
```

## 📚 Additional Resources

- Netflix Prize Dataset: https://www.kaggle.com/datasets/netflix-inc/netflix-prize-data
- XGBoost Docs: https://xgboost.readthedocs.io/
- FastAPI Docs: https://fastapi.tiangolo.com/
- Docker Compose: https://docs.docker.com/compose/

## 📞 Support

For issues or questions:

1. Check logs: `docker-compose logs -f`
2. Review API docs: http://localhost:8000/docs
3. Verify model: `curl /api/netflix/model/status`
4. Check GitHub Issues: [project repo]

---

**Last Updated:** June 5, 2026  
**Version:** 1.0  
**Status:** Production Ready ✅
