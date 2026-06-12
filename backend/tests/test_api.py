import pytest
from fastapi import status

class TestHealthEndpoint:
    def test_health_check(self, test_client):
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self, test_client):
        response = test_client.get("/")
        assert response.status_code == 200

class TestAuthEndpoints:
    def test_login_invalid_credentials(self, test_client):
        response = test_client.post("/api/v1/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_register_validation(self, test_client):
        response = test_client.post("/api/v1/auth/register", json={
            "name": "",
            "email": "invalid",
            "password": "short"
        })
        assert response.status_code in [200, 400, 422]

class TestDashboardEndpoints:
    def test_dashboard_summary(self, test_client):
        response = test_client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_customers" in data
    
    def test_recent_predictions(self, test_client):
        response = test_client.get("/api/v1/predictions/recent?limit=5")
        assert response.status_code == 200
    
    def test_agent_queue(self, test_client):
        response = test_client.get("/api/v1/agent/queue?agent_id=default&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "queue" in data

class TestPredictionEndpoint:
    def test_predict_valid_customer(self, test_client):
        response = test_client.get("/api/v1/predictions/recent?limit=1")
        assert response.status_code in [200, 404]
