import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

@pytest.fixture
def test_client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)

@pytest.fixture
def sample_customer_data():
    return {
        "customer_id": 1,
        "name": "Test Customer",
        "region": "North",
        "age": 35,
        "income": 500000
    }
