"""
Netflix Prize Dataset Downloader
Downloads the Netflix Prize dataset from Kaggle and organizes it for the pipeline.
"""

import os
import sys
from pathlib import Path
import subprocess
import shutil


def setup_kaggle_credentials():
    """Guide user to setup Kaggle credentials if not present."""
    kaggle_dir = Path.home() / '.kaggle'
    kaggle_json = kaggle_dir / 'kaggle.json'
    
    if kaggle_json.exists():
        print("✓ Kaggle credentials found")
        return True
    
    print("\n❌ Kaggle credentials not found!")
    print("\nSetup Instructions:")
    print("1. Go to: https://www.kaggle.com/settings/account")
    print("2. Click 'Create New API Token'")
    print("3. This downloads kaggle.json")
    print(f"4. Move it to: {kaggle_dir}")
    print("\nOn Windows, the path should be:")
    username = os.getenv('USERNAME')
    print(f"   C:\\Users\\{username}\\.kaggle\\kaggle.json")
    print("\nAfter setup, run this script again.")
    return False


def download_netflix_dataset():
    """Download Netflix Prize dataset from Kaggle."""
    dataset_name = 'netflix-inc/netflix-prize-data'
    data_dir = Path(__file__).parent.parent / 'data' / 'netflix_prize'
    
    # Create data directory
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📥 Downloading Netflix Prize dataset to {data_dir}...")
    print("   This may take 10-30 minutes depending on your internet speed...")
    print("   Dataset size: ~2 GB compressed\n")
    
    try:
        # Download using kaggle CLI
        cmd = [
            'kaggle', 'datasets', 'download',
            '-d', dataset_name,
            '-p', str(data_dir),
            '--unzip'
        ]
        
        result = subprocess.run(cmd, check=True)
        print("✓ Dataset downloaded successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Download failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ kaggle CLI not found. Install with: pip install kaggle")
        return False


def verify_dataset(data_dir):
    """Verify the downloaded dataset."""
    required_files = [
        'combined_data_1.txt',
        'combined_data_2.txt',
        'combined_data_3.txt',
        'combined_data_4.txt',
        'movie_titles.csv'
    ]
    
    data_dir = Path(data_dir)
    missing = [f for f in required_files if not (data_dir / f).exists()]
    
    if not missing:
        print("\n✓ All dataset files verified!")
        for f in required_files:
            size_mb = (data_dir / f).stat().st_size / (1024**2)
            print(f"  - {f} ({size_mb:.1f} MB)")
        return True
    else:
        print(f"\n❌ Missing files: {missing}")
        return False


def main():
    print("=" * 60)
    print("Netflix Prize Dataset Downloader")
    print("=" * 60)
    
    # Check credentials
    if not setup_kaggle_credentials():
        return False
    
    # Download dataset
    if not download_netflix_dataset():
        return False
    
    # Verify
    data_dir = Path(__file__).parent.parent / 'data' / 'netflix_prize'
    if verify_dataset(data_dir):
        print("\n✅ Setup complete! You can now run the data pipeline.")
        print(f"\nDataset location: {data_dir}")
        return True
    
    return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
