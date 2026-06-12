import shutil
from datetime import datetime
from pathlib import Path

def backup():
    base = Path(__file__).parent.parent
    src = base / 'data' / 'feature_store.db'
    dst = base / 'data' / f'feature_store_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    shutil.copy(src, dst)
    print(f"Backed up to {dst}")

if __name__ == '__main__':
    backup()
