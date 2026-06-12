import importlib

libs = ['pandas', 'numpy', 'xgboost', 'joblib', 'sqlalchemy', 'fastapi', 'shap', 'kmodes', 'mlflow']
for lib in libs:
    try:
        importlib.import_module(lib)
        print(f"[OK] {lib} is installed")
    except ImportError:
        print(f"[MISSING] {lib} is NOT installed")
