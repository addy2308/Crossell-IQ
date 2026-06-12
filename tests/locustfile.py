"""
Load Testing Scripts for Netflix Cross-Sell API
Uses Locust to test API performance and scalability
"""

from locust import HttpUser, task, between, TaskSet
import json
import random
from datetime import datetime

# Sample customer data for testing
SAMPLE_CUSTOMERS = [
    {
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
    },
    {
        "total_ratings": 100,
        "unique_movies": 80,
        "mean_rating": 3.2,
        "std_rating": 1.1,
        "tenure_days": 200,
        "recency_days": 45,
        "rating_velocity": 0.3,
        "is_active_6m": 0,
        "is_active_1y": 1,
        "rating_consistency": 0.65,
        "engagement_score": 45
    },
    {
        "total_ratings": 500,
        "unique_movies": 380,
        "mean_rating": 4.1,
        "std_rating": 0.7,
        "tenure_days": 1000,
        "recency_days": 5,
        "rating_velocity": 0.8,
        "is_active_6m": 1,
        "is_active_1y": 1,
        "rating_consistency": 0.92,
        "engagement_score": 92
    },
    {
        "total_ratings": 50,
        "unique_movies": 40,
        "mean_rating": 2.9,
        "std_rating": 1.3,
        "tenure_days": 50,
        "recency_days": 100,
        "rating_velocity": 0.2,
        "is_active_6m": 0,
        "is_active_1y": 0,
        "rating_consistency": 0.50,
        "engagement_score": 25
    }
]


def generate_random_customer():
    """Generate a random customer profile"""
    base = random.choice(SAMPLE_CUSTOMERS)
    return {
        "total_ratings": base["total_ratings"] + random.randint(-50, 50),
        "unique_movies": base["unique_movies"] + random.randint(-30, 30),
        "mean_rating": max(1, min(5, base["mean_rating"] + random.uniform(-0.5, 0.5))),
        "std_rating": max(0.1, base["std_rating"] + random.uniform(-0.3, 0.3)),
        "tenure_days": max(1, base["tenure_days"] + random.randint(-100, 100)),
        "recency_days": max(0, base["recency_days"] + random.randint(-20, 20)),
        "rating_velocity": max(0, base["rating_velocity"] + random.uniform(-0.2, 0.2)),
        "is_active_6m": random.randint(0, 1),
        "is_active_1y": random.randint(0, 1),
        "rating_consistency": max(0, min(1, base["rating_consistency"] + random.uniform(-0.1, 0.1))),
        "engagement_score": max(0, min(100, base["engagement_score"] + random.randint(-20, 20)))
    }


class NetflixAPITasks(TaskSet):
    """Define API testing tasks"""
    
    @task(3)
    def single_prediction(self):
        """Test single customer prediction endpoint (highest frequency)"""
        customer = generate_random_customer()
        self.client.post(
            "/api/netflix/predict",
            json=customer,
            name="/api/netflix/predict"
        )
    
    @task(2)
    def batch_prediction(self):
        """Test batch prediction endpoint"""
        customers = [generate_random_customer() for _ in range(random.randint(5, 10))]
        self.client.post(
            "/api/netflix/predict/batch",
            json={"customers": customers},
            name="/api/netflix/predict/batch"
        )
    
    @task(1)
    def get_model_status(self):
        """Test model status endpoint"""
        self.client.get(
            "/api/netflix/model/status",
            name="/api/netflix/model/status"
        )
    
    @task(1)
    def get_model_info(self):
        """Test model info endpoint"""
        self.client.get(
            "/api/netflix/model/info",
            name="/api/netflix/model/info"
        )
    
    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        self.client.post(
            "/api/netflix/health-check",
            json={"test": True},
            name="/api/netflix/health-check"
        )


class NetflixAPIUser(HttpUser):
    """Simulate a user of the Netflix API"""
    
    tasks = [NetflixAPITasks]
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests


class QuickLoadTest(HttpUser):
    """Quick/light load test"""
    
    tasks = [NetflixAPITasks]
    wait_time = between(2, 5)


class StressTest(HttpUser):
    """Stress test with minimal wait time"""
    
    tasks = [NetflixAPITasks]
    wait_time = between(0.5, 1)
