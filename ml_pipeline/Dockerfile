FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pandas numpy scikit-learn xgboost \
    kmodes shap mlflow pyyaml joblib \
    matplotlib

COPY . .

CMD ["python", "training/train.py"]