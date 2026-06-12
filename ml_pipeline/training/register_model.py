"""
Register trained model in MLflow Model Registry.
"""

import mlflow
import yaml

def register_model():
    """Register the latest model version."""
    with open('../config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    mlflow.set_tracking_uri(config['mlflow']['tracking_uri'])
    
    # Get the latest run
    client = mlflow.tracking.MlflowClient()
    experiment = client.get_experiment_by_name(config['mlflow']['experiment_name'])
    
    if not experiment:
        print("No experiment found. Run train.py first.")
        return
    
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["metrics.auc DESC"],
        max_results=1
    )
    
    if not runs:
        print("No runs found. Run train.py first.")
        return
    
    best_run = runs[0]
    run_id = best_run.info.run_id
    
    # Register model
    model_uri = f"runs:/{run_id}/model"
    result = mlflow.register_model(model_uri, config['model']['name'])
    
    print(f"✓ Model registered: {result.name} v{result.version}")
    print(f"  Run ID: {run_id}")
    print(f"  AUC: {best_run.data.metrics.get('auc', 'N/A')}")

if __name__ == '__main__':
    register_model()