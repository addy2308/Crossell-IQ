"""
Pytest Load Tests for Netflix Cross-Sell API
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from typing import Dict, List, Any


@pytest.fixture
def api_base_url():
    """API base URL"""
    return "http://localhost:8000"


@pytest.fixture
def sample_customer():
    """Sample customer data"""
    return {
        "total_ratings": 250,
        "unique_movies": 180,
        "mean_rating": 3.8,
        "std_rating": 0.9,
        "tenure_days": 500,
        "recency_days": 15,
        "rating_velocity": 0.5,
        "is_active_6m": 1,
        "is_active_1y": 1,
        "rating_consistency": 0.85,
        "engagement_score": 75
    }


class TestAPIPerformance:
    """Performance tests for Netflix API"""
    
    def test_single_prediction_response_time(self, api_base_url, sample_customer):
        """Test single prediction response time < 100ms"""
        start_time = time.time()
        
        response = requests.post(
            f"{api_base_url}/api/netflix/predict",
            json=sample_customer
        )
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert elapsed_time < 100, f"Response time {elapsed_time}ms exceeds 100ms threshold"
        assert response.json()["success"] is True
    
    def test_batch_prediction_response_time(self, api_base_url, sample_customer):
        """Test batch prediction response time < 500ms for 10 customers"""
        customers = [sample_customer.copy() for _ in range(10)]
        
        start_time = time.time()
        
        response = requests.post(
            f"{api_base_url}/api/netflix/predict/batch",
            json={"customers": customers}
        )
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        assert response.status_code == 200
        assert elapsed_time < 500, f"Batch response time {elapsed_time}ms exceeds 500ms threshold"
        assert len(response.json()) == 10
    
    def test_model_status_response_time(self, api_base_url):
        """Test model status endpoint < 50ms"""
        start_time = time.time()
        
        response = requests.get(f"{api_base_url}/api/netflix/model/status")
        
        elapsed_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert elapsed_time < 50, f"Status check {elapsed_time}ms exceeds 50ms threshold"
    
    def test_concurrent_single_predictions(self, api_base_url, sample_customer):
        """Test 20 concurrent single predictions"""
        num_requests = 20
        max_response_time = 100  # ms
        
        def make_request():
            start = time.time()
            response = requests.post(
                f"{api_base_url}/api/netflix/predict",
                json=sample_customer
            )
            elapsed = (time.time() - start) * 1000
            return response.status_code, elapsed
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [f.result() for f in as_completed(futures)]
        
        # All requests should succeed
        assert all(status == 200 for status, _ in results), \
            f"Some requests failed: {[s for s, _ in results]}"
        
        # Calculate statistics
        response_times = [elapsed for _, elapsed in results]
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        print(f"\nConcurrency Test Results:")
        print(f"  Average response time: {avg_time:.2f}ms")
        print(f"  Max response time: {max_time:.2f}ms")
        
        assert avg_time < max_response_time, \
            f"Average response time {avg_time:.2f}ms exceeds threshold"
    
    def test_concurrent_batch_predictions(self, api_base_url, sample_customer):
        """Test 10 concurrent batch predictions"""
        num_requests = 10
        customers_per_batch = 5
        
        def make_batch_request():
            start = time.time()
            customers = [sample_customer.copy() for _ in range(customers_per_batch)]
            response = requests.post(
                f"{api_base_url}/api/netflix/predict/batch",
                json={"customers": customers}
            )
            elapsed = (time.time() - start) * 1000
            return response.status_code, elapsed
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_batch_request) for _ in range(num_requests)]
            results = [f.result() for f in as_completed(futures)]
        
        assert all(status == 200 for status, _ in results)
        
        response_times = [elapsed for _, elapsed in results]
        avg_time = sum(response_times) / len(response_times)
        
        print(f"\nBatch Concurrency Test Results:")
        print(f"  Average response time: {avg_time:.2f}ms")
        print(f"  Total requests: {num_requests}")


class TestAPIReliability:
    """Reliability tests for Netflix API"""
    
    def test_model_status_consistently_available(self, api_base_url):
        """Test that model status endpoint is consistently available"""
        num_requests = 50
        success_count = 0
        
        for _ in range(num_requests):
            try:
                response = requests.get(
                    f"{api_base_url}/api/netflix/model/status",
                    timeout=5
                )
                if response.status_code == 200:
                    success_count += 1
            except requests.RequestException:
                pass
        
        availability = (success_count / num_requests) * 100
        print(f"\nAvailability Test: {availability:.1f}% ({success_count}/{num_requests})")
        
        assert availability >= 99, f"Availability {availability}% below 99% threshold"
    
    def test_prediction_consistency(self, api_base_url, sample_customer):
        """Test that same input produces same output"""
        num_requests = 5
        results = []
        
        for _ in range(num_requests):
            response = requests.post(
                f"{api_base_url}/api/netflix/predict",
                json=sample_customer
            )
            assert response.status_code == 200
            results.append(response.json()["propensity_score"])
        
        # All scores should be identical (or very close due to floating point)
        assert all(abs(r - results[0]) < 0.0001 for r in results), \
            f"Predictions inconsistent: {results}"
        
        print(f"\nConsistency Test: All predictions identical = {results[0]:.4f}")


class TestAPIErrorHandling:
    """Error handling tests"""
    
    def test_invalid_customer_data(self, api_base_url):
        """Test handling of invalid customer data"""
        invalid_data = {"invalid_field": 123}
        
        response = requests.post(
            f"{api_base_url}/api/netflix/predict",
            json=invalid_data
        )
        
        # Should handle gracefully
        assert response.status_code in [400, 422]
    
    def test_missing_required_fields(self, api_base_url, sample_customer):
        """Test handling of missing required fields"""
        incomplete_data = {k: v for k, v in sample_customer.items() if k != "total_ratings"}
        
        response = requests.post(
            f"{api_base_url}/api/netflix/predict",
            json=incomplete_data
        )
        
        assert response.status_code in [400, 422]


# Performance benchmarking fixture
@pytest.fixture
def benchmark_results():
    """Store benchmark results"""
    return {}


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "reliability: mark test as a reliability test"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
