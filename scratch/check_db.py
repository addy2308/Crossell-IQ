import sqlite3
import os

db = 'backend/crosssell.db'
print('DB path exists:', os.path.exists(db))
if os.path.exists(db):
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in c.fetchall()]
        print('Tables:', tables)
        for t in tables:
            c.execute(f"SELECT count(*) FROM {t}")
            print(f"- {t}: {c.fetchone()[0]} rows")
        conn.close()
    except Exception as e:
        print("Error reading db:", e)
