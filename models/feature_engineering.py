import pandas as pd
import numpy as np
from datetime import datetime

def build_features():
    today = datetime.now()
    
    cust = pd.read_csv('data/customers.csv')
    trans = pd.read_csv('data/transactions.csv', parse_dates=['transaction_date'])
    serv = pd.read_csv('data/services.csv', parse_dates=['last_service_date'])
    claims = pd.read_csv('data/claims.csv', parse_dates=['last_claim_date'])
    lost = pd.read_csv('data/lost_quotations.csv', parse_dates=['lost_date'])
    
    rfm = trans.groupby('customer_id').agg(
        last_transaction_date=('transaction_date','max'),
        frequency=('transaction_date','count'),
        monetary=('amount','sum')
    ).reset_index()
    rfm['recency_days'] = (today - rfm['last_transaction_date']).dt.days
    
    df = cust.merge(rfm, on='customer_id', how='left').fillna(9999)
    df['tenure_days'] = (today - pd.to_datetime(df['acquisition_date'])).dt.days
    
    df['owns_A'] = df['products_owned_str'].str.contains('A').astype(int)
    df['owns_B'] = df['products_owned_str'].str.contains('B').astype(int)
    df['owns_C'] = df['products_owned_str'].str.contains('C').astype(int)
    df['num_products'] = df['products_owned_str'].apply(lambda x: len(x.split(',')))
    
    serv_agg = serv.groupby('customer_id')['last_service_date'].max().reset_index()
    serv_agg['days_since_service'] = (today - serv_agg['last_service_date']).dt.days
    df = df.merge(serv_agg[['customer_id','days_since_service']], on='customer_id', how='left').fillna(9999)
    
    claims_agg = claims.groupby('customer_id')['last_claim_date'].max().reset_index()
    claims_agg['had_claim_60d'] = ((today - claims_agg['last_claim_date']).dt.days <= 60).astype(int)
    df = df.merge(claims_agg[['customer_id','had_claim_60d']], on='customer_id', how='left').fillna(0)
    
    lost_agg = lost.groupby('customer_id').agg(
        lost_quotation_count=('competitor','count'),
        competitor_price_avg=('competitor_price','mean')
    ).reset_index()
    df = df.merge(lost_agg, on='customer_id', how='left').fillna(0)
    
    np.random.seed(42)
    df['renewal_in_30_days'] = np.random.choice([0,1], len(df), p=[0.8,0.2])
    df['engagement_score'] = np.random.uniform(0,1, len(df))
    
    df['target'] = df['cross_sell_flag']
    
    drop_cols = ['name','email','region','products_owned_str','acquisition_date','last_transaction_date','cross_sell_flag']
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    
    return df
