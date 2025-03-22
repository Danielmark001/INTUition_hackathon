import os
import json
import time
import logging
import asyncio
from collections import deque
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any, Deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Telemetry Collector")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class TelemetryPoint(BaseModel):
    timestamp: float
    service_id: str
    endpoint: str
    latency: float
    cpu_usage: float
    memory_usage: float
    request_count: int
    error_count: int
    additional_metrics: Optional[Dict[str, Any]] = None

class TelemetryQuery(BaseModel):
    service_ids: Optional[List[str]] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    limit: Optional[int] = 100
    metrics: Optional[List[str]] = None

# In-memory data store
# Using deques with max length to prevent memory issues
telemetry_data: Dict[str, Deque[Dict[str, Any]]] = {}
recent_points: Deque[Dict[str, Any]] = deque(maxlen=1000)
transaction_traces: Dict[str, List[Dict[str, Any]]] = {}

# Configuration
MAX_POINTS_PER_SERVICE = 10000  # Maximum telemetry points to keep per service
DATA_RETENTION_PERIOD = 86400  # 24 hours in seconds

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Telemetry Collector")
    # Start cleanup task
    asyncio.create_task(periodic_cleanup())

# API Endpoints
@app.get("/")
async def root():
    return {"status": "Telemetry Collector operational"}

@app.post("/data")
async def receive_telemetry(data: TelemetryPoint):
    """Receive telemetry data from services"""
    telemetry_dict = data.dict()
    
    # Add to recent points
    recent_points.append(telemetry_dict)
    
    # Store by service ID
    service_id = data.service_id
    if service_id not in telemetry_data:
        telemetry_data[service_id] = deque(maxlen=MAX_POINTS_PER_SERVICE)
    
    telemetry_data[service_id].append(telemetry_dict)
    
    # Track transaction if provided
    transaction_id = telemetry_dict.get("additional_metrics", {}).get("transaction_id")
    if transaction_id:
        if transaction_id not in transaction_traces:
            transaction_traces[transaction_id] = []
        
        transaction_traces[transaction_id].append({
            "timestamp": data.timestamp,
            "service_id": service_id,
            "endpoint": data.endpoint,
            "latency": data.latency,
            "transaction_id": transaction_id
        })
    
    return {"status": "received"}

@app.get("/data/recent")
async def get_recent_data(limit: int = 100):
    """Get the most recent telemetry data points"""
    return list(recent_points)[-limit:]

@app.get("/data/services")
async def get_service_list():
    """Get a list of all services that have reported telemetry"""
    return list(telemetry_data.keys())

@app.get("/data/service/{service_id}")
async def get_service_data(
    service_id: str, 
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    limit: int = 1000
):
    """Get telemetry data for a specific service"""
    if service_id not in telemetry_data:
        raise HTTPException(status_code=404, detail="No data found for service")
    
    # Filter by time range if provided
    filtered_data = list(telemetry_data[service_id])
    
    if start_time is not None:
        filtered_data = [d for d in filtered_data if d["timestamp"] >= start_time]
    
    if end_time is not None:
        filtered_data = [d for d in filtered_data if d["timestamp"] <= end_time]
    
    # Return the most recent points up to the limit
    return filtered_data[-limit:]

@app.post("/data/query")
async def query_telemetry(query: TelemetryQuery):
    """Query telemetry data with flexible filters"""
    # Determine which services to query
    if query.service_ids:
        services_to_query = [s for s in query.service_ids if s in telemetry_data]
    else:
        services_to_query = list(telemetry_data.keys())
    
    results = []
    
    # Time range constraints
    start_time = query.start_time or 0
    end_time = query.end_time or time.time()
    
    # Collect data from each service
    for service_id in services_to_query:
        service_data = telemetry_data[service_id]
        
        for point in service_data:
            if start_time <= point["timestamp"] <= end_time:
                # Filter metrics if requested
                if query.metrics:
                    filtered_point = {
                        "timestamp": point["timestamp"],
                        "service_id": point["service_id"]
                    }
                    for metric in query.metrics:
                        if metric in point:
                            filtered_point[metric] = point[metric]
                        elif "additional_metrics" in point and metric in point["additional_metrics"]:
                            filtered_point[metric] = point["additional_metrics"][metric]
                    
                    results.append(filtered_point)
                else:
                    results.append(point)
    
    # Sort by timestamp and apply limit
    results.sort(key=lambda x: x["timestamp"])
    
    if query.limit:
        results = results[-query.limit:]
    
    return results

@app.get("/data/transactions/{transaction_id}")
async def get_transaction_trace(transaction_id: str):
    """Get the trace of a specific transaction across services"""
    if transaction_id not in transaction_traces:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {
        "transaction_id": transaction_id,
        "spans": sorted(transaction_traces[transaction_id], key=lambda x: x["timestamp"])
    }

@app.get("/data/transactions/recent")
async def get_recent_transactions(limit: int = 20):
    """Get recent transaction traces"""
    recent_transactions = sorted(
        transaction_traces.items(),
        key=lambda x: max(span["timestamp"] for span in x[1]) if x[1] else 0,
        reverse=True
    )[:limit]
    
    return [
        {
            "transaction_id": tx_id,
            "spans": sorted(spans, key=lambda x: x["timestamp"]),
            "services": list(set(span["service_id"] for span in spans)),
            "start_time": min(span["timestamp"] for span in spans) if spans else None,
            "end_time": max(span["timestamp"] for span in spans) if spans else None,
            "total_latency": sum(span["latency"] for span in spans)
        }
        for tx_id, spans in recent_transactions
    ]

@app.get("/metrics")
async def get_aggregated_metrics():
    """Get aggregated metrics for all services"""
    metrics = {}
    
    for service_id, data in telemetry_data.items():
        if not data:
            continue
        
        # Get the most recent 10 minutes of data
        now = time.time()
        recent_data = [d for d in data if d["timestamp"] >= now - 600]
        
        if not recent_data:
            continue
        
        # Calculate aggregated metrics
        avg_cpu = sum(d["cpu_usage"] for d in recent_data) / len(recent_data)
        avg_memory = sum(d["memory_usage"] for d in recent_data) / len(recent_data)
        total_requests = sum(d["request_count"] for d in recent_data)
        total_errors = sum(d["error_count"] for d in recent_data)
        avg_latency = sum(d["latency"] for d in recent_data) / len(recent_data)
        
        metrics[service_id] = {
            "avg_cpu": avg_cpu,
            "avg_memory": avg_memory,
            "total_requests": total_requests,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "avg_latency": avg_latency,
            "data_points": len(recent_data)
        }
    
    return metrics

@app.get("/metrics/{service_id}")
async def get_service_metrics(
    service_id: str,
    time_window: Optional[int] = 600  # 10 minutes in seconds
):
    """Get aggregated metrics for a specific service over time"""
    if service_id not in telemetry_data:
        raise HTTPException(status_code=404, detail="No data found for service")
    
    # Group data by time buckets (1-minute intervals)
    now = time.time()
    start_time = now - time_window
    
    data = [d for d in telemetry_data[service_id] if d["timestamp"] >= start_time]
    
    if not data:
        return []
    
    # Create 1-minute buckets
    buckets = {}
    bucket_size = 60  # 1 minute
    
    for point in data:
        bucket_time = int(point["timestamp"] / bucket_size) * bucket_size
        
        if bucket_time not in buckets:
            buckets[bucket_time] = {
                "timestamp": bucket_time,
                "cpu_points": [],
                "memory_points": [],
                "latency_points": [],
                "request_count": 0,
                "error_count": 0
            }
        
        bucket = buckets[bucket_time]
        bucket["cpu_points"].append(point["cpu_usage"])
        bucket["memory_points"].append(point["memory_usage"])
        bucket["latency_points"].append(point["latency"])
        bucket["request_count"] += point["request_count"]
        bucket["error_count"] += point["error_count"]
    
    # Calculate aggregates for each bucket
    metrics = []
    
    for timestamp, bucket in sorted(buckets.items()):
        metrics.append({
            "timestamp": timestamp,
            "cpu_usage": sum(bucket["cpu_points"]) / len(bucket["cpu_points"]) if bucket["cpu_points"] else 0,
            "memory_usage": sum(bucket["memory_points"]) / len(bucket["memory_points"]) if bucket["memory_points"] else 0,
            "latency": sum(bucket["latency_points"]) / len(bucket["latency_points"]) if bucket["latency_points"] else 0,
            "request_count": bucket["request_count"],
            "error_count": bucket["error_count"],
            "error_rate": bucket["error_count"] / bucket["request_count"] if bucket["request_count"] > 0 else 0
        })
    
    return metrics

@app.delete("/data/service/{service_id}")
async def delete_service_data(service_id: str):
    """Delete telemetry data for a specific service"""
    if service_id in telemetry_data:
        del telemetry_data[service_id]
        # Also clean up from recent points
        global recent_points
        recent_points = deque(
            [p for p in recent_points if p["service_id"] != service_id],
            maxlen=recent_points.maxlen
        )
        return {"status": "deleted"}
    else:
        raise HTTPException(status_code=404, detail="No data found for service")

# Background tasks
async def periodic_cleanup():
    """Periodically clean up old telemetry data"""
    while True:
        try:
            logger.info("Running telemetry data cleanup")
            
            # Clean up old data
            now = time.time()
            cutoff_time = now - DATA_RETENTION_PERIOD
            
            # Clean up transaction traces
            old_transactions = []
            for tx_id, spans in transaction_traces.items():
                if not spans or max(span["timestamp"] for span in spans) < cutoff_time:
                    old_transactions.append(tx_id)
            
            for tx_id in old_transactions:
                del transaction_traces[tx_id]
            
            # Update recent points
            global recent_points
            recent_points = deque(
                [p for p in recent_points if p["timestamp"] >= cutoff_time],
                maxlen=recent_points.maxlen
            )
            
            # Clean up per-service data
            for service_id in list(telemetry_data.keys()):
                telemetry_data[service_id] = deque(
                    [p for p in telemetry_data[service_id] if p["timestamp"] >= cutoff_time],
                    maxlen=MAX_POINTS_PER_SERVICE
                )
            
            logger.info(f"Cleanup complete. Kept {len(recent_points)} recent points, {len(transaction_traces)} transactions")
        
        except Exception as e:
            logger.error(f"Error in telemetry cleanup: {str(e)}")
        
        # Run cleanup every hour
        await asyncio.sleep(3600)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)