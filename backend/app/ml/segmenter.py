import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from typing import List, Tuple


class CustomerSegmenter:
    """Customer segmentation using clustering."""
    
    SEGMENT_NAMES = {
        0: "High-Value Loyalist",
        1: "Dormant Upsell Candidate",
        2: "Price-Sensitive Switcher",
        3: "Life-Stage Triggered"
    }
    
    SEGMENT_STRATEGIES = {
        0: "Premium upsell via personal call",
        1: "Re-engagement with targeted email campaigns",
        2: "Price-matched competitive bundle offers",
        3: "Life-event triggered cross-sell notifications"
    }
    
    def __init__(self, n_clusters: int = 4):
        self.n_clusters = n_clusters
        self.model = None
        self.feature_columns = [
            'recency_days', 'frequency', 'monetary', 
            'tenure_days', 'num_products', 'engagement_score'
        ]
    
    def fit(self, features: pd.DataFrame) -> np.ndarray:
        """Fit the segmentation model."""
        X = features[self.feature_columns].fillna(0).values
        
        # Normalize
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # K-Means clustering
        self.model = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        labels = self.model.fit_predict(X_scaled)
        
        return labels
    
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Predict segments for new data."""
        if self.model is None:
            return np.zeros(len(features))
        
        X = features[self.feature_columns].fillna(0).values
        
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        return self.model.predict(X_scaled)
    
    def get_segment_name(self, segment_id: int) -> str:
        """Get human-readable segment name."""
        return self.SEGMENT_NAMES.get(segment_id, "Unknown")
    
    def get_strategy(self, segment_id: int) -> str:
        """Get recommended strategy for segment."""
        return self.SEGMENT_STRATEGIES.get(segment_id, "Standard approach")