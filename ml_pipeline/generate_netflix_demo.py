import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

np.random.seed(42)
n_users = 10000
today = datetime.now()

df = pd.DataFrame({
    'customer_id': range(1, n_users + 1),
    'recency_days': np.random.exponential(scale=30, size=n_users).astype(int),
    'frequency': np.random.poisson(lam=20, size=n_users),
    'monetary': np.random.choice([3.0, 3.5, 4.0, 4.5, 5.0], size=n_users, p=[0.05, 0.15, 0.35, 0.30, 0.15]),
    'tenure_days': np.random.randint(30, 1500, size=n_users),
    'num_products': np.random.choice([5, 10, 20, 30, 50], size=n_users, p=[0.2, 0.3, 0.3, 0.15, 0.05]),
    'engagement_score': np.random.beta(a=2, b=5, size=n_users),
    'days_since_service': np.random.randint(0, 200, size=n_users),
    'had_claim_60d': np.random.choice([0, 1], size=n_users, p=[0.85, 0.15]),
    'renewal_in_30_days': np.random.choice([0, 1], size=n_users, p=[0.7, 0.3]),
    'lost_quotation_count': np.random.poisson(lam=0.5, size=n_users),
    'owns_A': np.random.choice([0, 1], size=n_users, p=[0.6, 0.4]),
    'owns_B': np.random.choice([0, 1], size=n_users, p=[0.5, 0.5]),
    'owns_C': np.random.choice([0, 1], size=n_users, p=[0.3, 0.7]),
    'age': np.random.randint(18, 75, size=n_users),
    'income': np.random.lognormal(mean=10.5, sigma=0.6, size=n_users) * 1000,
})

# Target: high engagement + recent activity + high rating ? likely to cross-sell
df['target'] = (
    (df['engagement_score'] > 0.5) &
    (df['recency_days'] < 60) &
    (df['monetary'] >= 4.0)
).astype(int)

# Save to feature store
base = Path(__file__).parent.parent
db_path = base / 'data' / 'feature_store.db'
conn = sqlite3.connect(db_path)
df.to_sql('features', conn, if_exists='replace', index=False)
conn.close()
print(f"Netflix demo feature store created: {len(df)} users in {db_path}")
