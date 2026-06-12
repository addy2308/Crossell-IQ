"""
ML Pipeline: Training Script
Trains XGBoost model and K-Prototypes segmenter.
Logs to MLflow.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

import pandas as pd
import numpy as np
import joblib
import yaml
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score
from xgboost import XGBClassifier
from kmodes.kprototypes import KPrototypes
import mlflow
import mlflow.xgboost

# Load config
with open('../config.yaml', 'r') as f:
    config = yaml.safe_load(f)

def load_data():
    """Load and prepare training data."""
    # Load feature matrix
    df = pd.read_csv('../../data/feature_matrix.csv')
    
    feature_cols = (
        config['features']['numerical'] + 
        config['features']['binary'] + 
        config['features']['count']
    )
    
    X = df[feature_cols]
    y = df['target'] if 'target' in df.columns else df['cross_sell_flag']
    
    return X, y, df

def train_xgboost(X_train, y_train, X_test, y_test):
    """Train XGBoost model and log to MLflow."""
    mlflow.set_tracking_uri(config['mlflow']['tracking_uri'])
    mlflow.set_experiment(config['mlflow']['experiment_name'])
    
    with mlflow.start_run(run_name=f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        # Log params
        params = config['model']['hyperparameters']
        mlflow.log_params(params)
        
        # Train
        model = XGBClassifier(
            **params,
            objective='binary:logistic',
            eval_metric='auc',
            random_state=config['training']['random_state']
        )
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        
        # Evaluate
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        
        auc = roc_auc_score(y_test, y_proba)
        mlflow.log_metric("auc", auc)
        
        # Log model
        mlflow.xgboost.log_model(model, "model")
        
        # Save locally
        os.makedirs('../../models', exist_ok=True)
        joblib.dump(model, '../../models/xgb_model.pkl')
        
        print(f"✓ XGBoost trained. AUC: {auc:.4f}")
        print(classification_report(y_test, y_pred))
        
        return model

def train_segmenter(df):
    """Train K-Prototypes segmentation model."""
    cluster_features = config['features']['numerical'][:6]  # Use top 6 numeric
    
    X_cluster = df[cluster_features].values
    
    kproto = KPrototypes(n_clusters=4, init='Huang', random_state=42)
    clusters = kproto.fit_predict(X_cluster, categorical=[])
    
    # Save
    joblib.dump(kproto, '../../models/kprototypes.pkl')
    
    # Save segment assignments
    df['segment'] = clusters
    df.to_csv('../../data/feature_matrix.csv', index=False)
    
    print(f"✓ Segmenter trained. Segments: {np.unique(clusters)}")
    print(f"  Segment sizes: {np.bincount(clusters)}")
    
    return kproto

if __name__ == '__main__':
    print("=" * 60)
    print("NBA Cross-Sell Engine - Model Training Pipeline")
    print("=" * 60)
    
    # Load data
    print("\n[1/3] Loading data...")
    X, y, df = load_data()
    print(f"  Loaded {len(df)} samples, {X.shape[1]} features")
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=config['training']['test_size'],
        random_state=config['training']['random_state']
    )
    print(f"  Train: {len(X_train)}, Test: {len(X_test)}")
    
    # Train models
    print("\n[2/3] Training XGBoost...")
    model = train_xgboost(X_train, y_train, X_test, y_test)
    
    print("\n[3/3] Training Segmenter...")
    segmenter = train_segmenter(df)
    
    # Save feature columns
    feature_cols = (
        config['features']['numerical'] + 
        config['features']['binary'] + 
        config['features']['count']
    )
    joblib.dump(feature_cols, '../../models/feature_columns.pkl')
    
    print("\n" + "=" * 60)
    print("✓ Training pipeline complete!")
    print("=" * 60)