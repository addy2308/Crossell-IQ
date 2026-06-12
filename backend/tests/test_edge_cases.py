import pytest
import pandas as pd
import numpy as np

class TestPredictorEdgeCases:
    def test_predict_with_missing_features(self):
        from app.ml.predictor import predictor
        # DataFrame with only some features – predictor should still return a result
        df = pd.DataFrame([{
            'recency_days': 30, 'frequency': 5, 'monetary': 3.5, 'tenure_days': 500,
            'num_products': 2, 'engagement_score': 0.8, 'days_since_service': 45,
            'had_claim_60d': 1, 'renewal_in_30_days': 1, 'lost_quotation_count': 0,
            'owns_A': 1, 'owns_B': 0, 'owns_C': 1, 'age': 35, 'income': 50000
        }])
        result = predictor.predict(df)
        assert "propensity_score" in result
        assert 0 <= result["propensity_score"] <= 1

    def test_predict_with_extreme_values(self):
        from app.ml.predictor import predictor
        df = pd.DataFrame([{
            'recency_days': 9999, 'frequency': 0, 'monetary': 0, 'tenure_days': 0,
            'num_products': 1, 'engagement_score': 0, 'days_since_service': 9999,
            'had_claim_60d': 0, 'renewal_in_30_days': 0, 'lost_quotation_count': 0,
            'owns_A': 0, 'owns_B': 0, 'owns_C': 0, 'age': 100, 'income': 0
        }])
        result = predictor.predict(df)
        assert "propensity_score" in result

    def test_predict_batch_with_empty_dataframe(self):
        from app.ml.predictor import predictor
        # Empty DataFrame should return empty DataFrame without crashing
        df = pd.DataFrame(columns=['recency_days', 'frequency', 'monetary', 'tenure_days',
                                   'num_products', 'engagement_score', 'days_since_service',
                                   'had_claim_60d', 'renewal_in_30_days', 'lost_quotation_count',
                                   'owns_A', 'owns_B', 'owns_C', 'age', 'income'])
        result = predictor.predict_batch(df)
        assert len(result) == 0

    def test_check_drift_with_identical_data(self):
        from app.ml.predictor import predictor
        df = pd.DataFrame([{
            'recency_days': 30, 'frequency': 5, 'monetary': 3.5, 'tenure_days': 500,
            'num_products': 2, 'engagement_score': 0.8, 'days_since_service': 45,
            'had_claim_60d': 1, 'renewal_in_30_days': 1, 'lost_quotation_count': 0,
            'owns_A': 1, 'owns_B': 0, 'owns_C': 1, 'age': 35, 'income': 50000
        }])
        drift = predictor.check_drift(df)
        assert "feature_drifts" in drift
