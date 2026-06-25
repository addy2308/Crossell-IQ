FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*

# Copy & install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the whole backend project
COPY . .

# Create folders for data and models (mounted volumes in dev, but inside the image for prod)
RUN mkdir -p /app/data /app/models

# Generate synthetic Netflix data & train the model (only if model doesn’t exist)
RUN if [ ! -f /app/models/xgb_model.pkl ]; then \
      python ../ml_pipeline/generate_netflix_demo.py && \
      python ../ml_pipeline/add_segments.py && \
      python ../models/train_model.py; \
    fi

# Expose port
EXPOSE 8000

# Start the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
