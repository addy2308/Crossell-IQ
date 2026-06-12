from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Dict, List

from app.models.customer import Customer, Prediction, Feedback


class AnalyticsService:
    """Service for analytics and reporting."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_funnel_metrics(self) -> Dict:
        """Get conversion funnel metrics."""
        # Total customers
        result = await self.db.execute(select(func.count(Customer.id)))
        total_customers = result.scalar() or 0
        
        # Customers with predictions
        result = await self.db.execute(
            select(func.count(Customer.id))
            .where(Customer.latest_propensity_score.isnot(None))
        )
        customers_predicted = result.scalar() or 0
        
        # Feedback received
        result = await self.db.execute(select(func.count(Feedback.id)))
        total_feedback = result.scalar() or 0
        
        # Conversions
        result = await self.db.execute(
            select(func.count(Feedback.id))
            .where(Feedback.outcome == "converted")
        )
        conversions = result.scalar() or 0
        
        return {
            "total_customers": total_customers,
            "customers_with_predictions": customers_predicted,
            "prediction_coverage": round((customers_predicted / max(total_customers, 1)) * 100, 1),
            "feedbacks_received": total_feedback,
            "conversions": conversions,
            "conversion_rate": round((conversions / max(total_feedback, 1)) * 100, 1),
            "funnel": [
                {"stage": "Total Customers", "count": total_customers},
                {"stage": "Predictions Made", "count": customers_predicted},
                {"stage": "Agent Actions", "count": total_feedback},
                {"stage": "Conversions", "count": conversions}
            ]
        }
    
    async def get_time_series_metrics(self, days: int = 30) -> List[Dict]:
        """Get daily metrics for the last N days."""
        metrics = []
        
        for i in range(days, 0, -1):
            date = datetime.utcnow() - timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            # Predictions on this day
            result = await self.db.execute(
                select(func.count(Prediction.id))
                .where(
                    Prediction.created_at >= date,
                    Prediction.created_at < next_date
                )
            )
            daily_predictions = result.scalar() or 0
            
            # Feedback on this day
            result = await self.db.execute(
                select(func.count(Feedback.id))
                .where(
                    Feedback.created_at >= date,
                    Feedback.created_at < next_date
                )
            )
            daily_feedback = result.scalar() or 0
            
            metrics.append({
                "date": date.strftime("%Y-%m-%d"),
                "predictions": daily_predictions,
                "feedback": daily_feedback
            })
        
        return metrics