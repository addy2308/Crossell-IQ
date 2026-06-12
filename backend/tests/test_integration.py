import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_dashboard_flow():
    # 1. Health check
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

    # 2. Dashboard summary
    resp = client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_customers" in data
    assert data["total_customers"] >= 10000

    # 3. Recent predictions
    resp = client.get("/api/v1/predictions/recent?limit=5")
    assert resp.status_code == 200
    preds = resp.json()
    assert isinstance(preds, list)
    assert len(preds) > 0

    # 4. Agent queue
    resp = client.get("/api/v1/agent/queue?agent_id=test&limit=3")
    assert resp.status_code == 200
    queue = resp.json()
    assert "queue" in queue
    assert len(queue["queue"]) > 0

    # 5. Model evaluation
    resp = client.get("/api/v1/evaluation/report")
    assert resp.status_code == 200
    report = resp.json()
    assert "model_metrics" in report
