import grpc
from concurrent import futures
import predict_pb2, predict_pb2_grpc
import pandas as pd
import joblib
from pathlib import Path
import redis
import json
import os
from fastapi import FastAPI
import uvicorn

# ---------- gRPC Service ----------
class PredictorServicer(predict_pb2_grpc.PredictorServicer):
    def __init__(self):
        base = Path(__file__).parent.parent.parent
        self.model = joblib.load(os.getenv('MODEL_PATH', base / 'models' / 'xgb_model.pkl'))
        self.features = joblib.load(base / 'models' / 'feature_columns.pkl')
        self.cache = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

    def Predict(self, request, context):
        # Check cache
        cache_key = str(request.features[:15])  # simple hash
        cached = self.cache.get(cache_key)
        if cached:
            data = json.loads(cached)
            return predict_pb2.PredictResponse(**data)

        X = pd.DataFrame([request.features], columns=self.features).fillna(0)
        proba = float(self.model.predict_proba(X)[0, 1])
        segment = 0 if proba > 0.7 else 1 if proba > 0.5 else 2
        names = {0:"High-Value Loyalist",1:"Dormant Upsell",2:"Price-Sensitive",3:"Life-Stage"}
        response = predict_pb2.PredictResponse(
            propensity=proba,
            segment=segment,
            segment_name=names.get(segment,"Unknown"),
            product="Premium Bundle" if proba > 0.7 else "Standard",
            channel="Phone" if proba > 0.8 else "Email"
        )
        # Cache for 5 minutes
        self.cache.setex(cache_key, 300, json.dumps({
            "propensity": proba, "segment": segment, "segment_name": names.get(segment,"Unknown"),
            "product": "Premium Bundle" if proba > 0.7 else "Standard",
            "channel": "Phone" if proba > 0.8 else "Email"
        }))
        return response

# ---------- REST API (internal) ----------
app = FastAPI()

@app.post("/predict")
async def predict(features: list[float]):
    # Same logic as gRPC
    return {"propensity": 0.85}

def main():
    # Start gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    predict_pb2_grpc.add_PredictorServicer_to_server(PredictorServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    # Start REST server
    uvicorn.run(app, host="0.0.0.0", port=8001)

if __name__ == '__main__':
    main()
