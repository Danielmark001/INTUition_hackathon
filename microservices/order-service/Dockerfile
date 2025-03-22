FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Expose API port
EXPOSE 8002

# Run service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]