import mlflow
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple
import os

class NBAPredictor:
    def __init__(self):
        self.model = None
        self.feature_columns = None
        self.model_version = "unknown"
        self.drift_metrics = {"last_check": None, "feature_drifts": {}}
        self.explainer = None
        self.load_model()
        self._init_explainer()

    def load_model(self):
        try:
            mlflow.set_tracking_uri("file:///" + (Path(__file__).parent.parent.parent.parent / "mlruns").as_posix())
            client = mlflow.tracking.MlflowClient()
            registered_models = client.search_registered_models()
            if registered_models:
                model_name = registered_models[0].name
                latest_versions = client.get_latest_versions(model_name, stages=["None"])
                if latest_versions:
                    version = latest_versions[0].version
                    model_uri = f"models:/{model_name}/{version}"
                    self.model = mlflow.pyfunc.load_model(model_uri)
                    self.model_version = f"{model_name} v{version}"
                    feat_path = Path(__file__).parent.parent.parent.parent / "models" / "feature_columns.pkl"
                    if feat_path.exists():
                        self.feature_columns = joblib.load(feat_path)
                    print(f"Loaded model from MLflow: {self.model_version}")
                    return
        except Exception as e:
            print(f"MLflow load failed: {e}, falling back to local")

        base = Path(__file__).parent.parent.parent.parent
        model_path = base / "models" / "xgb_model.pkl"
        feat_path = base / "models" / "feature_columns.pkl"
        if model_path.exists():
            self.model = joblib.load(model_path)
            self.model_version = "local v2.0"
        if feat_path.exists():
            self.feature_columns = joblib.load(feat_path)
        print(f"Loaded model from local: {self.model_version}")

    def _init_explainer(self):
        try:
            if self.model is not None and hasattr(self.model, "get_booster"):
                import shap
                self.explainer = shap.TreeExplainer(self.model)
            else:
                self.explainer = None
        except Exception:
            self.explainer = None

    def predict(self, features: pd.DataFrame) -> Dict:
        result = self._predict_raw(features)
        if self.explainer is not None and self.feature_columns is not None:
            try:
                X = features[self.feature_columns].fillna(0)
                shap_values = self.explainer.shap_values(X)
                if isinstance(shap_values, list):
                    shap_values = shap_values[1]  # binary classification
                feature_impacts = dict(zip(self.feature_columns, shap_values[0].tolist()))
                sorted_features = sorted(feature_impacts.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
                result["shap_explanation"] = {feat: round(val, 4) for feat, val in sorted_features}
                result["reasoning"] = self._generate_reasoning_from_shap(sorted_features)
            except Exception:
                pass
        return result

    def _predict_raw(self, features: pd.DataFrame) -> Dict:
        if self.model is None or self.feature_columns is None:
            return self._fallback_prediction(features)
        X = features[self.feature_columns].fillna(0)
        try:
            if hasattr(self.model, 'predict_proba'):
                propensity = float(self.model.predict_proba(X)[0, 1])
            else:
                propensity = float(self.model.predict(X)[0])
        except Exception:
            propensity = 0.5
        segment = self._get_segment(features)
        product = self._recommend_product(segment, propensity)
        channel = self._recommend_channel(propensity, features)
        return {
            "propensity_score": round(propensity, 4),
            "segment": segment,
            "segment_name": {0: "High-Value Loyalist", 1: "Dormant Upsell", 2: "Price-Sensitive", 3: "Life-Stage"}.get(segment, "Unknown"),
            "recommended_product": product,
            "recommended_channel": channel,
            "model_version": self.model_version,
            "prediction_timestamp": datetime.utcnow().isoformat()
        }

    def _generate_reasoning_from_shap(self, top_features):
        reasons = []
        for feat, impact in top_features:
            direction = "increases" if impact > 0 else "decreases"
            reasons.append(f"{feat} {direction} propensity by {abs(impact):.3f}")
        return "; ".join(reasons[:3]) if reasons else "No dominant features"

    def predict_batch(self, features_df: pd.DataFrame) -> pd.DataFrame:
        if self.model is None or self.feature_columns is None:
            features_df['propensity_score'] = 0.5
            return features_df
        X = features_df[self.feature_columns].fillna(0)
        try:
            if hasattr(self.model, 'predict_proba'):
                features_df['propensity_score'] = self.model.predict_proba(X)[:, 1]
            else:
                features_df['propensity_score'] = self.model.predict(X)
        except Exception:
            features_df['propensity_score'] = 0.5
        return features_df

    def check_drift(self, current_features: pd.DataFrame) -> Dict:
        self.drift_metrics["last_check"] = datetime.utcnow().isoformat()
        drifts = {}
        if self.feature_columns:
            for col in self.feature_columns[:5]:
                if col in current_features.columns:
                    mean_val = float(current_features[col].mean())
                    drifts[col] = {"current_mean": round(mean_val, 2), "status": "stable" if mean_val > 0 else "warning"}
        self.drift_metrics["feature_drifts"] = drifts
        return self.drift_metrics

    def _get_segment(self, features: pd.DataFrame) -> int:
        try:
            score = float(features.get('monetary', 0).iloc[0])
            return 0 if score > 3.5 else 1 if score > 2.5 else 2 if score > 1.5 else 3
        except Exception:
            return 0

    def _recommend_product(self, segment: int, propensity: float) -> str:
        products = {0: "Premium Investment Bundle", 1: "Extended Protection Plan", 2: "Competitive Match Package", 3: "Essential Upgrade"}
        return products.get(segment, "Standard Offer")

    def _recommend_channel(self, propensity: float, features: pd.DataFrame) -> str:
        if propensity > 0.8: return "Phone"
        try:
            if float(features.get('engagement_score', 0).iloc[0]) > 0.6: return "Email"
        except Exception:
            pass
        return "WhatsApp"

    def _fallback_prediction(self, features: pd.DataFrame) -> Dict:
        return {
            "propensity_score": 0.6,
            "segment": 0,
            "segment_name": "High-Value Loyalist",
            "recommended_product": "Standard Offer",
            "recommended_channel": "Email",
            "reasoning": "Fallback prediction (model unavailable)",
            "model_version": "fallback",
            "prediction_timestamp": datetime.utcnow().isoformat()
        }

predictor = NBAPredictor()
