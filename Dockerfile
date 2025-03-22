# Metamorphic Architecture - Base Dockerfile
# This is a multi-stage build that serves as a template for all components

# ===== Python API Base =====
FROM python:3.9-slim as python-api-base

WORKDIR /app

# Install common dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install common Python packages
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# ===== Node.js Dashboard Base =====
FROM node:16-alpine as node-dashboard-base

WORKDIR /app

# Install common dependencies
RUN apk add --no-cache libc6-compat

# ===== Common Environment Variables =====
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NODE_ENV=production

# ===== Metamorphosis Engine =====
FROM python-api-base as metamorphosis-engine

WORKDIR /app

COPY ./metamorphosis-engine /app/

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

# ===== Architectural Plasticity Layer =====
FROM python-api-base as plasticity-layer

WORKDIR /app

COPY ./plasticity-layer /app/

EXPOSE 8010

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8010"]

# ===== Usage Pattern Intelligence =====
FROM python-api-base as pattern-intelligence

WORKDIR /app

COPY ./pattern-intelligence /app/

EXPOSE 8020

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8020"]

# ===== Multi-Objective Optimizer =====
FROM python-api-base as optimizer

WORKDIR /app

COPY ./optimizer /app/

EXPOSE 8030

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8030"]

# ===== Service Registry =====
FROM python-api-base as service-registry

WORKDIR /app

COPY ./service-registry /app/

EXPOSE 8040

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8040"]

# ===== Telemetry Collector =====
FROM python-api-base as telemetry

WORKDIR /app

COPY ./telemetry /app/

EXPOSE 8050

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8050"]

# ===== Architecture Analyzer =====
FROM python-api-base as architecture-analyzer

WORKDIR /app

COPY ./architecture-analyzer /app/

EXPOSE 8060

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8060"]

# ===== User Service =====
FROM python-api-base as user-service

WORKDIR /app

COPY ./microservices/user-service /app/

EXPOSE 9000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9000"]

# ===== Order Service =====
FROM python-api-base as order-service

WORKDIR /app

COPY ./microservices/order-service /app/

EXPOSE 9010

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9010"]

# ===== Payment Service =====
FROM python-api-base as payment-service

WORKDIR /app

COPY ./microservices/payment-service /app/

EXPOSE 9020

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9020"]

# ===== Dashboard =====
FROM node-dashboard-base as dashboard

WORKDIR /app

# Copy package files
COPY ./dashboard/package.json ./dashboard/package-lock.json ./

# Install dependencies
RUN npm ci --production

# Copy application files
COPY ./dashboard /app/

# Build the app
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]