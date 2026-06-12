from celery import Celery
from app.config import get_settings
import time

settings = get_settings()

celery_app = Celery(
    'crosssell_tasks',
    broker=settings.REDIS_URL or 'redis://localhost:6379/0',
    backend=settings.REDIS_URL or 'redis://localhost:6379/0'
)

@celery_app.task
def batch_predict():
    """Background task to run batch predictions for all customers."""
    # Simulate batch prediction
    time.sleep(2)
    return {"status": "completed", "predictions": 482}

@celery_app.task
def send_agent_alert(agent_id: str, message: str):
    """Send alert to agent (simulated)."""
    # In production, this would push via WebSocket or email
    print(f"Alert sent to {agent_id}: {message}")
    return {"agent_id": agent_id, "message": message}

@celery_app.task
def retrain_model():
    """Trigger model retraining (simulated)."""
    time.sleep(5)
    return {"status": "Model retrained", "auc": 0.85}
