"""
Netflix Cross-Sell Model Deployment Script
Prepares and deploys the trained model for production use.
"""

import shutil
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelDeploymentManager:
    """Manages model deployment to production."""
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        
        self.base_dir = Path(base_dir)
        self.models_dir = self.base_dir / 'models'
        self.deployment_dir = self.base_dir / 'deployment' / 'models'
        self.deployment_dir.mkdir(parents=True, exist_ok=True)
    
    def find_latest_model(self) -> Tuple[Path, Path, Path]:
        """Find the latest model files."""
        model_files = sorted(self.models_dir.glob('netflix_xgboost_*.pkl'))
        
        if not model_files:
            raise FileNotFoundError("No trained models found")
        
        latest_model = model_files[-1]
        timestamp = latest_model.stem.replace('netflix_xgboost_', '')
        
        scaler_file = self.models_dir / f'netflix_scaler_{timestamp}.pkl'
        metadata_file = self.models_dir / f'netflix_metadata_{timestamp}.json'
        
        if not scaler_file.exists() or not metadata_file.exists():
            raise FileNotFoundError(f"Missing supporting files for model {timestamp}")
        
        return latest_model, scaler_file, metadata_file
    
    def validate_model_files(self, model_file: Path, scaler_file: Path, metadata_file: Path) -> bool:
        """Validate model files are complete and valid."""
        logger.info("Validating model files...")
        
        # Check files exist
        if not all(f.exists() for f in [model_file, scaler_file, metadata_file]):
            logger.error("Missing model files")
            return False
        
        # Check file sizes are reasonable
        min_size_kb = 100
        for f in [model_file, scaler_file]:
            if f.stat().st_size < min_size_kb * 1024:
                logger.error(f"File too small: {f.name}")
                return False
        
        # Check metadata
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                if 'features' not in metadata or 'metrics' not in metadata:
                    logger.error("Invalid metadata structure")
                    return False
        except json.JSONDecodeError:
            logger.error("Metadata JSON is invalid")
            return False
        
        logger.info("✓ Model validation passed")
        return True
    
    def deploy_to_staging(self, model_file: Path, scaler_file: Path, metadata_file: Path) -> bool:
        """Deploy model to staging environment."""
        logger.info("Deploying to staging...")
        
        try:
            staging_dir = self.deployment_dir / 'staging'
            staging_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy files
            shutil.copy2(model_file, staging_dir / model_file.name)
            shutil.copy2(scaler_file, staging_dir / scaler_file.name)
            shutil.copy2(metadata_file, staging_dir / metadata_file.name)
            
            # Create deployment manifest
            manifest = {
                'timestamp': datetime.now().isoformat(),
                'model_file': model_file.name,
                'scaler_file': scaler_file.name,
                'metadata_file': metadata_file.name,
                'environment': 'staging',
                'status': 'deployed'
            }
            
            with open(staging_dir / 'manifest.json', 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"✓ Deployed to staging: {staging_dir}")
            return True
        
        except Exception as e:
            logger.error(f"Staging deployment failed: {e}")
            return False
    
    def deploy_to_production(self, model_file: Path, scaler_file: Path, metadata_file: Path) -> bool:
        """Deploy model to production environment."""
        logger.info("Deploying to production...")
        
        try:
            prod_dir = self.deployment_dir / 'production'
            prod_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup existing production model if it exists
            existing_models = list(prod_dir.glob('netflix_xgboost_*.pkl'))
            if existing_models:
                backup_dir = prod_dir / 'backups'
                backup_dir.mkdir(exist_ok=True)
                for f in existing_models:
                    shutil.move(str(f), str(backup_dir / f.name))
                logger.info(f"✓ Backed up previous model to {backup_dir}")
            
            # Copy new model files
            shutil.copy2(model_file, prod_dir / model_file.name)
            shutil.copy2(scaler_file, prod_dir / scaler_file.name)
            shutil.copy2(metadata_file, prod_dir / metadata_file.name)
            
            # Create deployment manifest
            manifest = {
                'timestamp': datetime.now().isoformat(),
                'model_file': model_file.name,
                'scaler_file': scaler_file.name,
                'metadata_file': metadata_file.name,
                'environment': 'production',
                'status': 'active',
                'previous_backups': [f.name for f in (prod_dir / 'backups').glob('*.pkl')] if (prod_dir / 'backups').exists() else []
            }
            
            with open(prod_dir / 'manifest.json', 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"✓ Deployed to production: {prod_dir}")
            return True
        
        except Exception as e:
            logger.error(f"Production deployment failed: {e}")
            return False
    
    def verify_deployment(self, environment: str) -> bool:
        """Verify deployment is working correctly."""
        logger.info(f"Verifying {environment} deployment...")
        
        try:
            env_dir = self.deployment_dir / environment
            
            if not env_dir.exists():
                logger.error(f"Deployment directory not found: {env_dir}")
                return False
            
            # Check required files
            required_files = list(env_dir.glob('netflix_xgboost_*.pkl')) + \
                           list(env_dir.glob('netflix_scaler_*.pkl')) + \
                           list(env_dir.glob('netflix_metadata_*.json'))
            
            if len(required_files) < 3:
                logger.error(f"Missing model files in {environment}")
                return False
            
            # Verify manifest
            manifest_file = env_dir / 'manifest.json'
            if not manifest_file.exists():
                logger.error(f"Manifest not found in {environment}")
                return False
            
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
                logger.info(f"  Status: {manifest.get('status')}")
                logger.info(f"  Deployed: {manifest.get('timestamp')}")
            
            logger.info(f"✓ {environment.capitalize()} deployment verified")
            return True
        
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
    
    def create_deployment_report(self, environment: str) -> Dict[str, Any]:
        """Create a comprehensive deployment report."""
        env_dir = self.deployment_dir / environment
        
        report = {
            'environment': environment,
            'timestamp': datetime.now().isoformat(),
            'model_files': [],
            'status': 'unknown'
        }
        
        if env_dir.exists():
            for f in env_dir.glob('*.pkl'):
                report['model_files'].append({
                    'name': f.name,
                    'size_mb': f.stat().st_size / (1024**2),
                    'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })
            
            manifest_file = env_dir / 'manifest.json'
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                    report['status'] = manifest.get('status', 'unknown')
        
        return report


def main():
    """Execute deployment workflow."""
    print("="*70)
    print("NETFLIX MODEL DEPLOYMENT MANAGER")
    print("="*70)
    
    manager = ModelDeploymentManager()
    
    try:
        # Find latest model
        logger.info("\n1. Finding latest trained model...")
        model_file, scaler_file, metadata_file = manager.find_latest_model()
        logger.info(f"   Found: {model_file.name}")
        
        # Validate
        logger.info("\n2. Validating model files...")
        if not manager.validate_model_files(model_file, scaler_file, metadata_file):
            logger.error("Validation failed!")
            return False
        
        # Deploy to staging
        logger.info("\n3. Deploying to staging...")
        if not manager.deploy_to_staging(model_file, scaler_file, metadata_file):
            logger.error("Staging deployment failed!")
            return False
        
        # Verify staging
        logger.info("\n4. Verifying staging deployment...")
        if not manager.verify_deployment('staging'):
            logger.error("Staging verification failed!")
            return False
        
        # Deploy to production
        logger.info("\n5. Deploying to production...")
        user_input = input("   Continue with production deployment? (yes/no): ").lower()
        if user_input != 'yes':
            logger.info("   Deployment cancelled")
            return True
        
        if not manager.deploy_to_production(model_file, scaler_file, metadata_file):
            logger.error("Production deployment failed!")
            return False
        
        # Verify production
        logger.info("\n6. Verifying production deployment...")
        if not manager.verify_deployment('production'):
            logger.error("Production verification failed!")
            return False
        
        # Generate reports
        logger.info("\n7. Generating deployment reports...")
        staging_report = manager.create_deployment_report('staging')
        prod_report = manager.create_deployment_report('production')
        
        logger.info("\n" + "="*70)
        logger.info("✓ DEPLOYMENT SUCCESSFUL!")
        logger.info("="*70)
        logger.info("\nProduction Status:")
        logger.info(f"  Environment: {prod_report['environment']}")
        logger.info(f"  Status: {prod_report['status']}")
        logger.info(f"  Model files: {len(prod_report['model_files'])}")
        
        return True
    
    except Exception as e:
        logger.error(f"Deployment error: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
