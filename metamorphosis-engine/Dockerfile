FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Expose API port
EXPOSE 8010

# Run service
CMD ["python", "-m", "src.engine"]