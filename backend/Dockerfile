FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*

# Copy the whole repository into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Allow MLflow to use the filesystem backend
ENV MLFLOW_ALLOW_FILE_STORE=true

# Create folders for data and models
RUN mkdir -p /app/data /app/models

# Generate synthetic Netflix data, export to CSV, add segments, and train the model
# (only if the model doesn’t already exist)
RUN if [ ! -f /app/models/xgb_model.pkl ]; then \
      cd /app && \
      python ml_pipeline/generate_netflix_demo.py && \
      python ml_pipeline/export_netflix_to_csv.py && \
      python ml_pipeline/add_segments.py && \
      python models/train_model.py; \
    fi

# Set the working directory to the backend folder for the server
WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
