import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional


class FeatureEngineer:
    """Feature engineering pipeline for NBA model."""
    
    def __init__(self):
        self.feature_columns = [
            'recency_days', 'frequency', 'monetary', 'tenure_days',
            'num_products', 'engagement_score', 'days_since_service',
            'had_claim_60d', 'renewal_in_30_days', 'lost_quotation_count',
            'owns_A', 'owns_B', 'owns_C'
        ]
    
    def build_features(
        self,
        customers_df: pd.DataFrame,
        transactions_df: Optional[pd.DataFrame] = None,
        services_df: Optional[pd.DataFrame] = None,
        claims_df: Optional[pd.DataFrame] = None,
        lost_quotations_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Build feature matrix from raw data."""
        
        today = datetime.now()
        df = customers_df.copy()
        
        # RFM features
        if transactions_df is not None:
            rfm = transactions_df.groupby('customer_id').agg(
                last_transaction=('transaction_date', 'max'),
                frequency=('transaction_date', 'count'),
                monetary=('amount', 'sum')
            ).reset_index()
            rfm['recency_days'] = (today - pd.to_datetime(rfm['last_transaction'])).dt.days
            df = df.merge(rfm[['customer_id', 'recency_days', 'frequency', 'monetary']], 
                         on='customer_id', how='left')
        else:
            df['recency_days'] = 9999
            df['frequency'] = 0
            df['monetary'] = 0
        
        # Tenure
        if 'acquisition_date' in df.columns:
            df['tenure_days'] = (today - pd.to_datetime(df['acquisition_date'])).dt.days
        else:
            df['tenure_days'] = 0
        
        # Product features
        if 'products_owned' in df.columns:
            df['owns_A'] = df['products_owned'].apply(lambda x: int('A' in x) if isinstance(x, list) else 0)
            df['owns_B'] = df['products_owned'].apply(lambda x: int('B' in x) if isinstance(x, list) else 0)
            df['owns_C'] = df['products_owned'].apply(lambda x: int('C' in x) if isinstance(x, list) else 0)
            df['num_products'] = df['products_owned'].apply(lambda x: len(x) if isinstance(x, list) else 1)
        else:
            df['owns_A'] = 0
            df['owns_B'] = 0
            df['owns_C'] = 0
            df['num_products'] = 1
        
        # Service features
        if services_df is not None:
            svc = services_df.groupby('customer_id')['last_service_date'].max().reset_index()
            svc['days_since_service'] = (today - pd.to_datetime(svc['last_service_date'])).dt.days
            df = df.merge(svc[['customer_id', 'days_since_service']], on='customer_id', how='left')
        else:
            df['days_since_service'] = 9999
        
        # Claim features
        if claims_df is not None:
            claims = claims_df.groupby('customer_id')['last_claim_date'].max().reset_index()
            claims['had_claim_60d'] = (
                (today - pd.to_datetime(claims['last_claim_date'])).dt.days <= 60
            ).astype(int)
            df = df.merge(claims[['customer_id', 'had_claim_60d']], on='customer_id', how='left')
        else:
            df['had_claim_60d'] = 0
        
        # Lost quotation features
        if lost_quotations_df is not None:
            lost = lost_quotations_df.groupby('customer_id').size().reset_index(name='lost_quotation_count')
            df = df.merge(lost, on='customer_id', how='left')
        else:
            df['lost_quotation_count'] = 0
        
        # Engagement (simulated if not provided)
        if 'engagement_score' not in df.columns:
            df['engagement_score'] = np.random.uniform(0.1, 1.0, len(df))
        
        # Renewal flag (simulated if not provided)
        if 'renewal_in_30_days' not in df.columns:
            df['renewal_in_30_days'] = np.random.choice([0, 1], len(df), p=[0.8, 0.2])
        
        # Fill NaN values
        df = df.fillna(0)
        
        return df[self.feature_columns + ['customer_id']]