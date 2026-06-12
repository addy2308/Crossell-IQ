from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

class AgentRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"

class PredictionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIONED = "actioned"
    CONVERTED = "converted"
    IGNORED = "ignored"
    EXPIRED = "expired"

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(200))
    email = Column(String(200))
    region = Column(String(100))
    age = Column(Integer)
    income = Column(Float)
    products_owned = Column(JSON)
    acquisition_date = Column(DateTime)
    
    # RFM features
    recency_days = Column(Integer, default=9999)
    frequency = Column(Integer, default=0)
    monetary = Column(Float, default=0.0)
    tenure_days = Column(Integer, default=0)
    
    # Behavioral features
    engagement_score = Column(Float, default=0.5)
    days_since_service = Column(Integer, default=9999)
    had_claim_60d = Column(Boolean, default=False)
    renewal_in_30_days = Column(Boolean, default=False)
    lost_quotation_count = Column(Integer, default=0)
    
    # Latest prediction
    latest_propensity_score = Column(Float)
    latest_recommended_product = Column(String(200))
    segment = Column(Integer)
    segment_name = Column(String(100))
    last_prediction_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    predictions = relationship("Prediction", back_populates="customer", lazy="selectin")
    feedbacks = relationship("Feedback", back_populates="customer", lazy="selectin")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    propensity_score = Column(Float, nullable=False)
    recommended_product = Column(String(200))
    recommended_channel = Column(String(50))
    model_version = Column(String(50))
    features_snapshot = Column(JSON)
    shap_explanation = Column(JSON)
    status = Column(String(50), default=PredictionStatus.PENDING.value)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    actioned_at = Column(DateTime)
    
    customer = relationship("Customer", back_populates="predictions")
    feedbacks = relationship("Feedback", back_populates="prediction", lazy="selectin")

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(500), nullable=False)
    region = Column(String(100))
    role = Column(String(50), default=AgentRole.AGENT.value)
    is_active = Column(Boolean, default=True)
    assigned_customers = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class Feedback(Base):
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    action_taken = Column(String(100), nullable=False)
    outcome = Column(String(50))
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="feedbacks")
    prediction = relationship("Prediction", back_populates="feedbacks")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)
    action = Column(String(200), nullable=False)
    resource = Column(String(200))
    details = Column(JSON)
    ip_address = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
