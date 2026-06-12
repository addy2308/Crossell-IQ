import pandas as pd
from typing import List, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio

from app.models.customer import Customer, Prediction
from app.ml.predictor import predictor


class PredictionService:
    """Service for batch prediction operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def batch_predict(self, customer_ids: List[int]) -> List[Dict]:
        """Run batch predictions for multiple customers."""
        result = await self.db.execute(
            select(Customer).where(Customer.customer_id.in_(customer_ids))
        )
        customers = result.scalars().all()
        
        if not customers:
            return []
        
        # Prepare feature matrix
        features_list = []
        for cust in customers:
            features_list.append({
                'customer_id': cust.customer_id,
                'recency_days': cust.recency_days or 9999,
                'frequency': cust.frequency or 0,
                'monetary': cust.monetary or 0,
                'tenure_days': cust.tenure_days or 0,
                'num_products': len(cust.products_owned) if cust.products_owned else 1,
                'engagement_score': cust.engagement_score or 0.5,
                'days_since_service': cust.days_since_service or 9999,
                'had_claim_60d': int(cust.had_claim_60d or False),
                'renewal_in_30_days': int(cust.renewal_in_30_days or False),
                'lost_quotation_count': cust.lost_quotation_count or 0,
                'owns_A': int('A' in (cust.products_owned or [])),
                'owns_B': int('B' in (cust.products_owned or [])),
                'owns_C': int('C' in (cust.products_owned or [])),
            })
        
        features_df = pd.DataFrame(features_list)
        results_df = predictor.predict_batch(features_df)
        
        # Format results
        predictions = []
        for _, row in results_df.iterrows():
            predictions.append({
                'customer_id': row['customer_id'],
                'propensity_score': round(row['propensity_score'], 4),
                'segment': int(row['segment'])
            })
        
        return predictions