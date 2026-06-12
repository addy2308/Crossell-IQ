from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Request, Response
import time

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
PREDICTION_COUNT = Counter('predictions_total', 'Total predictions served')
CACHE_HITS = Counter('cache_hits_total', 'Prediction cache hits')

async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)
    return response

async def metrics_endpoint():
    return Response(content=generate_latest(), media_type="text/plain")
