import shutil
from pathlib import Path
import sys

def restore(backup_file=None):
    base = Path(__file__).parent.parent
    if backup_file:
        src = base / backup_file
    else:
        backups = sorted(base.glob('data/feature_store_backup_*.db'))
        if not backups:
            print("No backups found")
            return
        src = backups[-1]
    dst = base / 'data' / 'feature_store.db'
    shutil.copy(src, dst)
    print(f"Restored from {src}")

if __name__ == '__main__':
    restore(sys.argv[1] if len(sys.argv) > 1 else None)
