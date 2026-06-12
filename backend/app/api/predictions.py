from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import pandas as pd
from datetime import datetime

from app.database import get_db
from app.models.customer import Customer, Prediction, Feedback
from app.schemas.prediction import (
    PredictionRequest, PredictionResponse,
    AgentQueueItem, FeedbackRequest, FeedbackResponse
)
from app.ml.predictor import predictor
from app.services.agent_service import AgentService

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def get_prediction(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get real-time propensity prediction for a customer."""
    # Fetch customer from database
    result = await db.execute(
        select(Customer).where(Customer.customer_id == request.customer_id)
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Prepare feature vector
    features = pd.DataFrame([{
        'recency_days': customer.recency_days or 9999,
        'frequency': customer.frequency or 0,
        'monetary': customer.monetary or 0,
        'tenure_days': customer.tenure_days or 0,
        'num_products': len(customer.products_owned) if customer.products_owned else 1,
        'engagement_score': customer.engagement_score or 0.5,
        'days_since_service': customer.days_since_service or 9999,
        'had_claim_60d': int(customer.had_claim_60d or False),
        'renewal_in_30_days': int(customer.renewal_in_30_days or False),
        'lost_quotation_count': customer.lost_quotation_count or 0,
        'owns_A': int('A' in (customer.products_owned or [])),
        'owns_B': int('B' in (customer.products_owned or [])),
        'owns_C': int('C' in (customer.products_owned or [])),
    }])
    
    # Get prediction
    propensity, product, segment, segment_name, shap_values = predictor.predict_single(features)
    
    # Save prediction to database
    prediction = Prediction(
        customer_id=customer.id,
        propensity_score=propensity,
        recommended_product=product,
        model_version="v2.0",
        features_snapshot=features.to_dict(orient='records')[0],
        shap_explanation=shap_values
    )
    db.add(prediction)
    
    # Update customer's latest prediction
    customer.latest_propensity_score = propensity
    customer.latest_recommended_product = product
    customer.segment = segment
    customer.segment_name = segment_name
    customer.last_prediction_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(prediction)
    
    return PredictionResponse(
        customer_id=request.customer_id,
        propensity_score=propensity,
        recommended_product=product,
        segment=segment,
        segment_name=segment_name,
        top_features=shap_values,
        timestamp=prediction.created_at
    )


@router.get("/agent-queue", response_model=List[AgentQueueItem])
async def get_agent_queue(
    agent_id: str = Query(..., description="Agent ID"),
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get prioritized next-best-action queue for an agent."""
    agent_service = AgentService(db)
    queue = await agent_service.get_agent_queue(agent_id, limit)
    return queue


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit agent feedback on a prediction."""
    # Verify prediction exists
    result = await db.execute(
        select(Prediction).where(Prediction.id == request.prediction_id)
    )
    prediction = result.scalar_one_or_none()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    # Create feedback record
    feedback = Feedback(
        customer_id=request.customer_id,
        agent_id=request.agent_id,
        prediction_id=request.prediction_id,
        action_taken=request.action_taken,
        outcome=request.outcome or "pending",
        notes=request.notes
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    
    return FeedbackResponse(
        status="success",
        message="Feedback recorded successfully",
        feedback_id=feedback.id
    )


@router.get("/history/{customer_id}")
async def get_prediction_history(
    customer_id: int,
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get prediction history for a customer."""
    result = await db.execute(
        select(Prediction)
        .where(Prediction.customer_id == customer_id)
        .order_by(Prediction.created_at.desc())
        .limit(limit)
    )
    predictions = result.scalars().all()
    
    return [
        {
            "id": p.id,
            "propensity_score": p.propensity_score,
            "recommended_product": p.recommended_product,
            "model_version": p.model_version,
            "created_at": p.created_at
        }
        for p in predictions
    ]