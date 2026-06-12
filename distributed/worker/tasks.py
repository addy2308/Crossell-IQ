from celery import Celery
import pandas as pd
import subprocess
import sys
from pathlib import Path
import os

celery_app = Celery('crosssell_worker', broker=os.getenv('REDIS_URL','redis://redis:6379/0'))

@celery_app.task
def process_feedback(customer_id, agent_id, action, notes):
    # Store feedback (simplified – in production, write to PostgreSQL)
    print(f"Feedback stored: {customer_id} - {action}")
    
    # Check feedback count – if >=10, trigger retraining
    # (in a real system, query the database)
    if customer_id % 10 == 0:   # demo trigger
        retrain_model.delay()

@celery_app.task
def retrain_model():
    print("Starting model retraining...")
    subprocess.run([sys.executable, "/app/../models/train_model.py"], check=True)
    print("Retraining complete.")

@celery_app.task
def check_drift():
    # Simplified drift check – in production, load current features and compare
    print("Drift check completed.")
