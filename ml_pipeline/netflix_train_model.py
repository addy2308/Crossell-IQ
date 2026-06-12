"""
Netflix Cross-Sell Model Training
Trains XGBoost propensity model using Netflix dataset.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple
import logging
import pickle
import json
from datetime import datetime

try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import (
        roc_auc_score, roc_curve, confusion_matrix,
        precision_recall_curve, f1_score, accuracy_score
    )
    import matplotlib.pyplot as plt
except ImportError as e:
    logging.warning(f"Optional dependencies not installed: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NetflixCrossSellModel:
    """Train and evaluate cross-sell propensity model."""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or Path(__file__).parent / 'config.yaml'
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.metrics = {}
    
    def load_features(self, features_path: str = None) -> pd.DataFrame:
        """Load pre-engineered features."""
        if features_path is None:
            features_path = Path(__file__).parent.parent / 'data' / 'processed' / 'netflix_features.parquet'
        
        logger.info(f"Loading features from {features_path}")
        
        if not Path(features_path).exists():
            logger.error(f"Features file not found: {features_path}")
            return pd.DataFrame()
        
        df = pd.read_parquet(features_path)
        logger.info(f"Loaded features for {len(df)} users")
        logger.info(f"Columns: {df.columns.tolist()}")
        
        return df
    
    def prepare_training_data(self, features_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data.
        Creates target variable based on cross-sell readiness.
        """
        logger.info("Preparing training data...")
        
        if features_df.empty:
            logger.error("No features provided")
            return pd.DataFrame(), pd.Series()
        
        # Use cross_sell_propensity as target (if available)
        if 'cross_sell_propensity' in features_df.columns:
            # Convert to binary: top 30% = positive class
            threshold = features_df['cross_sell_propensity'].quantile(0.7)
            y = (features_df['cross_sell_propensity'] >= threshold).astype(int)
        else:
            logger.warning("cross_sell_propensity not found, using random target")
            y = np.random.binomial(1, 0.3, len(features_df))
        
        # Select features for modeling
        exclude_cols = ['user_id', 'cross_sell_propensity', 'crosssell_segment',
                       'first_rating_date', 'last_rating_date', 'title']
        
        feature_cols = [c for c in features_df.columns 
                       if c not in exclude_cols and features_df[c].dtype in [np.int64, np.float64]]
        
        X = features_df[feature_cols].copy()
        
        # Handle missing values
        X = X.fillna(X.mean(numeric_only=True))
        
        self.feature_columns = feature_cols
        
        logger.info(f"Training data shape: {X.shape}")
        logger.info(f"Target distribution: {y.value_counts().to_dict()}")
        logger.info(f"Features: {feature_cols}")
        
        return X, y
    
    def train_model(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2):
        """Train XGBoost model."""
        logger.info("Training XGBoost model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=42,
            stratify=y
        )
        
        logger.info(f"Train set: {X_train.shape}")
        logger.info(f"Test set: {X_test.shape}")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train XGBoost
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            verbosity=1
        )
        
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            early_stopping_rounds=20,
            verbose=False
        )
        
        logger.info("Model training complete")
        
        # Evaluate
        self._evaluate_model(X_test_scaled, y_test)
        
        return self.model
    
    def _evaluate_model(self, X_test_scaled: np.ndarray, y_test: pd.Series):
        """Evaluate model performance."""
        logger.info("\nModel Evaluation")
        logger.info("="*60)
        
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba)
        f1 = f1_score(y_test, y_pred)
        
        logger.info(f"Accuracy:  {accuracy:.4f}")
        logger.info(f"AUC-ROC:   {auc:.4f}")
        logger.info(f"F1-Score:  {f1:.4f}")
        
        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        
        logger.info(f"Sensitivity: {sensitivity:.4f}")
        logger.info(f"Specificity: {specificity:.4f}")
        logger.info(f"Precision:   {precision:.4f}")
        
        self.metrics = {
            'accuracy': float(accuracy),
            'auc_roc': float(auc),
            'f1_score': float(f1),
            'sensitivity': float(sensitivity),
            'specificity': float(specificity),
            'precision': float(precision)
        }
    
    def get_feature_importance(self, top_n: int = 15) -> pd.DataFrame:
        """Get feature importance."""
        if self.model is None:
            logger.error("Model not trained yet")
            return pd.DataFrame()
        
        importance_dict = self.model.get_booster().get_score(importance_type='weight')
        
        # Convert to DataFrame
        importance_df = pd.DataFrame(
            list(importance_dict.items()),
            columns=['feature', 'importance']
        ).sort_values('importance', ascending=False)
        
        # Map feature names
        if self.feature_columns:
            feature_map = {f'f{i}': col for i, col in enumerate(self.feature_columns)}
            importance_df['feature'] = importance_df['feature'].map(
                lambda x: feature_map.get(x, x)
            )
        
        logger.info("\nTop Feature Importance")
        logger.info("="*60)
        for idx, row in importance_df.head(top_n).iterrows():
            logger.info(f"{row['feature']:<30} {row['importance']:>8.0f}")
        
        return importance_df.head(top_n)
    
    def save_model(self, output_dir: str = None):
        """Save model artifacts."""
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / 'models'
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save model
        model_path = output_dir / f'netflix_xgboost_{timestamp}.pkl'
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Model saved: {model_path}")
        
        # Save scaler
        scaler_path = output_dir / f'netflix_scaler_{timestamp}.pkl'
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        logger.info(f"Scaler saved: {scaler_path}")
        
        # Save metadata
        metadata = {
            'timestamp': timestamp,
            'features': self.feature_columns,
            'metrics': self.metrics,
            'model_type': 'XGBClassifier',
            'dataset': 'Netflix Prize'
        }
        
        metadata_path = output_dir / f'netflix_metadata_{timestamp}.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Metadata saved: {metadata_path}")
        
        return model_path, scaler_path, metadata_path
    
    def make_predictions(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions on new data."""
        if self.model is None:
            logger.error("Model not trained")
            return np.array([])
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)[:, 1]


def main():
    """Run complete training pipeline."""
    logger.info("="*70)
    logger.info("NETFLIX CROSS-SELL MODEL TRAINING")
    logger.info("="*70)
    
    # Initialize model
    model_trainer = NetflixCrossSellModel()
    
    # Load features
    features_df = model_trainer.load_features()
    
    if features_df.empty:
        logger.error("Failed to load features")
        return False
    
    # Prepare data
    X, y = model_trainer.prepare_training_data(features_df)
    
    if X.empty:
        logger.error("Failed to prepare training data")
        return False
    
    # Train model
    try:
        model_trainer.train_model(X, y)
        
        # Get feature importance
        model_trainer.get_feature_importance()
        
        # Save model
        model_trainer.save_model()
        
        logger.info("\n" + "="*70)
        logger.info("✓ Training complete!")
        logger.info("="*70)
        
        return True
    
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
