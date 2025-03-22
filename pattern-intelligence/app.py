import os
import json
import time
import logging
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import httpx
import asyncio
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Usage Pattern Intelligence")

# Models
class TelemetryData(BaseModel):
    timestamp: float
    service_id: str
    endpoint: str
    latency: float
    cpu_usage: float
    memory_usage: float
    request_count: int
    error_count: int
    user_id: Optional[str] = None
    transaction_id: Optional[str] = None
    additional_metrics: Optional[Dict[str, Any]] = None

class ServiceUsagePattern(BaseModel):
    service_id: str
    pattern_id: str
    description: str
    confidence: float
    metrics: Dict[str, Any]
    detected_at: float
    recommendations: Optional[List[Dict[str, Any]]] = None

class SystemPatternRequest(BaseModel):
    time_window: Optional[int] = 3600  # Default 1 hour in seconds
    min_confidence: Optional[float] = 0.7
    include_historical: Optional[bool] = False

# In-memory store (would use a database in production)
telemetry_buffer = []
detected_patterns = []
service_metrics = {}  # Time-series metrics by service
transaction_flows = []  # Captured transaction flows across services
models = {}  # Trained ML models for pattern detection

TELEMETRY_URL = os.environ.get("TELEMETRY_URL", "http://telemetry:8050")
MAX_BUFFER_SIZE = 10000  # Maximum telemetry points to keep in memory

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Usage Pattern Intelligence")
    # Start background processing
    asyncio.create_task(periodic_pattern_detection())
    asyncio.create_task(fetch_telemetry_data())

# API Endpoints
@app.get("/")
async def root():
    return {"status": "Usage Pattern Intelligence operational"}

@app.post("/telemetry")
async def receive_telemetry(data: TelemetryData):
    """Endpoint to receive telemetry directly (alternative to polling)"""
    process_telemetry_point(data)
    return {"status": "received"}

@app.get("/patterns")
async def get_patterns(time_window: Optional[int] = 3600, min_confidence: Optional[float] = 0.7):
    """Get detected usage patterns within time window"""
    now = time.time()
    filtered_patterns = [
        p for p in detected_patterns 
        if p.detected_at >= now - time_window and p.confidence >= min_confidence
    ]
    return filtered_patterns

@app.post("/patterns/system")
async def analyze_system_patterns(request: SystemPatternRequest):
    """Analyze system-wide patterns and recommend architectural changes"""
    patterns = await detect_system_patterns(
        time_window=request.time_window,
        min_confidence=request.min_confidence
    )
    return patterns

@app.get("/metrics/{service_id}")
async def get_service_metrics(service_id: str, time_window: Optional[int] = 3600):
    """Get time-series metrics for a specific service"""
    if service_id not in service_metrics:
        raise HTTPException(status_code=404, detail="No metrics found for service")
    
    now = time.time()
    filtered_metrics = [
        m for m in service_metrics[service_id]
        if m["timestamp"] >= now - time_window
    ]
    return filtered_metrics

@app.post("/recommendations")
async def get_recommendations(background_tasks: BackgroundTasks):
    """Generate architectural recommendations based on detected patterns"""
    # Trigger recommendation generation in the background
    background_tasks.add_task(generate_recommendations)
    return {"status": "Generating recommendations"}

# Background tasks
async def periodic_pattern_detection():
    """Periodically run pattern detection on collected telemetry"""
    while True:
        try:
            logger.info("Running periodic pattern detection")
            # Detect patterns from buffered telemetry
            if len(telemetry_buffer) > 100:  # Only run if we have enough data
                await detect_service_patterns()
                await detect_transaction_patterns()
                # Clean up old data
                cleanup_old_data()
            else:
                logger.info(f"Not enough telemetry data for analysis: {len(telemetry_buffer)}")
        except Exception as e:
            logger.error(f"Error in pattern detection: {str(e)}")
        
        # Run every 5 minutes
        await asyncio.sleep(300)

async def fetch_telemetry_data():
    """Fetch telemetry data from the telemetry service"""
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{TELEMETRY_URL}/data/recent")
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Fetched {len(data)} telemetry points")
                    
                    for point in data:
                        process_telemetry_point(TelemetryData(**point))
                else:
                    logger.warning(f"Failed to fetch telemetry: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching telemetry: {str(e)}")
        
        # Fetch every 10 seconds
        await asyncio.sleep(10)

def process_telemetry_point(data: TelemetryData):
    """Process an incoming telemetry data point"""
    # Add to buffer (with size limit)
    telemetry_buffer.append(data.dict())
    if len(telemetry_buffer) > MAX_BUFFER_SIZE:
        telemetry_buffer.pop(0)  # Remove oldest
    
    # Update service metrics
    if data.service_id not in service_metrics:
        service_metrics[data.service_id] = []
    
    service_metrics[data.service_id].append({
        "timestamp": data.timestamp,
        "endpoint": data.endpoint,
        "latency": data.latency,
        "cpu_usage": data.cpu_usage,
        "memory_usage": data.memory_usage,
        "request_count": data.request_count,
        "error_count": data.error_count
    })
    
    # Limit per-service metrics storage
    if len(service_metrics[data.service_id]) > 1000:
        service_metrics[data.service_id].pop(0)  # Remove oldest
    
    # Track transaction flows if transaction_id is present
    if data.transaction_id:
        transaction_flows.append({
            "timestamp": data.timestamp,
            "transaction_id": data.transaction_id,
            "service_id": data.service_id,
            "endpoint": data.endpoint,
            "user_id": data.user_id
        })
        # Limit transaction flows storage
        if len(transaction_flows) > 5000:
            transaction_flows.pop(0)  # Remove oldest

async def detect_service_patterns():
    """Detect usage patterns within individual services"""
    # Group telemetry by service
    by_service = {}
    for point in telemetry_buffer:
        if point["service_id"] not in by_service:
            by_service[point["service_id"]] = []
        by_service[point["service_id"]].append(point)
    
    # Analyze each service
    for service_id, data in by_service.items():
        if len(data) < 50:  # Skip if not enough data
            continue
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(data)
        
        # 1. Detect load patterns
        load_patterns = detect_load_patterns(df, service_id)
        if load_patterns:
            for pattern in load_patterns:
                detected_patterns.append(pattern)
        
        # 2. Detect endpoint usage patterns
        endpoint_patterns = detect_endpoint_patterns(df, service_id)
        if endpoint_patterns:
            for pattern in endpoint_patterns:
                detected_patterns.append(pattern)
        
        # 3. Detect resource usage anomalies
        anomaly_patterns = detect_resource_anomalies(df, service_id)
        if anomaly_patterns:
            for pattern in anomaly_patterns:
                detected_patterns.append(pattern)

async def detect_transaction_patterns():
    """Detect patterns in transaction flows across services"""
    if len(transaction_flows) < 100:
        return  # Not enough data
    
    # Convert to DataFrame
    df = pd.DataFrame(transaction_flows)
    
    # Group by transaction_id
    transactions = df.groupby("transaction_id").agg(list).reset_index()
    
    # Analyze service interaction patterns
    if len(transactions) > 10:  # Need multiple transactions to find patterns
        # Create service interaction sequences
        transactions["service_sequence"] = transactions["service_id"].apply(
            lambda x: "->".join(x))
        
        # Find common sequences
        sequence_counts = transactions["service_sequence"].value_counts()
        common_sequences = sequence_counts[sequence_counts > 3].to_dict()
        
        # Create patterns for common flows
        now = time.time()
        for sequence, count in common_sequences.items():
            confidence = min(1.0, count / len(transactions))
            services = sequence.split("->")
            
            # Check if this creates a tight coupling pattern
            if len(services) >= 3:
                detected_patterns.append(ServiceUsagePattern(
                    service_id=services[0],  # Start of chain
                    pattern_id=f"flow_{hash(sequence) % 10000}",
                    description=f"Common transaction flow: {sequence}",
                    confidence=confidence,
                    metrics={
                        "frequency": count,
                        "total_transactions": len(transactions),
                        "services_involved": services
                    },
                    detected_at=now,
                    recommendations=[{
                        "type": "service_coupling",
                        "description": f"Consider merging tightly coupled services: {', '.join(services)}",
                        "confidence": confidence,
                        "impact": "high" if confidence > 0.8 else "medium"
                    }]
                ))

async def detect_system_patterns(time_window: int, min_confidence: float):
    """Analyze system-wide patterns to identify architectural optimization opportunities"""
    system_patterns = []
    now = time.time()
    
    # 1. Identify service coupling from transaction flows
    if len(transaction_flows) > 0:
        recent_flows = [t for t in transaction_flows if t["timestamp"] >= now - time_window]
        
        if len(recent_flows) > 50:
            df = pd.DataFrame(recent_flows)
            
            # Create a service co-occurrence matrix
            service_pairs = []
            for txn_id, group in df.groupby("transaction_id"):
                services = group["service_id"].unique()
                for i in range(len(services)):
                    for j in range(i+1, len(services)):
                        service_pairs.append((services[i], services[j]))
            
            if service_pairs:
                pair_counts = {}
                for pair in service_pairs:
                    sorted_pair = tuple(sorted(pair))
                    if sorted_pair in pair_counts:
                        pair_counts[sorted_pair] += 1
                    else:
                        pair_counts[sorted_pair] = 1
                
                # Find highly coupled services
                total_txns = len(df["transaction_id"].unique())
                for pair, count in pair_counts.items():
                    coupling_score = count / total_txns
                    if coupling_score >= min_confidence:
                        system_patterns.append({
                            "pattern_type": "service_coupling",
                            "services": list(pair),
                            "confidence": coupling_score,
                            "description": f"Services {pair[0]} and {pair[1]} are tightly coupled",
                            "recommendations": [{
                                "type": "architectural",
                                "action": "merge_services" if coupling_score > 0.9 else "optimize_communication",
                                "description": f"Consider {'merging these services' if coupling_score > 0.9 else 'optimizing communication between these services'}"
                            }]
                        })
    
    # 2. Identify resource utilization patterns
    if service_metrics:
        service_avg_usage = {}
        for service_id, metrics in service_metrics.items():
            recent_metrics = [m for m in metrics if m["timestamp"] >= now - time_window]
            if recent_metrics:
                avg_cpu = sum(m["cpu_usage"] for m in recent_metrics) / len(recent_metrics)
                avg_memory = sum(m["memory_usage"] for m in recent_metrics) / len(recent_metrics)
                service_avg_usage[service_id] = {
                    "cpu": avg_cpu,
                    "memory": avg_memory,
                    "request_count": sum(m["request_count"] for m in recent_metrics)
                }
        
        # Find overprovisioned services
        for service_id, usage in service_avg_usage.items():
            if usage["cpu"] < 0.2 and usage["memory"] < 0.3 and usage["request_count"] > 10:
                system_patterns.append({
                    "pattern_type": "resource_utilization",
                    "service_id": service_id,
                    "confidence": 0.8,
                    "description": f"Service {service_id} appears overprovisioned",
                    "metrics": usage,
                    "recommendations": [{
                        "type": "resource_optimization",
                        "action": "reduce_resources",
                        "description": f"Consider reducing resources allocated to {service_id}"
                    }]
                })
            elif usage["cpu"] > 0.8 or usage["memory"] > 0.8:
                system_patterns.append({
                    "pattern_type": "resource_utilization",
                    "service_id": service_id,
                    "confidence": 0.9,
                    "description": f"Service {service_id} is approaching resource limits",
                    "metrics": usage,
                    "recommendations": [{
                        "type": "resource_optimization",
                        "action": "increase_resources",
                        "description": f"Consider increasing resources for {service_id}"
                    }]
                })
    
    return system_patterns

def detect_load_patterns(df, service_id):
    """Detect load patterns for a service"""
    patterns = []
    now = time.time()
    
    # Check for temporal patterns in request volume
    if "timestamp" in df.columns and "request_count" in df.columns:
        # Convert timestamp to hour of day
        df["hour"] = df["timestamp"].apply(lambda x: datetime.fromtimestamp(x).hour)
        hourly_load = df.groupby("hour")["request_count"].mean().reset_index()
        
        # Find peak hours (more than 50% above average)
        avg_load = hourly_load["request_count"].mean()
        peak_hours = hourly_load[hourly_load["request_count"] > avg_load * 1.5]["hour"].tolist()
        
        if peak_hours:
            peak_hours_str = ", ".join([f"{h}:00-{h+1}:00" for h in peak_hours])
            patterns.append(ServiceUsagePattern(
                service_id=service_id,
                pattern_id=f"load_pattern_{service_id}_{hash(str(peak_hours)) % 10000}",
                description=f"Peak load during hours: {peak_hours_str}",
                confidence=0.85,
                metrics={
                    "peak_hours": peak_hours,
                    "peak_load_factor": max(hourly_load["request_count"]) / avg_load if avg_load > 0 else 0,
                    "average_load": avg_load
                },
                detected_at=now,
                recommendations=[{
                    "type": "scaling",
                    "description": f"Consider time-based scaling for service {service_id} during peak hours"
                }]
            ))
    
    return patterns

def detect_endpoint_patterns(df, service_id):
    """Detect endpoint usage patterns for a service"""
    patterns = []
    now = time.time()
    
    if "endpoint" in df.columns:
        # Analyze endpoint popularity
        endpoint_counts = df["endpoint"].value_counts().reset_index()
        endpoint_counts.columns = ["endpoint", "count"]
        total_requests = endpoint_counts["count"].sum()
        
        # Find endpoints that account for >70% of traffic
        dominant_endpoints = endpoint_counts[endpoint_counts["count"] > total_requests * 0.7]["endpoint"].tolist()
        
        if dominant_endpoints:
            for endpoint in dominant_endpoints:
                patterns.append(ServiceUsagePattern(
                    service_id=service_id,
                    pattern_id=f"endpoint_{service_id}_{hash(endpoint) % 10000}",
                    description=f"Dominant endpoint usage: {endpoint}",
                    confidence=0.9,
                    metrics={
                        "endpoint": endpoint,
                        "usage_percentage": df[df["endpoint"] == endpoint].shape[0] / df.shape[0] * 100,
                        "total_requests": df.shape[0]
                    },
                    detected_at=now,
                    recommendations=[{
                        "type": "optimization",
                        "description": f"Optimize or split high-traffic endpoint: {endpoint}"
                    }]
                ))
        
        # Find unused or rarely used endpoints
        rare_endpoints = endpoint_counts[endpoint_counts["count"] < total_requests * 0.01]["endpoint"].tolist()
        if rare_endpoints and len(rare_endpoints) > 1:  # Only flag if multiple rare endpoints
            patterns.append(ServiceUsagePattern(
                service_id=service_id,
                pattern_id=f"rare_endpoints_{service_id}_{len(rare_endpoints)}",
                description=f"Multiple rarely used endpoints detected ({len(rare_endpoints)})",
                confidence=0.75,
                metrics={
                    "rare_endpoint_count": len(rare_endpoints),
                    "examples": rare_endpoints[:5],  # First 5 examples
                    "total_requests": df.shape[0]
                },
                detected_at=now,
                recommendations=[{
                    "type": "optimization",
                    "description": f"Consider consolidating or removing rarely used endpoints"
                }]
            ))
    
    return patterns

def detect_resource_anomalies(df, service_id):
    """Detect resource usage anomalies for a service"""
    patterns = []
    now = time.time()
    
    # Check for resource efficiency
    if all(col in df.columns for col in ["request_count", "cpu_usage", "memory_usage"]):
        # Calculate efficiency metrics
        df["cpu_per_request"] = df.apply(
            lambda row: row["cpu_usage"] / row["request_count"] if row["request_count"] > 0 else 0, 
            axis=1
        )
        df["memory_per_request"] = df.apply(
            lambda row: row["memory_usage"] / row["request_count"] if row["request_count"] > 0 else 0, 
            axis=1
        )
        
        # Filter out zero values
        df_filtered = df[(df["cpu_per_request"] > 0) & (df["memory_per_request"] > 0)]
        
        if len(df_filtered) > 20:  # Need enough data points
            # Use DBSCAN to find anomalies in resource usage
            features = df_filtered[["cpu_per_request", "memory_per_request"]].values
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Save the model for future anomaly detection
            models[f"{service_id}_resource_scaler"] = scaler
            
            # Detect anomalies
            dbscan = DBSCAN(eps=0.5, min_samples=5)
            clusters = dbscan.fit_predict(features_scaled)
            
            # Find outliers (points with cluster label -1)
            outliers = df_filtered.iloc[clusters == -1]
            
            if len(outliers) > 0 and len(outliers) < len(df_filtered) * 0.3:  # Significant but not too many
                patterns.append(ServiceUsagePattern(
                    service_id=service_id,
                    pattern_id=f"resource_anomaly_{service_id}_{now}",
                    description=f"Resource usage anomalies detected",
                    confidence=0.8,
                    metrics={
                        "anomaly_count": len(outliers),
                        "total_points": len(df_filtered),
                        "percentage": len(outliers) / len(df_filtered) * 100,
                        "max_cpu_per_request": float(outliers["cpu_per_request"].max()),
                        "max_memory_per_request": float(outliers["memory_per_request"].max())
                    },
                    detected_at=now,
                    recommendations=[{
                        "type": "resource_optimization",
                        "description": f"Investigate resource efficiency issues in service {service_id}"
                    }]
                ))
    
    return patterns

async def generate_recommendations():
    """Generate architectural recommendations based on detected patterns"""
    # This would be a more sophisticated algorithm in a real system
    # that considers multiple patterns and their interactions
    
    logger.info("Generating architectural recommendations")
    
    # Simulate thinking time
    await asyncio.sleep(5)
    
    # For demo purposes, we'll just return the recommendations from patterns
    # A real system would aggregate and prioritize these
    recommendations = []
    for pattern in detected_patterns:
        if pattern.recommendations:
            for rec in pattern.recommendations:
                recommendations.append({
                    "source_pattern": pattern.pattern_id,
                    "confidence": pattern.confidence,
                    "recommendation": rec
                })
    
    # In a real system, we'd store these or notify the metamorphosis engine
    logger.info(f"Generated {len(recommendations)} recommendations")
    
    return recommendations

def cleanup_old_data():
    """Clean up old data to prevent memory bloat"""
    global telemetry_buffer, detected_patterns, transaction_flows
    
    now = time.time()
    # Keep only the last 24 hours of data
    telemetry_buffer = [t for t in telemetry_buffer if t["timestamp"] >= now - 86400]
    detected_patterns = [p for p in detected_patterns if p.detected_at >= now - 86400]
    transaction_flows = [t for t in transaction_flows if t["timestamp"] >= now - 86400]
    
    # Clean up service metrics (keep last 24 hours)
    for service_id in service_metrics:
        service_metrics[service_id] = [
            m for m in service_metrics[service_id] 
            if m["timestamp"] >= now - 86400
        ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8020)