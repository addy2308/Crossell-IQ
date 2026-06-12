# Load Testing Guide for Netflix Cross-Sell API

## Overview

Complete load testing suite for Netflix API with multiple testing frameworks and scenarios.

## 🚀 Quick Start

### 1. **Pytest Load Tests** (Recommended for development)

```bash
# Install dependencies
pip install pytest requests

# Run all tests
pytest tests/test_api_load.py -v -s

# Run specific test
pytest tests/test_api_load.py::TestAPIPerformance::test_single_prediction_response_time -v

# Generate report
pytest tests/test_api_load.py --tb=short -v --html=report.html
```

### 2. **Locust Load Tests** (Recommended for production testing)

```bash
# Install Locust
pip install locust

# Start with web UI
locust -f tests/locustfile.py -H http://localhost:8000

# Run headless with predefined scenario
python tests/load_test_runner.py --scenario stress --headless

# Custom parameters
python tests/load_test_runner.py --users 50 --spawn-rate 5 --duration 5m
```

## 📋 Test Scenarios

### Pytest Tests

#### Performance Tests
- **test_single_prediction_response_time**: Verifies single prediction < 100ms
- **test_batch_prediction_response_time**: Verifies batch prediction < 500ms for 10 customers
- **test_model_status_response_time**: Verifies model status < 50ms
- **test_concurrent_single_predictions**: Tests 20 concurrent predictions
- **test_concurrent_batch_predictions**: Tests 10 concurrent batch predictions

#### Reliability Tests
- **test_model_status_consistently_available**: 50 requests, must have 99%+ availability
- **test_prediction_consistency**: Same input produces same output (5 iterations)

#### Error Handling Tests
- **test_invalid_customer_data**: Graceful handling of invalid JSON
- **test_missing_required_fields**: Validation of required fields

### Locust Scenarios

#### Light Load Test
```bash
python tests/load_test_runner.py --scenario light
# 5 users, 1 user/sec spawn rate, 2 minute duration
```

#### Moderate Load Test
```bash
python tests/load_test_runner.py --scenario moderate
# 20 users, 2 users/sec spawn rate, 5 minute duration
# Simulates normal operating conditions
```

#### High Load Test
```bash
python tests/load_test_runner.py --scenario high
# 50 users, 5 users/sec spawn rate, 5 minute duration
# Peak load simulation
```

#### Stress Test
```bash
python tests/load_test_runner.py --scenario stress
# 100 users, 10 users/sec spawn rate, 3 minute duration
# Breaking point test
```

#### Spike Test
```bash
python tests/load_test_runner.py --scenario spike
# 200 users, 50 users/sec spawn rate, 2 minute duration
# Sudden traffic spike
```

#### Endurance Test
```bash
python tests/load_test_runner.py --scenario endurance
# 30 users, 3 users/sec spawn rate, 30 minute duration
# Memory leak detection
```

## 🔧 Custom Load Test

### Using load_test_runner.py

```bash
# Basic test
python tests/load_test_runner.py --host http://localhost:8000 --users 25 --spawn-rate 5 --duration 3m

# With stress test configuration
python tests/load_test_runner.py --users 100 --spawn-rate 20 --duration 5m --type stress

# List all scenarios
python tests/load_test_runner.py --list-scenarios

# Headless execution
python tests/load_test_runner.py --users 50 --headless
```

### Locust Web UI

```bash
# Start Locust with web interface
locust -f tests/locustfile.py -H http://localhost:8000

# Open browser to http://localhost:8089
# Configure users and spawn rate in UI
# Start swarming
```

## 📊 Test Execution Workflow

### Pre-Test Setup

```bash
# 1. Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# 2. Start application
docker-compose -f docker-compose.prod.yml up -d

# 3. Verify API is ready
curl http://localhost:8000/api/netflix/model/status

# 4. Check monitoring dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
```

### Execute Pytest Tests

```bash
# Full test suite with detailed output
pytest tests/test_api_load.py -v -s --tb=long

# Performance tests only
pytest tests/test_api_load.py::TestAPIPerformance -v

# Reliability tests only
pytest tests/test_api_load.py::TestAPIReliability -v

# Generate HTML report
pytest tests/test_api_load.py -v --html=reports/pytest_report.html

# Generate JUnit XML for CI/CD
pytest tests/test_api_load.py -v --junit-xml=reports/junit.xml
```

### Execute Locust Tests

```bash
# Terminal 1: Start monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Terminal 2: Start application
docker-compose -f docker-compose.prod.yml up -d

# Terminal 3: Run load test
python tests/load_test_runner.py --scenario moderate

# Terminal 4: Watch metrics in Grafana
# http://localhost:3000/d/netflix-api
```

## 📈 Interpreting Results

### Pytest Results

```bash
$ pytest tests/test_api_load.py -v

test_single_prediction_response_time PASSED                    [ 11%]
test_batch_prediction_response_time PASSED                     [ 22%]
test_model_status_response_time PASSED                         [ 33%]
test_concurrent_single_predictions PASSED                      [ 44%]
test_concurrent_batch_predictions PASSED                       [ 55%]
test_model_status_consistently_available PASSED                [ 66%]
test_prediction_consistency PASSED                             [ 77%]
test_invalid_customer_data PASSED                              [ 88%]
test_missing_required_fields PASSED                            [100%]

=== 9 passed in 12.45s ===
```

**What to look for:**
- ✅ All tests passing
- ⏱️ Response times within thresholds
- 📊 Availability >= 99%
- ✓ Consistency maintained under load

### Locust Results

**Metrics in Locust Web UI:**

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Response Time (median) | < 50ms | 50-100ms | > 100ms |
| Response Time (95%) | < 200ms | 200-500ms | > 500ms |
| Error Rate | < 0.1% | 0.1-1% | > 1% |
| Requests/sec | Stable | Slightly varying | Dropping |
| Success Rate | > 99.9% | 99-99.9% | < 99% |

**Example Locust Output:**

```
Type        Name                          # reqs  # fails | Median  95%   | Avg     Min     Max
--------    ----                          ------  ------  |------  ------  |------  ------  ------
POST        /api/netflix/predict          1050    5       | 45     120     | 52      10      250
POST        /api/netflix/predict/batch    350     2       | 110    450     | 125     40      580
GET         /api/netflix/model/status     700     0       | 25     65      | 28      8       95
GET         /api/netflix/model/info       350     0       | 30     70      | 32      10      110
POST        /api/netflix/health-check     350     1       | 20     50      | 23      7       85
--------    ----                          ------  ------  |------  ------  |------  ------  ------
Total       5                             2800    8       | 50     150     | 72      7       580

Requests/sec: 225
Failure rate: 0.29%
```

## 🔍 Performance Analysis

### Key Performance Indicators (KPIs)

1. **Response Time**
   - Target: < 100ms (p95)
   - Acceptable: < 200ms (p95)
   - Critical: > 500ms (p95)

2. **Error Rate**
   - Target: < 0.1%
   - Acceptable: 0.1-0.5%
   - Critical: > 1%

3. **Throughput**
   - Target: > 100 req/s
   - Acceptable: > 50 req/s
   - Critical: < 20 req/s

4. **Availability**
   - Target: 99.99%
   - Acceptable: 99.9%
   - Critical: < 99%

### Bottleneck Identification

**High Response Time:**
```promql
# In Grafana/Prometheus
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Check specific endpoints
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{path="/api/netflix/predict/batch"}[5m]))
```

**High Error Rate:**
```promql
rate(http_requests_total{status=~"5.."}[5m])
```

**High CPU Usage:**
```promql
rate(node_cpu_seconds_total{mode="system"}[5m])
```

**High Memory Usage:**
```promql
node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes
```

## 🚀 Optimization Strategies

### If Response Time is High

1. **Database Optimization**
   - Add indexes on frequently queried columns
   - Optimize slow queries with EXPLAIN ANALYZE
   - Increase connection pool size

2. **Model Optimization**
   - Profile model.predict() with cProfile
   - Cache predictions for identical inputs
   - Batch predictions when possible

3. **Backend Optimization**
   - Increase number of Uvicorn workers
   - Use FastAPI dependency caching
   - Implement response caching with Redis

4. **Infrastructure**
   - Allocate more CPU/memory to containers
   - Use load balancing across API instances
   - Enable gzip compression

### If Error Rate is High

1. **Application Debugging**
   - Check application logs: `docker logs backend-netflix`
   - Enable request logging in FastAPI
   - Add detailed error tracking

2. **Resource Issues**
   - Check disk space: `df -h`
   - Monitor memory: `free -h`
   - Check database connections

3. **Dependency Issues**
   - Verify database connectivity
   - Check Redis availability
   - Monitor external API calls

### If Throughput is Low

1. **Increase Concurrency**
   - Increase number of Uvicorn workers
   - Increase FastAPI max_connections
   - Scale horizontally with multiple instances

2. **Reduce Latency**
   - Implement caching
   - Batch requests
   - Optimize database queries

3. **Connection Management**
   - Increase connection pool size
   - Enable connection pooling in Redis
   - Use persistent connections

## 📊 Continuous Load Testing

### GitHub Actions Workflow

```yaml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Run daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install pytest locust requests
      
      - name: Run Pytest load tests
        run: |
          pytest tests/test_api_load.py -v --junit-xml=reports/junit.xml
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: reports/
```

## 📝 Reporting

### Generate Test Report

```bash
# HTML report from Pytest
pytest tests/test_api_load.py --html=reports/load_test_report.html

# JSON output for parsing
pytest tests/test_api_load.py --json=reports/results.json

# Locust CSV results
locust -f tests/locustfile.py -H http://localhost:8000 --csv=reports/locust
```

### Sample Report Template

```markdown
# Load Test Report - Netflix Cross-Sell API

**Date:** 2026-06-05  
**Test Duration:** 5 minutes  
**Concurrent Users:** 50  
**Test Scenario:** Moderate Load

## Summary
- ✅ All endpoints operational
- ✅ Response times within SLA
- ✅ Error rate < 0.1%
- ⚠️ Peak memory usage at 87%

## Metrics
- Requests: 15,000
- Success Rate: 99.87%
- Avg Response Time: 45ms
- P95 Response Time: 120ms
- P99 Response Time: 280ms

## Bottlenecks
- Batch endpoint shows 20% higher latency under load
- Database connection pool at 75% capacity

## Recommendations
1. Increase DB connection pool to 50
2. Implement result caching for batch predictions
3. Vertical scale API instances
```

## 🔗 Integration with CI/CD

### GitLab CI

```yaml
load-test:
  stage: test
  script:
    - pip install pytest locust requests
    - pytest tests/test_api_load.py -v --junit-xml=junit.xml
  artifacts:
    reports:
      junit: junit.xml
    paths:
      - reports/
```

## 📚 Resources

- Pytest Documentation: https://docs.pytest.org/
- Locust Documentation: https://locust.io/
- FastAPI Performance: https://fastapi.tiangolo.com/deployment/
- XGBoost Optimization: https://xgboost.readthedocs.io/

---

**Last Updated:** June 5, 2026  
**Version:** 1.0  
**Maintained By:** DevOps Team
