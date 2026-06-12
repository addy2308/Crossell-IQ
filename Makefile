.PHONY: install test run docker-build docker-up docker-down deploy k8s-apply k8s-delete logs clean

# Development
install:
    cd backend && pip install -r requirements.txt

test:
    cd backend && python -m pytest tests/ -v --tb=short --cov=app --cov-report=term

test-watch:
    cd backend && python -m pytest tests/ -v --tb=short --cov=app -f

run:
    cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

run-prod:
    cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Docker
docker-build:
    docker build -t crosssell-iq:latest ./backend

docker-up:
    docker-compose up -d

docker-down:
    docker-compose down

docker-logs:
    docker-compose logs -f api

docker-rebuild:
    docker-compose build --no-cache api
    docker-compose up -d

# Kubernetes
k8s-apply:
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/secret.yaml
    kubectl apply -f k8s/postgres.yaml
    kubectl apply -f k8s/redis.yaml
    kubectl apply -f k8s/api.yaml
    kubectl apply -f k8s/ingress.yaml

k8s-delete:
    kubectl delete namespace crosssell-iq

k8s-status:
    kubectl get all -n crosssell-iq

# Monitoring
monitoring-up:
    kubectl apply -f monitoring/prometheus.yml
    kubectl apply -f monitoring/grafana-dashboard.json

# Database
db-migrate:
    cd backend && alembic upgrade head

db-reset:
    cd backend && rm -f crosssell.db && python -m pytest tests/ -v --tb=short

# Cleanup
clean:
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    rm -rf backend/.pytest_cache backend/crosssell.db

# Full deploy
deploy: test docker-build docker-up
    @echo "Deployment complete at http://localhost:8000"

# CI
ci: install test docker-build
    @echo "CI pipeline complete"
