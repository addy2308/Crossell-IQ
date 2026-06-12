import pandas as pd
import joblib
from pathlib import Path
import redis
import os
import json
from fastapi import FastAPI
import uvicorn

app = FastAPI()

class PredictionService:
    def __init__(self):
        # In Docker, models are mounted at /app/models
        model_dir = Path(os.getenv('MODEL_DIR', '/app/models'))
        self.model = joblib.load(model_dir / 'xgb_model.pkl')
        self.features = joblib.load(model_dir / 'feature_columns.pkl')
        self.cache = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True)

    def predict(self, features: dict):
        cache_key = None
        if 'customer_id' in features:
            cache_key = f"pred:{features['customer_id']}"
            cached = self.cache.get(cache_key)
            if cached:
                return json.loads(cached)
        
        X = pd.DataFrame([features], columns=self.features).fillna(0)
        proba = float(self.model.predict_proba(X)[0, 1])
        segment = 0 if proba > 0.7 else 1 if proba > 0.5 else 2 if proba > 0.3 else 3
        names = {0:"High-Value Loyalist",1:"Dormant Upsell",2:"Price-Sensitive",3:"Life-Stage"}
        result = {
            "propensity_score": round(proba, 4),
            "segment": segment,
            "segment_name": names.get(segment, "Unknown"),
            "recommended_product": "Premium Bundle" if proba > 0.7 else "Standard Upgrade",
            "recommended_channel": "Phone" if proba > 0.8 else "Email",
            "reasoning": self._reasoning(features, proba)
        }
        if cache_key:
            self.cache.setex(cache_key, 300, json.dumps(result))
        return result

    def _reasoning(self, features, proba):
        reasons = []
        if features.get('renewal_in_30_days', 0): reasons.append("Policy renewal upcoming")
        if features.get('had_claim_60d', 0): reasons.append("Recent claim activity")
        if features.get('engagement_score', 0) > 0.7: reasons.append("High digital engagement")
        if features.get('monetary', 0) > 15000: reasons.append("High customer value")
        return ", ".join(reasons) if reasons else f"Propensity: {proba:.0%}"

    def check_drift(self, sample_df):
        # Simplified drift check
        return {"last_check": "recent", "feature_drifts": {}}

pred_svc = PredictionService()

@app.post("/predict")
async def predict(features: dict):
    return pred_svc.predict(features)

@app.post("/monitor/drift")
async def monitor_drift(sample: dict):
    df = pd.DataFrame(sample)
    return pred_svc.check_drift(df)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8001)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
