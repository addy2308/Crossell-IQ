from fastapi import APIRouter
import pandas as pd
import numpy as np
import os
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import joblib
from pathlib import Path

router = APIRouter(prefix="/evaluation", tags=["Model Evaluation"])

@router.get("/report")
async def get_evaluation_report():
    """Generate a comprehensive model evaluation report on test data."""
    try:
        base = Path(__file__).parent.parent.parent.parent
        df = pd.read_csv(base / 'data' / 'feature_matrix.csv')
        model = joblib.load(base / 'models' / 'xgb_model.pkl')
        features = joblib.load(base / 'models' / 'feature_columns.pkl')

        X = df[features].fillna(0)
        y = df['target'] if 'target' in df.columns else np.zeros(len(df))

        from sklearn.model_selection import train_test_split
        _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        report = classification_report(y_test, y_pred, output_dict=True)
        cm = confusion_matrix(y_test, y_pred).tolist()
        auc = roc_auc_score(y_test, y_proba)

        return {
            "model_metrics": {
                "auc": round(auc, 4),
                "precision": round(report['1']['precision'], 4),
                "recall": round(report['1']['recall'], 4),
                "f1_score": round(report['1']['f1-score'], 4)
            },
            "confusion_matrix": cm,
            "full_report": report
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/compare")
async def compare_models():
    """Compare the current model with the previous version (if available)."""
    base = Path(__file__).parent.parent.parent.parent
    current_path = base / 'models' / 'xgb_model.pkl'
    previous_path = base / 'models' / 'xgb_model_previous.pkl'

    result = {"current_model": {}, "previous_model": {}, "comparison": {}}

    if current_path.exists():
        model = joblib.load(current_path)
        features = joblib.load(base / 'models' / 'feature_columns.pkl')
        df = pd.read_csv(base / 'data' / 'feature_matrix.csv')
        X = df[features].fillna(0)
        y = df['target'] if 'target' in df.columns else np.zeros(len(df))
        _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        y_proba = model.predict_proba(X_test)[:, 1]
        result["current_model"]["auc"] = round(roc_auc_score(y_test, y_proba), 4)

    if previous_path.exists():
        model_prev = joblib.load(previous_path)
        y_proba_prev = model_prev.predict_proba(X_test)[:, 1]
        result["previous_model"]["auc"] = round(roc_auc_score(y_test, y_proba_prev), 4)
        result["comparison"]["auc_change"] = round(result["current_model"]["auc"] - result["previous_model"]["auc"], 4)

    return result
