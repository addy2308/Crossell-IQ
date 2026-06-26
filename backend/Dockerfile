FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*

# Copy the whole repository into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Create folders for data and models
RUN mkdir -p /app/data /app/models

# Generate synthetic Netflix data & train the model (only if model doesn’t exist)
RUN if [ ! -f /app/models/xgb_model.pkl ]; then \
      cd /app && \
      python ml_pipeline/generate_netflix_demo.py && \
      python ml_pipeline/add_segments.py && \
      python models/train_model.py; \
    fi

# Set the working directory to the backend folder for the server
WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
