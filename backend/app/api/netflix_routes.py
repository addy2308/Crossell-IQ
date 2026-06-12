"""
Netflix Cross-Sell Propensity API Endpoints
REST API for cross-sell propensity predictions using the Netflix model.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import logging

from backend.app.services.netflix_model_service import get_model_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/netflix",
    tags=["netflix", "predictions"]
)

# Request/Response models
class CustomerFeaturesRequest(BaseModel):
    """Request model for single customer prediction."""
    total_ratings: Optional[int] = Field(None, description="Total number of ratings")
    unique_movies: Optional[int] = Field(None, description="Number of unique movies rated")
    mean_rating: Optional[float] = Field(None, description="Average rating given")
    std_rating: Optional[float] = Field(None, description="Standard deviation of ratings")
    tenure_days: Optional[int] = Field(None, description="Days since first rating")
    recency_days: Optional[int] = Field(None, description="Days since last rating")
    rating_velocity: Optional[float] = Field(None, description="Ratings per day")
    is_active_6m: Optional[int] = Field(None, description="Active in last 6 months (0/1)")
    is_active_1y: Optional[int] = Field(None, description="Active in last year (0/1)")
    rating_consistency: Optional[float] = Field(None, description="Rating consistency score")
    engagement_score: Optional[float] = Field(None, description="Overall engagement score")
    
    class Config:
        schema_extra = {
            "example": {
                "total_ratings": 250,
                "unique_movies": 180,
                "mean_rating": 3.8,
                "std_rating": 1.2,
                "tenure_days": 500,
                "recency_days": 15,
                "rating_velocity": 0.5,
                "is_active_6m": 1,
                "is_active_1y": 1,
                "rating_consistency": 0.85,
                "engagement_score": 75
            }
        }


class BatchPredictionRequest(BaseModel):
    """Request model for batch predictions."""
    customers: List[Dict[str, Any]] = Field(..., description="List of customer feature dictionaries")


class CrossSellPredictionResponse(BaseModel):
    """Response model for cross-sell prediction."""
    success: bool
    propensity_score: Optional[float] = Field(None, description="Propensity score (0-1)")
    propensity_percentage: Optional[float] = Field(None, description="Propensity as percentage")
    segment: Optional[str] = Field(None, description="Customer segment (Low/Medium/High/Very High)")
    recommended_action: Optional[str] = Field(None, description="Recommended marketing action")
    timestamp: Optional[str] = Field(None, description="Prediction timestamp")
    error: Optional[str] = Field(None, description="Error message if prediction failed")


class ModelInfoResponse(BaseModel):
    """Response model for model information."""
    is_loaded: bool
    model_type: str
    num_features: int
    features: List[str]
    metadata: Dict[str, Any] = {}


# Endpoints

@router.post("/predict", response_model=CrossSellPredictionResponse)
async def predict_cross_sell_propensity(request: CustomerFeaturesRequest):
    """
    Predict cross-sell propensity for a single customer.
    
    Returns a propensity score (0-1) indicating likelihood of accepting a cross-sell offer,
    along with customer segment and recommended actions.
    """
    try:
        # Convert request to dictionary
        features = request.dict(exclude_none=True)
        
        # Get prediction
        model_service = get_model_service()
        result = model_service.predict_propensity(features)
        
        return CrossSellPredictionResponse(**result)
    
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/batch", response_model=List[CrossSellPredictionResponse])
async def predict_batch(request: BatchPredictionRequest):
    """
    Predict cross-sell propensity for multiple customers.
    
    Accepts a list of customer feature dictionaries and returns propensity scores for each.
    Useful for bulk customer scoring and segmentation.
    """
    try:
        if not request.customers:
            raise ValueError("Empty customer list")
        
        model_service = get_model_service()
        results = model_service.batch_predict(request.customers)
        
        return [CrossSellPredictionResponse(**result) for result in results]
    
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/info", response_model=ModelInfoResponse)
async def get_model_information():
    """
    Get information about the loaded Netflix cross-sell model.
    
    Returns model type, features used, and metadata about the model version.
    """
    try:
        model_service = get_model_service()
        info = model_service.get_model_info()
        return ModelInfoResponse(**info)
    
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/status")
async def get_model_status():
    """
    Check if the Netflix model is loaded and ready for predictions.
    """
    try:
        model_service = get_model_service()
        return {
            "model_loaded": model_service.is_loaded,
            "status": "ready" if model_service.is_loaded else "not_loaded",
            "num_features": len(model_service.feature_columns),
            "model_type": "XGBoost Cross-Sell Propensity Classifier"
        }
    
    except Exception as e:
        logger.error(f"Error checking model status: {e}")
        return {
            "model_loaded": False,
            "status": "error",
            "error": str(e)
        }


@router.post("/health-check")
async def health_check():
    """
    Health check endpoint for the Netflix model service.
    """
    model_service = get_model_service()
    return {
        "service": "netflix-cross-sell",
        "status": "healthy" if model_service.is_loaded else "degraded",
        "model_ready": model_service.is_loaded,
        "version": "1.0"
    }


# Example usage documentation
"""
USAGE EXAMPLES:

1. Single Customer Prediction:
   POST /api/netflix/predict
   {
     "total_ratings": 250,
     "unique_movies": 180,
     "mean_rating": 3.8,
     "tenure_days": 500,
     "recency_days": 15,
     "rating_velocity": 0.5,
     "is_active_6m": 1,
     "engagement_score": 75
   }

2. Batch Predictions:
   POST /api/netflix/predict/batch
   {
     "customers": [
       {"total_ratings": 250, "mean_rating": 3.8, ...},
       {"total_ratings": 150, "mean_rating": 3.5, ...}
     ]
   }

3. Check Model Status:
   GET /api/netflix/model/status

4. Get Model Information:
   GET /api/netflix/model/info
"""
