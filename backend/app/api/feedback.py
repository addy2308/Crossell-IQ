from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import sqlite3
from pathlib import Path
import subprocess, sys, os, joblib

router = APIRouter(prefix="/feedback", tags=["Feedback"])

class FeedbackRequest(BaseModel):
    customer_id: int
    agent_id: str
    action: str
    notes: str = ""

def store_feedback(data: dict):
    db_path = Path(__file__).parent.parent.parent.parent / 'data' / 'feedback.db'
    conn = sqlite3.connect(db_path)
    conn.execute('''CREATE TABLE IF NOT EXISTS feedback
                 (customer_id INTEGER, agent_id TEXT, action TEXT, notes TEXT, timestamp TEXT)''')
    conn.execute('INSERT INTO feedback VALUES (?,?,?,?,?)',
                 (data['customer_id'], data['agent_id'], data['action'],
                  data['notes'], datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def trigger_retraining():
    """Run the training script and reload the model after completion."""
    base = Path(__file__).parent.parent.parent.parent
    train_script = base / 'models' / 'train_model.py'
    subprocess.run([sys.executable, str(train_script)], check=False)
    # Reload the predictor instance
    from app.ml.predictor import predictor
    predictor.load_model()

@router.post("/submit")
async def submit_feedback(feedback: FeedbackRequest, background_tasks: BackgroundTasks):
    store_feedback(feedback.dict())
    db_path = Path(__file__).parent.parent.parent.parent / 'data' / 'feedback.db'
    conn = sqlite3.connect(db_path)
    count = conn.execute('SELECT COUNT(*) FROM feedback').fetchone()[0]
    conn.close()
    if count >= 10:
        background_tasks.add_task(trigger_retraining)
        return {"status": "Feedback stored. Retraining triggered."}
    return {"status": "Feedback stored."}
