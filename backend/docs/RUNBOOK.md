# Incident Response Runbook

## 1. Model Returns NaN or Zero Predictions
**Symptoms:** Dashboard shows 0.0 propensity for all customers.
**Action:**
1. Check `/api/v1/evaluation/report` – if AUC dropped below 0.5, model is degraded.
2. Roll back to previous model: `cp models/xgb_model_previous.pkl models/xgb_model.pkl`
3. Restart server: `docker restart crosssell-api`
4. Investigate feature drift: `GET /api/v1/monitor/drift`

## 2. High Latency (p99 > 1s)
**Action:**
1. Check Redis cache: `redis-cli ping`
2. Scale up replicas: `kubectl scale deployment crosssell-api --replicas=5`
3. Check database load: `SELECT count(*) FROM features` should complete in <100ms

## 3. Dashboard Not Loading
**Action:**
1. Verify backend: `curl http://localhost:8000/health`
2. Check static files: `ls backend/static/index.html`
3. Check browser console for CORS errors – ensure `ALLOWED_ORIGINS` includes the dashboard domain

## 4. Feedback Loop Not Triggering Retraining
**Action:**
1. Check feedback count: `SELECT count(*) FROM feedback`
2. Verify threshold: should trigger at >= 10 feedbacks
3. Manually trigger: `POST /api/v1/tasks/batch-predict`

## 5. Feature Store Corruption
**Action:**
1. Restore from backup: `python scripts/restore_features.py --date latest`
2. Re-run data pipeline: `python ml_pipeline/data_pipeline_netflix_real.py`
