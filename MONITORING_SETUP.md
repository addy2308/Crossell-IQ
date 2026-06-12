# Netflix Cross-Sell API Monitoring & Alerting Setup Guide

## Overview

Complete monitoring stack for the Netflix cross-sell API with:
- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization and dashboarding
- **Alertmanager** - Alert management and routing
- **Node Exporter** - System metrics
- **cAdvisor** - Container metrics

## 🚀 Quick Start

```bash
# 1. Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# 2. Access services
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/netflix2024)
# Alertmanager: http://localhost:9093
# cAdvisor: http://localhost:8080

# 3. Start main application
docker-compose -f docker-compose.prod.yml up -d

# 4. View dashboards in Grafana
```

## 📊 Architecture

```
┌─────────────────────────────────────────────────────┐
│              FastAPI Netflix API                    │
│         (exports /metrics endpoint)                 │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┼──────────┬──────────────┐
        ▼          ▼          ▼              ▼
   ┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
   │Prometheus│cAdvisor│ Node-Exp│Docker
   │ :9090   │ :8080  │ :9100   │ Exporter
   └────────┘ └────────┘ └──────────┘ └──────────┘
        │
        ▼
   ┌─────────────┐
   │  Alertmanager│
   │    :9093    │
   └──────┬──────┘
          │
   ┌──────┴────────┬────────────┬──────────┐
   │ Email         │ Slack      │ Webhooks │
   │ Notifications │ Channels   │ Custom   │
   └───────────────┴────────────┴──────────┘

   Grafana :3000
   (reads from Prometheus, displays alerts)
```

## 🔧 Configuration Files

### 1. **prometheus.yml**
Defines scrape configurations for all data sources:
- Netflix Backend API (:8000)
- PostgreSQL Database (:5432)
- Redis Cache (:6379)
- Node Exporter (:9100)
- Docker metrics

### 2. **alerts.yml**
Prometheus alert rules with 20+ conditions:
- API Performance (response time, error rate)
- Model Performance (latency, errors)
- Database Health (connections, slow queries)
- Redis Cache (miss rate, memory)
- System Resources (CPU, memory, disk)
- Service Availability
- SLA Monitoring

### 3. **alertmanager.yml**
Alert routing and notification configuration:
- Severity-based routing
- Component-specific receivers
- Email notifications
- Slack integration
- Webhook support

### 4. **grafana-dashboard-netflix.json**
Pre-built dashboard showing:
- API Response Time (5m average)
- Error Rate Gauge
- Request Rate
- Response Time Percentiles (p50, p95, p99)
- Status Code Distribution
- Requests by Endpoint

## 📈 Metrics Collected

### FastAPI Metrics
```
http_requests_total - Total requests by status, method, path
http_request_duration_seconds - Request duration histogram
```

### Database Metrics
```
pg_stat_activity_count - Active database connections
pg_settings_max_connections - Max allowed connections
pg_stat_statements_mean_exec_time - Average query execution time
```

### Redis Metrics
```
redis_keyspace_hits_total - Cache hits
redis_keyspace_misses_total - Cache misses
redis_memory_used_bytes - Memory in use
redis_memory_max_bytes - Max memory configured
```

### System Metrics
```
node_cpu_seconds_total - CPU time by mode
node_memory_MemAvailable_bytes - Available memory
node_memory_MemTotal_bytes - Total memory
node_filesystem_avail_bytes - Available disk space
```

## 🚨 Alert Examples

### High Response Time
```yaml
- alert: HighAPIResponseTime
  expr: rate(http_request_duration_seconds_sum[5m]) / 
        rate(http_request_duration_seconds_count[5m]) > 0.5
  for: 5m
  severity: warning
```

### High Error Rate
```yaml
- alert: HighAPIErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 5m
  severity: warning
```

### Database Down
```yaml
- alert: DatabaseDown
  expr: up{job="postgresql"} == 0
  for: 1m
  severity: critical
```

## 🎯 Setting Up Notifications

### Email Setup

1. **Gmail App Passwords** (recommended):
   ```bash
   # Enable 2FA in Gmail
   # Go to: https://myaccount.google.com/apppasswords
   # Generate app-specific password
   ```

2. **Update alertmanager.yml**:
   ```yaml
   global:
     smtp_smarthost: 'smtp.gmail.com:587'
     smtp_auth_username: 'your-email@gmail.com'
     smtp_auth_password: 'your-app-password'
     smtp_from: 'netflix-alerts@gmail.com'
   ```

### Slack Integration

1. **Create Incoming Webhook**:
   - Go to https://api.slack.com/apps
   - Create new app
   - Enable Incoming Webhooks
   - Copy webhook URL

2. **Update alertmanager.yml**:
   ```yaml
   slack_configs:
     - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
       channel: '#netflix-api-alerts'
   ```

### PagerDuty Integration

1. **Create Integration Key**:
   - Go to PagerDuty
   - Create new integration
   - Copy integration key

2. **Update alertmanager.yml**:
   ```yaml
   pagerduty_configs:
     - service_key: 'YOUR_INTEGRATION_KEY'
   ```

## 📊 Using Grafana

### Login
- URL: http://localhost:3000
- Username: admin
- Password: netflix2024

### Import Dashboard
1. Click "+" → "Import"
2. Upload `grafana-dashboard-netflix.json`
3. Select Prometheus as data source
4. View metrics in real-time

### Create Custom Dashboards
1. Click "+" → "Dashboard"
2. Add panels with PromQL queries
3. Examples:
   ```promql
   # Average response time
   rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
   
   # Error rate percentage
   rate(http_requests_total{status=~"5.."}[5m]) * 100
   
   # Requests per second
   rate(http_requests_total[1m])
   ```

## 🔍 Querying Prometheus

### PromQL Examples

**Current request rate:**
```promql
rate(http_requests_total[5m])
```

**95th percentile response time:**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Error rate by endpoint:**
```promql
rate(http_requests_total{status=~"5.."}[5m]) by (path)
```

**Database connection usage:**
```promql
pg_stat_activity_count / pg_settings_max_connections
```

**Redis cache hit rate:**
```promql
rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
```

## 🔄 Load Testing & Monitoring

### Run Load Tests with Monitoring

```bash
# Terminal 1: Start monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Terminal 2: Start application
docker-compose -f docker-compose.prod.yml up -d

# Terminal 3: Run load test
cd tests
python load_test_runner.py --scenario stress --headless

# Terminal 4: Monitor metrics
# Open Grafana dashboard: http://localhost:3000/d/netflix-api
```

### Watch Metrics in Real-time

```bash
# Prometheus query API
curl 'http://localhost:9090/api/v1/query?query=rate(http_requests_total[5m])'

# Get active alerts
curl 'http://localhost:9090/api/v1/alerts'
```

## 🛠️ Troubleshooting

### Prometheus not scraping metrics

1. Check if API exports /metrics:
   ```bash
   curl http://localhost:8000/metrics
   ```

2. Verify prometheus.yml configuration

3. Check Prometheus targets:
   ```
   http://localhost:9090/targets
   ```

### Grafana dashboard empty

1. Verify Prometheus data source:
   - Configuration → Data Sources → Prometheus
   - Click "Test" button

2. Check if data exists:
   - Go to Prometheus: http://localhost:9090
   - Graph tab → Enter PromQL query

### Alerts not firing

1. Check alert rules:
   ```
   http://localhost:9090/alerts
   ```

2. Verify alert manager is running:
   ```bash
   curl http://localhost:9093/-/healthy
   ```

3. Check alertmanager logs:
   ```bash
   docker logs alertmanager-netflix -f
   ```

## 📋 Production Checklist

- [ ] Configure email/Slack notifications
- [ ] Set up escalation policies
- [ ] Create runbooks for critical alerts
- [ ] Test alert routing and notifications
- [ ] Configure backup data storage
- [ ] Set up log aggregation (ELK stack)
- [ ] Monitor Prometheus storage usage
- [ ] Set up retention policies (15 days recommended)
- [ ] Document runbooks for each alert
- [ ] Schedule regular backups of Grafana dashboards

## 🔐 Security Hardening

### Protect Prometheus
```bash
# Add reverse proxy with authentication
# Use nginx with htpasswd
```

### Protect Grafana
```yaml
# Change default password
# Enable LDAP/OIDC authentication
# Use HTTPS with valid certificates
```

### Protect Alertmanager
```bash
# Don't expose directly to internet
# Use VPN or bastion host
```

## 📚 References

- Prometheus Docs: https://prometheus.io/docs/
- Grafana Docs: https://grafana.com/docs/grafana/latest/
- PromQL Guide: https://prometheus.io/docs/prometheus/latest/querying/basics/
- Alertmanager Docs: https://prometheus.io/docs/alerting/latest/

---

**Last Updated:** June 5, 2026  
**Version:** 1.0  
**Maintainer:** Netflix Team
