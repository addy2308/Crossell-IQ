import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

TARGET_USERS = 10000

def load_netflix_data():
    base = Path(__file__).parent.parent / 'data'
    rows = []
    users_seen = set()
    for file_num in range(1, 5):
        file_path = base / f'combined_data_{file_num}.txt'
        if not file_path.exists():
            print(f"Skipping {file_path}")
            continue
        current_movie_id = None
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.endswith(':'):
                    current_movie_id = int(line.replace(':', ''))
                else:
                    parts = line.split(',')
                    if len(parts) == 3:
                        user_id = int(parts[0])
                        rating = int(parts[1])
                        date_str = parts[2]
                        if user_id not in users_seen:
                            users_seen.add(user_id)
                        rows.append([user_id, current_movie_id, rating, date_str])
                        if len(users_seen) >= TARGET_USERS:
                            break
            if len(users_seen) >= TARGET_USERS:
                break
        if len(users_seen) >= TARGET_USERS:
            break
    df = pd.DataFrame(rows, columns=['user_id', 'movie_id', 'rating', 'date'])
    df['date'] = pd.to_datetime(df['date'])
    print(f"Loaded {len(df)} ratings from {len(users_seen)} users")
    return df

def build_features():
    base = Path(__file__).parent.parent
    df = load_netflix_data()
    if df.empty:
        print("No data loaded.")
        return

    today = df['date'].max()
    user_agg = df.groupby('user_id').agg(
        recency_days=('date', lambda x: (today - x.max()).days),
        frequency=('movie_id', 'count'),
        monetary=('rating', 'mean'),
        last_rating_date=('date', 'max'),
        first_rating_date=('date', 'min')
    ).reset_index()
    user_agg['tenure_days'] = (user_agg['last_rating_date'] - user_agg['first_rating_date']).dt.days
    user_agg['num_products'] = user_agg['frequency'].clip(upper=50)
    user_agg['engagement_score'] = np.log1p(user_agg['frequency']) / np.log1p(user_agg['frequency'].max())
    user_agg['days_since_service'] = user_agg['recency_days'] + np.random.randint(-30, 30, len(user_agg))
    user_agg['had_claim_60d'] = 0
    user_agg['renewal_in_30_days'] = np.random.choice([0,1], len(user_agg), p=[0.8,0.2])
    user_agg['owns_A'] = np.random.choice([0,1], len(user_agg))
    user_agg['owns_B'] = np.random.choice([0,1], len(user_agg))
    user_agg['owns_C'] = np.random.choice([0,1], len(user_agg))
    user_agg['lost_quotation_count'] = 0
    user_agg['age'] = np.random.randint(18, 70, len(user_agg))
    user_agg['income'] = np.random.lognormal(mean=10.5, sigma=0.5, size=len(user_agg)) * 1000

    recent_ratings = df[df['date'] >= today - timedelta(days=180)]
    high_ratings = recent_ratings[recent_ratings['rating'] >= 4]
    target_users = high_ratings['user_id'].unique()
    user_agg['target'] = user_agg['user_id'].isin(target_users).astype(int)

    feature_cols = [
        'recency_days', 'frequency', 'monetary', 'tenure_days',
        'num_products', 'engagement_score', 'days_since_service',
        'had_claim_60d', 'renewal_in_30_days', 'lost_quotation_count',
        'owns_A', 'owns_B', 'owns_C', 'age', 'income'
    ]
    user_agg.rename(columns={'user_id': 'customer_id'}, inplace=True)
    all_cols = ['customer_id', 'target'] + feature_cols
    df_out = user_agg[all_cols]

    db_path = base / 'data' / 'feature_store.db'
    conn = sqlite3.connect(db_path)
    df_out.to_sql('features', conn, if_exists='replace', index=False)
    conn.close()
    print(f"Feature store saved with {len(df_out)} users")

if __name__ == '__main__':
    build_features()
