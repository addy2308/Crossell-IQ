"""
Model Evaluation Script
Generates evaluation metrics, SHAP analysis, and drift monitoring.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import shap
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, ConfusionMatrixDisplay
)

def evaluate_model():
    """Evaluate trained model and generate report."""
    # Load model and data
    model = joblib.load('../../models/xgb_model.pkl')
    feature_cols = joblib.load('../../models/feature_columns.pkl')
    df = pd.read_csv('../../data/feature_matrix.csv')
    
    X = df[feature_cols]
    y = df['target'] if 'target' in df.columns else df['cross_sell_flag']
    
    # Predictions
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)[:, 1]
    
    # Metrics
    metrics = {
        'accuracy': accuracy_score(y, y_pred),
        'precision': precision_score(y, y_pred),
        'recall': recall_score(y, y_pred),
        'f1_score': f1_score(y, y_pred),
        'auc_roc': roc_auc_score(y, y_proba)
    }
    
    print("=" * 50)
    print("Model Evaluation Report")
    print("=" * 50)
    for name, value in metrics.items():
        print(f"  {name}: {value:.4f}")
    
    # Confusion Matrix
    cm = confusion_matrix(y, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot()
    plt.title('Confusion Matrix')
    plt.savefig('../../data/confusion_matrix.png')
    print("\n✓ Confusion matrix saved")
    
    # SHAP Analysis
    print("\nGenerating SHAP analysis...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X.sample(min(1000, len(X))))
    
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X.sample(min(1000, len(X))), show=False)
    plt.tight_layout()
    plt.savefig('../../data/shap_summary.png')
    print("✓ SHAP summary saved")
    
    # Feature Importance
    importance = model.get_booster().get_score(importance_type='gain')
    importance_df = pd.DataFrame(
        sorted(importance.items(), key=lambda x: x[1], reverse=True),
        columns=['feature', 'importance']
    )
    print("\nTop 10 Features:")
    print(importance_df.head(10).to_string(index=False))
    
    return metrics

if __name__ == '__main__':
    evaluate_model()