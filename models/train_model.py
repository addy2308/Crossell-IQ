import mlflow
import mlflow.xgboost
import optuna
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import roc_auc_score, accuracy_score
import sqlite3
import joblib
from pathlib import Path
import os

mlflow.set_tracking_uri("file:///" + (Path(__file__).parent.parent / "mlruns").as_posix())
mlflow.set_experiment("crosssell-propensity-tuning")

def load_features():
    db_path = Path(__file__).parent.parent / 'data' / 'feature_store.db'
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM features", conn)
    conn.close()
    return df

def objective(trial, X_train, y_train, X_test, y_test):
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 500),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "random_state": 42
    }
    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    y_proba = model.predict_proba(X_test)[:, 1]
    return roc_auc_score(y_test, y_proba)

def train():
    df = load_features()
    feature_cols = [c for c in df.columns if c not in ('customer_id', 'target')]
    X = df[feature_cols]
    y = df['target']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Optuna study
    study = optuna.create_study(direction="maximize")
    study.optimize(lambda trial: objective(trial, X_train, y_train, X_test, y_test), n_trials=20)

    # Train final model with best params
    with mlflow.start_run(run_name="optuna-best") as run:
        best_params = study.best_params
        mlflow.log_params(best_params)
        mlflow.log_metric("best_cv_auc", study.best_value)

        model = xgb.XGBClassifier(**best_params, objective="binary:logistic", eval_metric="auc", random_state=42)
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_proba)
        acc = accuracy_score(y_test, y_pred)

        mlflow.log_metrics({"test_auc": auc, "test_accuracy": acc})
        mlflow.xgboost.log_model(model, "model")

        os.makedirs('models', exist_ok=True)
        joblib.dump(model, 'models/xgb_model.pkl')
        joblib.dump(feature_cols, 'models/feature_columns.pkl')

        print(f"Optuna tuning complete. Best AUC: {study.best_value:.4f}")
        print(f"Best params: {study.best_params}")
        print(f"Test AUC: {auc:.4f}, Accuracy: {acc:.4f}")

if __name__ == '__main__':
    train()
