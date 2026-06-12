import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

class FeatureStore:
    def __init__(self, db_path="data/feature_store.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self._init_db()

    def _init_db(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS features
            (customer_id INTEGER PRIMARY KEY, recency_days INTEGER, frequency INTEGER,
             monetary REAL, tenure_days INTEGER, num_products INTEGER,
             engagement_score REAL, days_since_service INTEGER, had_claim_60d INTEGER,
             renewal_in_30_days INTEGER, lost_quotation_count INTEGER,
             owns_A INTEGER, owns_B INTEGER, owns_C INTEGER,
             age INTEGER, income REAL, target INTEGER, version TEXT, updated_at TEXT)''')
        self.conn.commit()

    def insert_or_update(self, df, version):
        df['version'] = version
        df['updated_at'] = datetime.utcnow().isoformat()
        df.to_sql('features', self.conn, if_exists='replace', index=False)
        self.conn.commit()

    def get_features(self, customer_ids, version="latest"):
        if version == "latest":
            version = pd.read_sql("SELECT MAX(version) FROM features", self.conn).iloc[0,0]
        query = f"SELECT * FROM features WHERE customer_id IN ({','.join(map(str,customer_ids))}) AND version = ?"
        return pd.read_sql(query, self.conn, params=(version,))
