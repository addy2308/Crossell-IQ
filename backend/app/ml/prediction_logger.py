import sqlite3
from datetime import datetime
from pathlib import Path

class PredictionLogger:
    def __init__(self, db_path="data/predictions.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self._init_db()

    def _init_db(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS prediction_log
            (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER,
             propensity_score REAL, segment INTEGER, product TEXT,
             channel TEXT, model_version TEXT, timestamp TEXT,
             response_time_ms REAL, cache_hit INTEGER DEFAULT 0)''')
        self.conn.commit()

    def log(self, customer_id, prediction, response_time_ms=0, cache_hit=0):
        self.conn.execute('''INSERT INTO prediction_log
            (customer_id, propensity_score, segment, product, channel, model_version, timestamp, response_time_ms, cache_hit)
            VALUES (?,?,?,?,?,?,?,?,?)''',
            (customer_id, prediction.get('propensity_score'), prediction.get('segment'),
             prediction.get('recommended_product'), prediction.get('recommended_channel'),
             prediction.get('model_version'), datetime.utcnow().isoformat(), response_time_ms, cache_hit))
        self.conn.commit()

    def get_stats(self, hours=24):
        cursor = self.conn.execute('''SELECT COUNT(*), AVG(propensity_score), AVG(response_time_ms),
                                      SUM(cache_hit) FROM prediction_log
                                      WHERE timestamp > datetime('now', '-' || ? || ' hours')''', (hours,))
        row = cursor.fetchone()
        return {"total_predictions": row[0], "avg_propensity": row[1], "avg_latency_ms": row[2], "cache_hit_rate": row[3] / max(row[0], 1)}
