import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

def build_features():
    today = datetime.now()
    base = Path(__file__).parent.parent

    # Load raw data
    cust = pd.read_csv(base / 'data' / 'customers.csv')
    trans = pd.read_csv(base / 'data' / 'transactions.csv', parse_dates=['transaction_date'])
    serv = pd.read_csv(base / 'data' / 'services.csv', parse_dates=['last_service_date'])
    claims = pd.read_csv(base / 'data' / 'claims.csv', parse_dates=['last_claim_date'])
    lost = pd.read_csv(base / 'data' / 'lost_quotations.csv', parse_dates=['lost_date'])

    # RFM
    rfm = trans.groupby('customer_id').agg(
        last_transaction=('transaction_date', 'max'),
        frequency=('transaction_date', 'count'),
        monetary=('amount', 'sum')
    ).reset_index()
    rfm['recency_days'] = (today - rfm['last_transaction']).dt.days

    df = cust.merge(rfm, on='customer_id', how='left').fillna(9999)
    df['tenure_days'] = (today - pd.to_datetime(df['acquisition_date'])).dt.days

    # Product features
    if 'products_owned_str' in df.columns:
        df['owns_A'] = df['products_owned_str'].str.contains('A').astype(int)
        df['owns_B'] = df['products_owned_str'].str.contains('B').astype(int)
        df['owns_C'] = df['products_owned_str'].str.contains('C').astype(int)
        df['num_products'] = df['products_owned_str'].apply(lambda x: len(x.split(',')))
    else:
        df['owns_A'] = df['owns_B'] = df['owns_C'] = 0
        df['num_products'] = 1

    # Service
    svc = serv.groupby('customer_id')['last_service_date'].max().reset_index()
    svc['days_since_service'] = (today - svc['last_service_date']).dt.days
    df = df.merge(svc[['customer_id','days_since_service']], on='customer_id', how='left').fillna(9999)

    # Claims
    clm = claims.groupby('customer_id')['last_claim_date'].max().reset_index()
    clm['had_claim_60d'] = ((today - clm['last_claim_date']).dt.days <= 60).astype(int)
    df = df.merge(clm[['customer_id','had_claim_60d']], on='customer_id', how='left').fillna(0)

    # Lost quotations
    lst = lost.groupby('customer_id').size().reset_index(name='lost_quotation_count')
    df = df.merge(lst, on='customer_id', how='left').fillna(0)

    # Engagement (simulated)
    np.random.seed(42)
    df['engagement_score'] = np.random.uniform(0, 1, len(df))
    df['renewal_in_30_days'] = np.random.choice([0,1], len(df), p=[0.8,0.2])
    df['age'] = np.random.randint(25, 70, len(df))
    df['income'] = np.random.lognormal(mean=10.5, sigma=0.7, size=len(df)) * 1000

    # Target (from existing flag if available)
    if 'cross_sell_flag' in df.columns:
        df['target'] = df['cross_sell_flag']
    else:
        # Simulate target based on features
        df['target'] = (
            (df['had_claim_60d'] * 0.3 + 
             df['renewal_in_30_days'] * 0.3 + 
             df['owns_B'] * 0.2 +
             (df['income'] > 500000).astype(int) * 0.2) > 0.4
        ).astype(int)

    # Select final features
    feature_cols = [
        'recency_days', 'frequency', 'monetary', 'tenure_days',
        'num_products', 'engagement_score', 'days_since_service',
        'had_claim_60d', 'renewal_in_30_days', 'lost_quotation_count',
        'owns_A', 'owns_B', 'owns_C', 'age', 'income'
    ]
    all_cols = ['customer_id', 'target'] + feature_cols
    df = df[all_cols]

    # Save to feature store (SQLite)
    db_path = base / 'data' / 'feature_store.db'
    conn = sqlite3.connect(db_path)
    df.to_sql('features', conn, if_exists='replace', index=False)
    conn.close()

    print(f"Feature pipeline completed. {len(df)} rows saved to {db_path}")
    return df

if __name__ == '__main__':
    build_features()
