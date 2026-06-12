#!/usr/bin/env python3
"""
Netflix Dataset Download Monitor & Auto-Trainer
Monitors download progress and automatically starts training when complete
"""

import os
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DownloadMonitor:
    """Monitor Netflix dataset download and trigger training"""
    
    def __init__(self, target_size_mb=683, check_interval=30):
        """
        Initialize monitor
        
        Args:
            target_size_mb: Expected final download size (683 MB)
            check_interval: Check every N seconds
        """
        self.target_size_mb = target_size_mb
        self.check_interval = check_interval
        self.zip_path = Path(__file__).parent.parent / 'data' / 'netflix_prize' / 'netflix-prize-data.zip'
        self.state_file = Path(__file__).parent.parent / '.download_state.json'
    
    def get_current_size_mb(self):
        """Get current download size in MB"""
        if not self.zip_path.exists():
            return 0
        return self.zip_path.stat().st_size / (1024 ** 2)
    
    def get_progress_percentage(self):
        """Get download progress as percentage"""
        current = self.get_current_size_mb()
        return (current / self.target_size_mb) * 100
    
    def save_state(self, state):
        """Save monitoring state to file"""
        state['timestamp'] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self):
        """Load previous monitoring state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {}
    
    def monitor(self, auto_train=True, verbose=True):
        """
        Monitor download and auto-train when complete
        
        Args:
            auto_train: Automatically start training when download completes
            verbose: Print detailed progress
        """
        logger.info("🔍 Starting Netflix Dataset Download Monitor")
        logger.info(f"📁 Monitoring: {self.zip_path}")
        logger.info(f"🎯 Target: {self.target_size_mb} MB")
        logger.info(f"⏱️  Check interval: {self.check_interval}s")
        
        previous_size = 0
        stall_count = 0
        max_stalls = 10  # Stop after 10 consecutive no-change checks
        
        while True:
            try:
                current_size = self.get_current_size_mb()
                progress = self.get_progress_percentage()
                
                # Print progress
                if verbose or progress % 10 < 1:  # Print at 10% increments
                    bar_length = 50
                    filled = int(bar_length * progress / 100)
                    bar = '█' * filled + '░' * (bar_length - filled)
                    logger.info(
                        f"[{bar}] {progress:6.1f}% ({current_size:7.0f}/{self.target_size_mb} MB)"
                    )
                
                # Check for stalled download
                if current_size == previous_size:
                    stall_count += 1
                    if stall_count >= max_stalls and current_size > 0:
                        logger.warning("⚠️  Download appears stalled")
                        logger.warning("Please check Kaggle API credentials and network connection")
                        return False
                else:
                    stall_count = 0
                
                # Check if download complete
                if current_size >= self.target_size_mb * 0.95:  # 95% = complete
                    logger.info("✅ Download complete!")
                    self.save_state({
                        'status': 'download_complete',
                        'size_mb': current_size,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    if auto_train:
                        logger.info("\n🚀 Starting automatic model training...")
                        return self.start_training()
                    else:
                        logger.info("⏸️  Download complete. Waiting for manual training start.")
                        return True
                
                previous_size = current_size
                time.sleep(self.check_interval)
            
            except KeyboardInterrupt:
                logger.info("\n⏹️  Monitor stopped by user")
                return False
            except Exception as e:
                logger.error(f"❌ Monitor error: {e}")
                time.sleep(self.check_interval)
    
    def start_training(self):
        """Start model training after download completes"""
        try:
            ml_pipeline_dir = Path(__file__).parent.parent / 'ml_pipeline'
            integration_script = ml_pipeline_dir / 'netflix_integration.py'
            
            if not integration_script.exists():
                logger.error(f"Integration script not found: {integration_script}")
                return False
            
            logger.info(f"🎓 Running: {integration_script}")
            logger.info("This will take 10-30 minutes depending on dataset size...")
            
            # Run integration script with mode 2 (quick sample)
            result = subprocess.run(
                [sys.executable, str(integration_script)],
                cwd=str(ml_pipeline_dir),
                input='2\n',  # Select quick mode
                text=True,
                capture_output=False
            )
            
            if result.returncode == 0:
                logger.info("✅ Model training completed successfully!")
                self.save_state({
                    'status': 'training_complete',
                    'timestamp': datetime.now().isoformat()
                })
                return True
            else:
                logger.error(f"❌ Training failed with return code: {result.returncode}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Training error: {e}")
            return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Netflix Download Monitor & Auto-Trainer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_monitor.py                    # Monitor and auto-train
  python download_monitor.py --no-train         # Monitor only
  python download_monitor.py --interval 60      # Check every 60 seconds
        """
    )
    
    parser.add_argument(
        '--no-train',
        action='store_true',
        help='Monitor download but do not auto-train'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Check interval in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--target-size',
        type=int,
        default=683,
        help='Expected download size in MB (default: 683)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Reduce output verbosity'
    )
    
    args = parser.parse_args()
    
    monitor = DownloadMonitor(
        target_size_mb=args.target_size,
        check_interval=args.interval
    )
    
    success = monitor.monitor(
        auto_train=not args.no_train,
        verbose=not args.quiet
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
