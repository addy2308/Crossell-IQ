"""
Netflix Prize Dataset Integration Script
Complete workflow: Download → Validate → Feature Engineer → Train Model
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner(title: str):
    """Print a formatted banner."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are installed."""
    print_banner("CHECKING DEPENDENCIES")
    
    dependencies = {
        'pandas': 'Data processing',
        'numpy': 'Numerical computing',
        'xgboost': 'ML model training',
        'sklearn': 'ML utilities',  # Note: package is 'scikit-learn' but imported as 'sklearn'
    }
    
    results = {}
    missing = []
    
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"✓ {package:<15} {description}")
            results[package] = True
        except ImportError:
            print(f"✗ {package:<15} {description} - MISSING")
            results[package] = False
            missing.append(package)
    
    if missing:
        print(f"\n⚠ Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r backend/requirements.txt")
        return results
    
    print("\n✓ All dependencies installed!")
    return results


def step_1_setup_kaggle() -> bool:
    """Step 1: Setup Kaggle credentials."""
    print_banner("STEP 1: SETUP KAGGLE CREDENTIALS")
    
    from pathlib import Path
    import os
    
    kaggle_dir = Path.home() / '.kaggle'
    kaggle_json = kaggle_dir / 'kaggle.json'
    
    print("Checking Kaggle API credentials...")
    
    if kaggle_json.exists():
        print(f"✓ Kaggle credentials found at {kaggle_json}")
        return True
    
    print("❌ Kaggle credentials not found!")
    print("\nSetup Instructions:")
    print("1. Visit: https://www.kaggle.com/settings/account")
    print("2. Click 'Create New API Token'")
    print("3. This will download kaggle.json")
    print(f"4. Move it to: {kaggle_dir}")
    print("\nAfter setup, run this script again.")
    
    return False


def step_2_download_dataset() -> bool:
    """Step 2: Download Netflix dataset."""
    print_banner("STEP 2: DOWNLOAD NETFLIX DATASET")
    
    try:
        import download_netflix_dataset
        
        # Setup and download
        if not download_netflix_dataset.setup_kaggle_credentials():
            return False
        
        if not download_netflix_dataset.download_netflix_dataset():
            return False
        
        # Verify
        data_dir = Path(__file__).parent.parent / 'data' / 'netflix_prize'
        if download_netflix_dataset.verify_dataset(data_dir):
            print("\n✓ Dataset download and verification complete!")
            return True
        
        return False
    
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Download failed: {e}", exc_info=True)
        return False


def step_3_validate_data() -> bool:
    """Step 3: Validate dataset quality."""
    print_banner("STEP 3: VALIDATE DATASET")
    
    try:
        import netflix_data_validation
        
        validator = netflix_data_validation.NetflixDataValidator()
        success = validator.run_all_checks()
        
        if success:
            print("\n✓ Data validation passed!")
        else:
            print("\n⚠ Data validation found issues (non-blocking)")
        
        return True
    
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        return False


def step_4_engineer_features() -> bool:
    """Step 4: Engineer features from dataset."""
    print_banner("STEP 4: FEATURE ENGINEERING")
    
    try:
        import netflix_data_pipeline
        
        logger.info("Building features from Netflix dataset...")
        logger.info("This may take 5-10 minutes for the full dataset...")
        
        pipeline = netflix_data_pipeline.NetflixDataPipeline()
        features = pipeline.build_training_features()
        
        if features.empty:
            logger.error("Feature engineering failed")
            return False
        
        # Save features
        pipeline.save_features(features)
        
        logger.info(f"\n✓ Features engineered for {len(features)} users!")
        logger.info(f"Feature dimensions: {features.shape}")
        
        return True
    
    except Exception as e:
        logger.error(f"Feature engineering failed: {e}", exc_info=True)
        return False


def step_5_train_model() -> bool:
    """Step 5: Train cross-sell model."""
    print_banner("STEP 5: TRAIN CROSS-SELL MODEL")
    
    try:
        import netflix_train_model
        
        logger.info("Training XGBoost propensity model...")
        
        trainer = netflix_train_model.NetflixCrossSellModel()
        features = trainer.load_features()
        
        if features.empty:
            logger.error("Failed to load features")
            return False
        
        X, y = trainer.prepare_training_data(features)
        
        if X.empty:
            logger.error("Failed to prepare data")
            return False
        
        trainer.train_model(X, y)
        trainer.get_feature_importance()
        trainer.save_model()
        
        logger.info("\n✓ Model training complete!")
        
        return True
    
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        return False


def run_quick_mode() -> bool:
    """Run in quick mode (sampling)."""
    print_banner("QUICK MODE: SAMPLE PROCESSING")
    
    print("Processing 10% sample of dataset for quick iteration...")
    print("(Update config.yaml sampling.sample_fraction for full dataset)\n")
    
    try:
        import netflix_data_pipeline
        
        pipeline = netflix_data_pipeline.NetflixDataPipeline()
        features = pipeline.build_training_features()
        
        # Sample 10%
        sample_size = int(len(features) * 0.1)
        sample_features = features.sample(n=sample_size, random_state=42)
        
        logger.info(f"Processing {len(sample_features)} users (10% sample)")
        
        pipeline.save_features(sample_features, name='netflix_features_sample')
        
        logger.info("✓ Sample processing complete!")
        return True
    
    except Exception as e:
        logger.error(f"Quick mode failed: {e}", exc_info=True)
        return False


def main():
    """Run complete integration workflow."""
    print_banner("NETFLIX PRIZE DATASET INTEGRATION")
    print("Cross-Sell Intelligence Engine v1.0")
    print("="*70)
    
    # Check dependencies
    deps = check_dependencies()
    if not all(deps.values()):
        print("\n⚠ Please install missing dependencies and try again")
        return False
    
    # Get mode
    print("\nRun Mode Options:")
    print("  1. Complete (download → validate → train) [30+ minutes]")
    print("  2. Quick Sample (process 10% sample) [5 minutes]")
    print("  3. Features Only (if data already downloaded)")
    
    mode = input("\nSelect mode (1-3) [default: 2]: ").strip() or "2"
    
    if mode == "1":
        # Complete workflow
        steps = [
            ("Kaggle Setup", step_1_setup_kaggle),
            ("Download Dataset", step_2_download_dataset),
            ("Validate Data", step_3_validate_data),
            ("Feature Engineering", step_4_engineer_features),
            ("Train Model", step_5_train_model)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n{'='*70}")
            logger.info(f"Running: {step_name}")
            logger.info(f"{'='*70}")
            
            if not step_func():
                logger.error(f"Failed at: {step_name}")
                return False
    
    elif mode == "2":
        # Quick mode
        if not step_1_setup_kaggle():
            return False
        if not step_2_download_dataset():
            return False
        if not run_quick_mode():
            return False
    
    elif mode == "3":
        # Features only
        if not step_4_engineer_features():
            return False
    
    else:
        logger.error("Invalid mode selected")
        return False
    
    # Summary
    print_banner("INTEGRATION COMPLETE!")
    print("✓ Netflix Prize dataset integrated successfully!")
    print("\nNext Steps:")
    print("1. Features saved to: data/processed/netflix_features.parquet")
    print("2. Model saved to: models/netflix_xgboost_*.pkl")
    print("3. Update backend/app/config.py to use Netflix features")
    print("4. Start API: docker-compose up backend")
    print("5. Access API: http://localhost:8000/docs")
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
