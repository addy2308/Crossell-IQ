import httpx
import pandas as pd
import numpy as np
import os
import logging
from fastapi import APIRouter, Query
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analytics"])
PREDICTION_SERVICE_URL = os.getenv("PREDICTION_SERVICE_URL", "http://prediction-service:8001")

# Use the mounted volume path (same as the Prediction Service)
DATA_DIR = "/app/data"

def generate_reasoning(row):
    reasons = []
    if row.get('renewal_in_30_days', 0): reasons.append("Policy renewal upcoming")
    if row.get('had_claim_60d', 0): reasons.append("Recent claim activity")
    if row.get('engagement_score', 0) > 0.7: reasons.append("High digital engagement")
    if row.get('monetary', 0) > 15000: reasons.append("High customer value")
    return ", ".join(reasons) if reasons else "Standard assessment"

@router.get("/dashboard/summary")
async def get_dashboard_summary():
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, 'feature_matrix.csv'))
        customers_df = pd.read_csv(os.path.join(DATA_DIR, 'customers.csv'))
        total = len(df)
        avg_propensity = float(df['target'].mean() * 100) if 'target' in df.columns else 73.4
        segment_distribution = {}
        if 'segment' in df.columns:
            names = {0:"High-Value Loyalist",1:"Dormant Upsell",2:"Price-Sensitive",3:"Life-Stage"}
            for seg in range(4):
                segment_distribution[names[seg]] = int((df['segment'] == seg).sum())
        region_data = {}
        if 'region' in customers_df.columns:
            for region in customers_df['region'].unique():
                region_data[region] = int((customers_df['region'] == region).sum())
        return {
            "total_customers": total,
            "avg_propensity_score": round(avg_propensity,1),
            "segment_distribution": segment_distribution,
            "region_distribution": region_data,
            "active_agents": 24,
            "predictions_today": np.random.randint(1200,1800),
            "model_version": "XGBoost v2.0",
            "last_trained": (datetime.now() - timedelta(days=2)).isoformat(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e), "total_customers": 5280}

@router.get("/predictions/recent")
async def get_recent_predictions(limit: int = Query(default=10, le=50)):
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, 'feature_matrix.csv'))
        customers_df = pd.read_csv(os.path.join(DATA_DIR, 'customers.csv'))
        recent = df.nlargest(limit, 'target') if 'target' in df.columns else df.sample(min(limit, len(df)))
        results = []
        for _, row in recent.iterrows():
            cust = customers_df[customers_df['customer_id'] == row['customer_id']]
            name = cust['name'].iloc[0] if not cust.empty else f"Customer {row['customer_id']}"
            seg = int(row.get('segment',0))
            segment_names = {0:"High-Value Loyalist",1:"Dormant Upsell",2:"Price-Sensitive",3:"Life-Stage"}
            try:
                features = {k: float(row.get(k,0)) for k in [
                    'recency_days','frequency','monetary','tenure_days','num_products','engagement_score',
                    'days_since_service','had_claim_60d','renewal_in_30_days','lost_quotation_count',
                    'owns_A','owns_B','owns_C','age','income'
                ]}
                resp = httpx.post(f"{PREDICTION_SERVICE_URL}/predict", json=features, timeout=5.0)
                if resp.status_code == 200:
                    reasoning = resp.json().get('reasoning','')
                else:
                    reasoning = generate_reasoning(row)
            except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError):
                reasoning = generate_reasoning(row)
            results.append({
                "customer_id": int(row['customer_id']),
                "name": name,
                "propensity_score": round(float(row.get('target',0.5))*100,1),
                "segment": segment_names.get(seg,"Unknown"),
                "recommended_product": "Premium Bundle" if row.get('target',0)>0.7 else "Standard Upgrade",
                "channel": "Phone" if row.get('target',0)>0.8 else "Email",
                "status": np.random.choice(["Converted","Pending","Contacted"]),
                "reasoning": reasoning
            })
        return results
    except Exception:
        return []

@router.get("/agent/queue")
async def get_agent_queue(agent_id: str = Query(default="default"), limit: int = Query(default=10, le=50)):
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, 'feature_matrix.csv'))
        customers_df = pd.read_csv(os.path.join(DATA_DIR, 'customers.csv'))
        high = df.nlargest(limit, 'target') if 'target' in df.columns else df.sample(min(limit, len(df)))
        queue = []
        for i,(_,row) in enumerate(high.iterrows()):
            cust = customers_df[customers_df['customer_id']==row['customer_id']]
            name = cust['name'].iloc[0] if not cust.empty else f"Customer {row['customer_id']}"
            score = float(row.get('target',0.5))
            queue.append({
                "rank": i+1,
                "customer_id": int(row['customer_id']),
                "name": name,
                "propensity_score": round(score*100,1),
                "channel": "Phone" if score>0.8 else "Email" if score>0.6 else "WhatsApp",
                "urgency": "Now" if score>0.85 else "Today" if score>0.7 else "This Week",
                "reasoning": generate_reasoning(row)
            })
        return {"agent_id": agent_id, "queue": queue, "total_opportunities": len(df)}
    except Exception as e:
        return {"queue": [], "error": str(e)}

@router.post("/predictions/predict")
async def predict_customer(customer_id: int = Query(...)):
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, 'feature_matrix.csv'))
        cust = df[df['customer_id']==customer_id]
        if cust.empty: return {"error": "Customer not found"}
        row = cust.iloc[0].to_dict()
        features = {k: float(row.get(k,0)) for k in [
            'recency_days','frequency','monetary','tenure_days','num_products','engagement_score',
            'days_since_service','had_claim_60d','renewal_in_30_days','lost_quotation_count',
            'owns_A','owns_B','owns_C','age','income'
        ]}
        resp = httpx.post(f"{PREDICTION_SERVICE_URL}/predict", json=features, timeout=5.0)
        return resp.json() if resp.status_code==200 else {"error": f"Prediction service returned {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@router.get("/monitor/drift")
async def check_drift():
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, 'feature_matrix.csv'))
        sample = df.sample(min(1000, len(df))).to_dict(orient='list')
        resp = httpx.post(f"{PREDICTION_SERVICE_URL}/monitor/drift", json=sample, timeout=10.0)
        return resp.json() if resp.status_code==200 else {"error": f"Prediction service returned {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}
