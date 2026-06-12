from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FeedbackCreate(BaseModel):
    customer_id: int
    agent_id: str
    prediction_id: int
    action_taken: str
    outcome: Optional[str] = None
    notes: Optional[str] = None


class FeedbackOut(BaseModel):
    id: int
    customer_id: int
    agent_id: str
    prediction_id: int
    action_taken: str
    outcome: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True