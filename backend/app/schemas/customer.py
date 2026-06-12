from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CustomerBase(BaseModel):
    customer_id: int
    region: Optional[str] = None
    age: Optional[int] = None
    products_owned: Optional[List[str]] = None


class CustomerResponse(CustomerBase):
    id: int
    tenure_days: Optional[int] = None
    recency_days: Optional[int] = None
    frequency: Optional[int] = None
    monetary: Optional[float] = None
    engagement_score: Optional[float] = None
    segment: Optional[int] = None
    segment_name: Optional[str] = None
    latest_propensity_score: Optional[float] = None
    latest_recommended_product: Optional[str] = None
    last_prediction_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CustomerList(BaseModel):
    total: int
    customers: List[CustomerResponse]