# Service Level Objectives (SLOs)

## 1. Availability
- **Target:** 99.9% uptime monthly
- **Measurement:** UptimeRobot ping on `/health` every minute

## 2. Latency
- **Target:** p95 < 200ms, p99 < 500ms for prediction endpoints
- **Measurement:** Prometheus histogram `http_request_duration_seconds`

## 3. Accuracy
- **Target:** AUC >= 0.80, F1-score >= 0.75 on test set
- **Measurement:** Monthly evaluation report on holdout data

## 4. Data Freshness
- **Target:** Features updated within 24 hours of new data arrival
- **Measurement:** `last_trained` field in `/dashboard/summary`

## 5. Error Budget
- **Allowed 0.1% downtime per month (~43 minutes)**
- **If error budget is exhausted, freeze new deployments until stability is restored**
