FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install graphviz dependencies
RUN apt-get update && apt-get install -y \
    graphviz \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy service code
COPY . .

# Expose API port
EXPOSE 8040

# Run service
CMD ["python", "-m", "src.analyzer_service"]