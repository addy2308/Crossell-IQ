from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class PredictionRequest(BaseModel):
    customer_id: int = Field(..., description="Customer ID to predict for")


class PredictionResponse(BaseModel):
    customer_id: int
    propensity_score: float = Field(..., ge=0, le=1)
    recommended_product: str
    segment: int
    segment_name: str
    top_features: Dict[str, float]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class AgentQueueRequest(BaseModel):
    agent_id: str
    limit: int = Field(default=10, ge=1, le=50)


class AgentQueueItem(BaseModel):
    customer_id: int
    propensity_score: float
    recommended_product: str
    urgency: str  # high, medium, low
    reasoning: str
    suggested_channel: str  # phone, email, whatsapp


class FeedbackRequest(BaseModel):
    customer_id: int
    agent_id: str
    prediction_id: int
    action_taken: str = Field(..., pattern="^(called_interested|called_not_interested|email_sent|ignored)$")
    outcome: Optional[str] = Field(None, pattern="^(converted|not_converted|pending)$")
    notes: Optional[str] = Field(None, max_length=500)


class FeedbackResponse(BaseModel):
    status: str
    message: str
    feedback_id: int