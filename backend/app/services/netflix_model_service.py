"""
Netflix Cross-Sell Propensity Model Service
Loads and manages the trained Netflix model for API predictions.
"""

import pickle
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class NetflixModelService:
    """Service for Netflix cross-sell propensity predictions."""
    
    def __init__(self, model_dir: str = None):
        """
        Initialize the model service.
        
        Args:
            model_dir: Directory containing model files. If None, uses default location.
        """
        if model_dir is None:
            model_dir = Path(__file__).parent.parent.parent / 'models'
        
        self.model_dir = Path(model_dir)
        self.model = None
        self.scaler = None
        self.metadata = {}
        self.feature_columns = []
        self.is_loaded = False
        
        # Try to load model on initialization
        self._load_latest_model()
    
    def _load_latest_model(self) -> bool:
        """Load the most recent model from disk."""
        try:
            # Find the latest model files
            model_files = list(self.model_dir.glob('netflix_xgboost_*.pkl'))
            
            if not model_files:
                logger.warning(f"No model files found in {self.model_dir}")
                return False
            
            # Get the latest model (sorted by timestamp in filename)
            latest_model_file = sorted(model_files)[-1]
            scaler_file = self.model_dir / latest_model_file.name.replace('xgboost', 'scaler')
            metadata_file = self.model_dir / latest_model_file.name.replace('xgboost', 'metadata').replace('.pkl', '.json')
            
            logger.info(f"Loading model from {latest_model_file.name}")
            
            # Load model
            with open(latest_model_file, 'rb') as f:
                self.model = pickle.load(f)
            
            # Load scaler
            if scaler_file.exists():
                with open(scaler_file, 'rb') as f:
                    self.scaler = pickle.load(f)
            else:
                logger.warning(f"Scaler file not found: {scaler_file}")
            
            # Load metadata
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    self.metadata = json.load(f)
                    self.feature_columns = self.metadata.get('features', [])
            else:
                logger.warning(f"Metadata file not found: {metadata_file}")
            
            self.is_loaded = True
            logger.info("✓ Model loaded successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict_propensity(self, customer_features: Dict[str, float]) -> Dict[str, any]:
        """
        Predict cross-sell propensity for a customer.
        
        Args:
            customer_features: Dictionary with feature values
            
        Returns:
            Dictionary with prediction results
        """
        if not self.is_loaded or self.model is None:
            return {
                'success': False,
                'error': 'Model not loaded',
                'propensity_score': None
            }
        
        try:
            # Prepare feature vector
            X = self._prepare_features(customer_features)
            
            if X is None:
                return {
                    'success': False,
                    'error': 'Missing required features',
                    'propensity_score': None
                }
            
            # Scale features
            if self.scaler:
                X_scaled = self.scaler.transform(X)
            else:
                X_scaled = X
            
            # Make prediction
            propensity = float(self.model.predict_proba(X_scaled)[0, 1])
            
            # Classify into segment
            if propensity < 0.25:
                segment = 'Low'
            elif propensity < 0.50:
                segment = 'Medium'
            elif propensity < 0.75:
                segment = 'High'
            else:
                segment = 'Very High'
            
            return {
                'success': True,
                'propensity_score': round(propensity, 4),
                'propensity_percentage': round(propensity * 100, 2),
                'segment': segment,
                'recommended_action': self._get_recommendation(propensity),
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {
                'success': False,
                'error': str(e),
                'propensity_score': None
            }
    
    def _prepare_features(self, customer_features: Dict[str, float]) -> Optional[np.ndarray]:
        """
        Prepare customer features for prediction.
        
        Args:
            customer_features: Dictionary with feature values
            
        Returns:
            Numpy array with features in correct order, or None if missing required features
        """
        try:
            if not self.feature_columns:
                logger.warning("Feature columns not loaded")
                return None
            
            # Create feature vector in correct order
            feature_vector = []
            missing_features = []
            
            for col in self.feature_columns:
                if col in customer_features:
                    feature_vector.append(customer_features[col])
                else:
                    # Use 0 for missing features
                    feature_vector.append(0)
                    missing_features.append(col)
            
            if missing_features:
                logger.debug(f"Missing features, using defaults: {missing_features}")
            
            return np.array([feature_vector])
        
        except Exception as e:
            logger.error(f"Feature preparation error: {e}")
            return None
    
    def _get_recommendation(self, propensity: float) -> str:
        """Get actionable recommendation based on propensity score."""
        if propensity > 0.75:
            return "Prioritize for premium cross-sell offers"
        elif propensity > 0.50:
            return "Recommend targeted cross-sell campaign"
        elif propensity > 0.25:
            return "Consider for nurture campaign"
        else:
            return "Not recommended for immediate cross-sell"
    
    def batch_predict(self, customers: List[Dict[str, float]]) -> List[Dict[str, any]]:
        """
        Make predictions for multiple customers.
        
        Args:
            customers: List of customer feature dictionaries
            
        Returns:
            List of prediction results
        """
        results = []
        for customer in customers:
            result = self.predict_propensity(customer)
            results.append(result)
        return results
    
    def get_model_info(self) -> Dict[str, any]:
        """Get information about the loaded model."""
        return {
            'is_loaded': self.is_loaded,
            'metadata': self.metadata,
            'num_features': len(self.feature_columns),
            'features': self.feature_columns[:10] if self.feature_columns else [],
            'model_type': 'XGBoost Classifier'
        }


# Singleton instance
_model_service = None


def get_model_service(model_dir: str = None) -> NetflixModelService:
    """Get or create the model service singleton."""
    global _model_service
    if _model_service is None:
        _model_service = NetflixModelService(model_dir)
    return _model_service
