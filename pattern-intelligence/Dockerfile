FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for ML
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy service code
COPY . .

# Create directories for data and models
RUN mkdir -p /app/data /app/models

# Expose API port
EXPOSE 8020

# Run service
CMD ["python", "-m", "src.intelligence_service"]