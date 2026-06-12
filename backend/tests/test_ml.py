import pytest
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

class TestPredictor:
    @pytest.fixture
    def sample_features(self):
        return pd.DataFrame([{
            'recency_days': 30, 'frequency': 5, 'monetary': 25000,
            'tenure_days': 500, 'num_products': 3, 'engagement_score': 0.8,
            'days_since_service': 45, 'had_claim_60d': 1,
            'renewal_in_30_days': 1, 'lost_quotation_count': 2,
            'owns_A': 1, 'owns_B': 1, 'owns_C': 0,
            'age': 35, 'income': 500000, 'competitor_price_avg': 12000
        }])
    
    def test_predictor_initialization(self):
        from app.ml.predictor import NBAPredictor
        predictor = NBAPredictor()
        assert predictor is not None
    
    def test_prediction_output_format(self, sample_features):
        from app.ml.predictor import predictor
        result = predictor.predict(sample_features)
        assert "propensity_score" in result
        assert "segment" in result
        assert "recommended_product" in result
        assert "reasoning" in result
        assert 0 <= result["propensity_score"] <= 1
    
    def test_batch_prediction(self):
        from app.ml.predictor import predictor
        df = pd.DataFrame([{
            'recency_days': i*10, 'frequency': i, 'monetary': i*5000,
            'tenure_days': i*100, 'num_products': i+1, 'engagement_score': 0.5,
            'days_since_service': i*20, 'had_claim_60d': i%2,
            'renewal_in_30_days': i%3, 'lost_quotation_count': i,
            'owns_A': 1, 'owns_B': 0, 'owns_C': 1,
            'age': 30+i, 'income': 300000+(i*50000), 'competitor_price_avg': 10000
        } for i in range(1, 6)])
        result = predictor.predict_batch(df)
        assert 'propensity_score' in result.columns
        assert len(result) == 5
    
    def test_drift_detection(self, sample_features):
        from app.ml.predictor import predictor
        drift = predictor.check_drift(sample_features)
        assert "last_check" in drift
        assert "feature_drifts" in drift

class TestAuthService:
    def test_password_hashing(self):
        from app.services.auth_service import AuthService
        password = "TestPass123"
        hashed = AuthService.hash_password(password)
        assert hashed != password
        assert len(hashed) > 10
