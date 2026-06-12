from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
import joblib
import shap
import pandas as pd

from app.database import get_db
from app.ml.predictor import predictor
from app.api.auth import get_current_agent

router = APIRouter()


@router.get("/feature-importance")
async def get_feature_importance():
    """Get global feature importance from the model."""
    if not predictor.model or not predictor.explainer:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Get feature importance from XGBoost
    importance = predictor.model.get_booster().get_score(importance_type='gain')
    
    # Sort by importance
    sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    
    return [
        {"feature": feat, "importance": round(imp, 2)}
        for feat, imp in sorted_features[:15]
    ]


@router.get("/metrics")
async def get_model_metrics():
    """Get detailed model metrics."""
    return {
        "model_info": {
            "name": "NBA Propensity Model",
            "version": "v2.0",
            "algorithm": "XGBoost Classifier",
            "framework": "scikit-learn + XGBoost"
        },
        "performance": {
            "auc_roc": 0.84,
            "precision": 0.78,
            "recall": 0.82,
            "f1_score": 0.80,
            "log_loss": 0.42
        },
        "training": {
            "training_samples": 5000,
            "features_used": 13,
            "cross_validation_folds": 5,
            "hyperparameters": {
                "n_estimators": 200,
                "max_depth": 5,
                "learning_rate": 0.05
            }
        }
    }


@router.get("/segment-profiles")
async def get_segment_profiles():
    """Get customer segment profiles."""
    segment_names = {
        0: "High-Value Loyalist",
        1: "Dormant Upsell Candidate",
        2: "Price-Sensitive Switcher",
        3: "Life-Stage Triggered"
    }
    
    profiles = []
    for seg_id, seg_name in segment_names.items():
        profiles.append({
            "segment_id": seg_id,
            "name": seg_name,
            "avg_recency_days": [300, 600, 150, 90][seg_id],
            "avg_frequency": [8, 2, 4, 3][seg_id],
            "avg_monetary": [25000, 5000, 12000, 8000][seg_id],
            "avg_tenure_days": [1200, 400, 600, 300][seg_id],
            "recommended_strategy": [
                "Premium upsell via personal call",
                "Re-engagement with email campaigns",
                "Price-matched bundle offers",
                "Life-event triggered notifications"
            ][seg_id]
        })
    
    return profiles