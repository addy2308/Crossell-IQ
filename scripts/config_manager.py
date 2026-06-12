#!/usr/bin/env python3
"""
Environment Configuration Manager
Manages environment-specific configurations for different deployment targets
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class EnvironmentConfig:
    """Environment configuration"""
    name: str
    debug: bool
    log_level: str
    database_url: str
    redis_url: str
    docker_registry: str
    image_tag: str
    replicas: int
    resources: Dict[str, Any]


class ConfigManager:
    """Manage environment configurations"""
    
    CONFIGS = {
        'development': EnvironmentConfig(
            name='development',
            debug=True,
            log_level='DEBUG',
            database_url='postgresql://netflix:netflix@localhost:5432/netflix_dev',
            redis_url='redis://localhost:6379/0',
            docker_registry='localhost:5000',
            image_tag='latest',
            replicas=1,
            resources={
                'cpu': '100m',
                'memory': '256Mi',
                'limit_cpu': '500m',
                'limit_memory': '512Mi'
            }
        ),
        'staging': EnvironmentConfig(
            name='staging',
            debug=False,
            log_level='INFO',
            database_url='postgresql://netflix:${DB_PASSWORD}@postgres-staging:5432/netflix',
            redis_url='redis://redis-staging:6379/0',
            docker_registry='ghcr.io/yourusername',
            image_tag='staging',
            replicas=2,
            resources={
                'cpu': '500m',
                'memory': '512Mi',
                'limit_cpu': '1000m',
                'limit_memory': '1Gi'
            }
        ),
        'production': EnvironmentConfig(
            name='production',
            debug=False,
            log_level='WARNING',
            database_url='postgresql://netflix:${DB_PASSWORD}@postgres-prod:5432/netflix',
            redis_url='redis://redis-prod:6379/0',
            docker_registry='ghcr.io/yourusername',
            image_tag='stable',
            replicas=3,
            resources={
                'cpu': '1000m',
                'memory': '1Gi',
                'limit_cpu': '2000m',
                'limit_memory': '2Gi'
            }
        )
    }
    
    @classmethod
    def get_config(cls, env: str) -> EnvironmentConfig:
        """Get configuration for environment"""
        if env not in cls.CONFIGS:
            raise ValueError(f"Unknown environment: {env}")
        return cls.CONFIGS[env]
    
    @classmethod
    def get_env_file(cls, env: str) -> str:
        """Generate .env file content"""
        config = cls.get_config(env)
        
        return f"""
# Netflix Cross-Sell API - {env.upper()} Environment Configuration

# Environment
ENVIRONMENT={env}
DEBUG={str(config.debug).lower()}
LOG_LEVEL={config.log_level}

# Database
DATABASE_URL={config.database_url}
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Redis Cache
REDIS_URL={config.redis_url}
CACHE_TTL=3600

# API Configuration
API_TITLE=Netflix Cross-Sell API
API_VERSION=1.0.0
API_WORKERS={config.replicas}

# Security
SECRET_KEY=${{SECRET_KEY}}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["https://netflix-api.example.com"]
CORS_CREDENTIALS=true
CORS_METHODS=["GET", "POST", "OPTIONS"]
CORS_HEADERS=["*"]

# MLFlow
MLFLOW_TRACKING_URI=postgresql://mlflow:${{MLFLOW_PASSWORD}}@postgres-prod:5432/mlflow
MLFLOW_BACKEND_STORE_URI=${{MLFLOW_TRACKING_URI}}
MLFLOW_ARTIFACTS_URI=s3://netflix-ml-artifacts/

# Model Configuration
MODEL_PATH=/app/models/netflix_model.pkl
BATCH_SIZE=32
MAX_PREDICTION_TIME=5.0

# Monitoring
PROMETHEUS_ENABLED=true
SENTRY_DSN=${{SENTRY_DSN}}

# Docker Registry
DOCKER_REGISTRY={config.docker_registry}
IMAGE_TAG={config.image_tag}

# Resource Limits
CPU_REQUEST={config.resources['cpu']}
MEMORY_REQUEST={config.resources['memory']}
CPU_LIMIT={config.resources['limit_cpu']}
MEMORY_LIMIT={config.resources['limit_memory']}
"""


def generate_k8s_manifest(env: str) -> str:
    """Generate Kubernetes manifest for environment"""
    config = ConfigManager.get_config(env)
    
    return f"""
apiVersion: v1
kind: Namespace
metadata:
  name: netflix-{{env}}

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: netflix-api
  namespace: netflix-{{env}}
  labels:
    app: netflix-api
    environment: {{env}}
spec:
  replicas: {{config.replicas}}
  selector:
    matchLabels:
      app: netflix-api
  template:
    metadata:
      labels:
        app: netflix-api
        environment: {{env}}
    spec:
      containers:
      - name: api
        image: {{config.docker_registry}}/netflix-api:{{config.image_tag}}
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: ENVIRONMENT
          value: "{{env}}"
        - name: LOG_LEVEL
          value: "{{config.log_level}}"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: netflix-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: netflix-config
              key: redis-url
        resources:
          requests:
            cpu: {{config.resources['cpu']}}
            memory: {{config.resources['memory']}}
          limits:
            cpu: {{config.resources['limit_cpu']}}
            memory: {{config.resources['limit_memory']}}
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: netflix-api
  namespace: netflix-{{env}}
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
    name: http
  selector:
    app: netflix-api

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: netflix-api-hpa
  namespace: netflix-{{env}}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: netflix-api
  minReplicas: {{config.replicas}}
  maxReplicas: {{config.replicas * 3}}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
"""


def generate_docker_compose(env: str) -> str:
    """Generate Docker Compose file for environment"""
    config = ConfigManager.get_config(env)
    
    return f"""
version: '3.8'

services:
  api:
    image: {{config.docker_registry}}/netflix-api:{{config.image_tag}}
    container_name: netflix-api-{{env}}
    ports:
      - "8000:8000"
    environment:
      ENVIRONMENT: {{env}}
      LOG_LEVEL: {{config.log_level}}
      DATABASE_URL: {{config.database_url}}
      REDIS_URL: {{config.redis_url}}
    depends_on:
      - postgres
      - redis
    networks:
      - netflix
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  postgres:
    image: postgres:15
    container_name: postgres-{{env}}
    environment:
      POSTGRES_USER: netflix
      POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD}}
      POSTGRES_DB: netflix
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - netflix
    restart: unless-stopped
  
  redis:
    image: redis:7
    container_name: redis-{{env}}
    ports:
      - "6379:6379"
    networks:
      - netflix
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  netflix:
    driver: bridge
"""


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate environment configurations')
    parser.add_argument('--env', choices=['development', 'staging', 'production'], required=True)
    parser.add_argument('--format', choices=['env', 'k8s', 'docker-compose'], default='env')
    
    args = parser.parse_args()
    
    if args.format == 'env':
        print(ConfigManager.get_env_file(args.env))
    elif args.format == 'k8s':
        print(generate_k8s_manifest(args.env))
    elif args.format == 'docker-compose':
        print(generate_docker_compose(args.env))
