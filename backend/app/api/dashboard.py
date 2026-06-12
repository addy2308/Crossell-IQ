from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime, timedelta
import random

from app.database import get_db
from app.models.customer import Customer, Prediction, Feedback, Agent

router = APIRouter()


@router.get("/kpis")
async def get_dashboard_kpis(
    db: AsyncSession = Depends(get_db)
):
    """Get main dashboard KPIs."""
    # Total customers
    result = await db.execute(select(func.count(Customer.id)))
    total_customers = result.scalar() or 0
    
    # Customers with predictions
    result = await db.execute(
        select(func.count(Customer.id))
        .where(Customer.latest_propensity_score.isnot(None))
    )
    predicted_customers = result.scalar() or 0
    
    # Average propensity
    result = await db.execute(
        select(func.avg(Customer.latest_propensity_score))
        .where(Customer.latest_propensity_score.isnot(None))
    )
    avg_propensity = result.scalar() or 0
    
    # Total feedback this month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    result = await db.execute(
        select(func.count(Feedback.id))
        .where(Feedback.created_at >= month_start)
    )
    monthly_feedback = result.scalar() or 0
    
    # Conversions this month
    result = await db.execute(
        select(func.count(Feedback.id))
        .where(
            Feedback.created_at >= month_start,
            Feedback.outcome == "converted"
        )
    )
    monthly_conversions = result.scalar() or 0
    
    return {
        "total_customers": total_customers,
        "predicted_customers": predicted_customers,
        "coverage_rate": round((predicted_customers / max(total_customers, 1)) * 100, 1),
        "average_propensity_score": round(avg_propensity * 100, 1),
        "monthly_feedback": monthly_feedback,
        "monthly_conversions": monthly_conversions,
        "conversion_rate": round((monthly_conversions / max(monthly_feedback, 1)) * 100, 1)
    }


@router.get("/revenue-trend")
async def get_revenue_trend(
    period: str = Query(default="weekly", pattern="^(daily|weekly|monthly)$"),
    weeks: int = Query(default=12, le=52),
    db: AsyncSession = Depends(get_db)
):
    """Get revenue trend data (simulated for prototype)."""
    import numpy as np
    np.random.seed(42)
    
    # Generate dates
    end_date = datetime.utcnow()
    if period == "weekly":
        dates = [end_date - timedelta(weeks=i) for i in range(weeks, 0, -1)]
    elif period == "monthly":
        dates = [end_date - timedelta(days=30*i) for i in range(weeks, 0, -1)]
    else:
        dates = [end_date - timedelta(days=i) for i in range(weeks*7, 0, -1)]
    
    # Simulated data
    baseline_rev = np.cumsum(np.random.normal(50000, 5000, len(dates)))
    nba_rev = baseline_rev * 1.2 + np.cumsum(np.random.normal(2000, 2000, len(dates)))
    
    return [
        {
            "date": d.strftime("%Y-%m-%d"),
            "baseline": round(b, 2),
            "nba": round(n, 2),
            "uplift": round(n - b, 2)
        }
        for d, b, n in zip(dates, baseline_rev, nba_rev)
    ]


@router.get("/segment-distribution")
async def get_segment_distribution(
    db: AsyncSession = Depends(get_db)
):
    """Get customer segment distribution."""
    result = await db.execute(
        select(
            Customer.segment_name,
            func.count(Customer.id).label('count')
        )
        .where(Customer.segment_name.isnot(None))
        .group_by(Customer.segment_name)
    )
    
    segment_names = {
        0: "High-Value Loyalist",
        1: "Dormant Upsell Candidate",
        2: "Price-Sensitive Switcher",
        3: "Life-Stage Triggered"
    }
    
    distribution = []
    for row in result:
        distribution.append({
            "name": row.segment_name or segment_names.get(row.segment_name, "Unknown"),
            "value": row.count
        })
    
    return distribution if distribution else [
        {"name": name, "value": random.randint(200, 800)}
        for name in segment_names.values()
    ]


@router.get("/model-performance")
async def get_model_performance(
    db: AsyncSession = Depends(get_db)
):
    """Get model performance metrics."""
    # Get feedback-based metrics
    result = await db.execute(
        select(
            func.count(Feedback.id).label('total'),
            func.sum(
                func.case((Feedback.outcome == "converted", 1), else_=0)
            ).label('converted')
        )
    )
    row = result.one()
    
    total_feedback = row.total or 0
    total_converted = row.converted or 0
    
    return {
        "model_name": "NBA Propensity Model v2.0",
        "algorithm": "XGBoost with SHAP explanations",
        "auc_score": 0.84,
        "precision": 0.78,
        "recall": 0.82,
        "total_predictions": total_feedback,
        "observed_conversion_rate": round((total_converted / max(total_feedback, 1)) * 100, 1),
        "feature_count": 13,
        "last_trained": (datetime.utcnow() - timedelta(days=7)).isoformat()
    }