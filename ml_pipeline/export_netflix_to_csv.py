import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path

base = Path(__file__).parent.parent
db_path = base / 'data' / 'feature_store.db'
conn = sqlite3.connect(db_path)
df = pd.read_sql("SELECT * FROM features", conn)
conn.close()

# Add synthetic customer names and regions (since Netflix data has no demographics)
np.random.seed(42)
n = len(df)
df['name'] = [f"User {i}" for i in df['customer_id']]
df['email'] = [f"user{i}@netflix.com" for i in df['customer_id']]
regions = ['North', 'South', 'East', 'West', 'Central', 'Northeast']
df['region'] = np.random.choice(regions, size=n)
df['age'] = np.random.randint(18, 75, size=n)
df['acquisition_date'] = pd.date_range(end='2024-01-01', periods=n, freq='D')
df['products_owned_str'] = np.random.choice(['Life Insurance,Health Insurance', 'Vehicle Insurance', 'Home Insurance,Travel Insurance', 'Health Insurance'], size=n)
df['cross_sell_flag'] = df['target']

# Save customers.csv (needed by analytics)
cust_cols = ['customer_id', 'name', 'email', 'acquisition_date', 'region', 'age', 'products_owned_str', 'cross_sell_flag']
df[cust_cols].to_csv(base / 'data' / 'customers.csv', index=False)

# Save feature_matrix.csv (needed by predictions)
feature_cols = ['customer_id', 'target', 'recency_days', 'frequency', 'monetary', 'tenure_days',
                'num_products', 'engagement_score', 'days_since_service', 'had_claim_60d',
                'renewal_in_30_days', 'lost_quotation_count', 'owns_A', 'owns_B', 'owns_C', 'age', 'income']
df[feature_cols].to_csv(base / 'data' / 'feature_matrix.csv', index=False)

print(f"Exported {n} Netflix customers to CSV files.")
