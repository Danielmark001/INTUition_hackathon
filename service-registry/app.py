import os
import json
import time
import logging
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("service-registry")

app = FastAPI(
    title="Metamorphic Architecture Service Registry",
    description="Central registry for service discovery and capabilities tracking",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ServiceInfo(BaseModel):
    service_id: str
    endpoint: str
    capabilities: List[str]
    dependencies: List[str] = []
    scaling_factor: float = 1.0
    resource_allocation: Dict[str, float]
    status: str = "active"
    metadata: Optional[Dict[str, Any]] = None
    last_heartbeat: Optional[float] = None

class HeartbeatRequest(BaseModel):
    service_id: str
    status: str = "active"
    metadata: Optional[Dict[str, Any]] = None

class ServiceQuery(BaseModel):
    capabilities: Optional[List[str]] = None
    status: Optional[str] = None
    min_scaling_factor: Optional[float] = None

# In-memory data stores
services: Dict[str, ServiceInfo] = {}
service_history: Dict[str, List[Dict[str, Any]]] = {}
status_changes: List[Dict[str, Any]] = []

# Configuration
HEARTBEAT_TIMEOUT = int(os.getenv("HEARTBEAT_TIMEOUT", "60"))  # seconds
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))  # seconds

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Service Registry")
    # Start background health checks
    asyncio.create_task(periodic_health_check())

# API Endpoints
@app.get("/", tags=["Status"])
async def root():
    """Get service registry status"""
    return {
        "status": "Service Registry operational",
        "services_registered": len(services),
        "uptime": time.time() - startup_time
    }

@app.get("/services", tags=["Services"])
async def get_services(status: Optional[str] = None):
    """
    Get all registered services, optionally filtered by status
    
    - **status**: Filter services by status (active, degraded, offline)
    """
    if status:
        return [s for s in services.values() if s.status == status]
    return list(services.values())

@app.get("/services/{service_id}", tags=["Services"])
async def get_service(service_id: str):
    """
    Get information about a specific service
    
    - **service_id**: Unique identifier of the service
    """
    if service_id not in services:
        raise HTTPException(status_code=404, detail="Service not found")
    return services[service_id]

@app.post("/services", tags=["Services"])
async def register_service(service: ServiceInfo, background_tasks: BackgroundTasks):
    """
    Register a new service or update an existing one
    
    - **service**: Service information including ID, endpoint, capabilities
    """
    # Set last heartbeat
    service.last_heartbeat = time.time()
    
    # Check if service already exists
    is_new = service.service_id not in services
    
    # Store the service
    services[service.service_id] = service
    
    # Record history
    if service.service_id not in service_history:
        service_history[service.service_id] = []
    
    service_history[service.service_id].append({
        "timestamp": time.time(),
        "action": "register" if is_new else "update",
        "status": service.status,
        "endpoint": service.endpoint,
        "capabilities": service.capabilities
    })
    
    # Record status change if new or status changed
    if is_new or (not is_new and services[service.service_id].status != service.status):
        status_changes.append({
            "timestamp": time.time(),
            "service_id": service.service_id,
            "old_status": None if is_new else services[service.service_id].status,
            "new_status": service.status
        })
    
    # Notify about the registration/update
    background_tasks.add_task(notify_service_change, service.service_id, "register" if is_new else "update")
    
    return {"status": "registered", "service_id": service.service_id}

@app.put("/services/{service_id}", tags=["Services"])
async def update_service(service_id: str, service: ServiceInfo, background_tasks: BackgroundTasks):
    """
    Update an existing service
    
    - **service_id**: ID of the service to update
    - **service**: Updated service information
    """
    if service_id != service.service_id:
        raise HTTPException(status_code=400, detail="Service ID mismatch")
    
    if service_id not in services:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Preserve last heartbeat if not provided
    if not service.last_heartbeat:
        service.last_heartbeat = services[service_id].last_heartbeat
    
    # Check for status change
    old_status = services[service_id].status
    status_changed = old_status != service.status
    
    # Store the updated service
    services[service_id] = service
    
    # Record history
    service_history[service_id].append({
        "timestamp": time.time(),
        "action": "update",
        "status": service.status,
        "endpoint": service.endpoint,
        "capabilities": service.capabilities
    })
    
    # Record status change
    if status_changed:
        status_changes.append({
            "timestamp": time.time(),
            "service_id": service_id,
            "old_status": old_status,
            "new_status": service.status
        })
    
    # Notify about the update
    background_tasks.add_task(notify_service_change, service_id, "update")
    
    return {"status": "updated", "service_id": service_id}

@app.delete("/services/{service_id}", tags=["Services"])
async def deregister_service(service_id: str, background_tasks: BackgroundTasks):
    """
    Deregister a service
    
    - **service_id**: ID of the service to remove
    """
    if service_id not in services:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Record status before removal
    old_status = services[service_id].status
    
    # Remove the service
    service = services.pop(service_id)
    
    # Record history
    if service_id in service_history:
        service_history[service_id].append({
            "timestamp": time.time(),
            "action": "deregister",
            "status": "deleted",
            "endpoint": service.endpoint,
            "capabilities": service.capabilities
        })
    
    # Record status change
    status_changes.append({
        "timestamp": time.time(),
        "service_id": service_id,
        "old_status": old_status,
        "new_status": "deleted"
    })
    
    # Notify about the deregistration
    background_tasks.add_task(notify_service_change, service_id, "deregister")
    
    return {"status": "deregistered", "service_id": service_id}

@app.post("/services/{service_id}/heartbeat", tags=["Monitoring"])
async def service_heartbeat(service_id: str, heartbeat: HeartbeatRequest):
    """
    Record a heartbeat from a service
    
    - **service_id**: ID of the service sending heartbeat
    - **heartbeat**: Heartbeat information including status
    """
    if service_id != heartbeat.service_id:
        raise HTTPException(status_code=400, detail="Service ID mismatch")
    
    if service_id not in services:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Update last heartbeat
    services[service_id].last_heartbeat = time.time()
    
    # Update status if changed
    old_status = services[service_id].status
    if heartbeat.status != old_status:
        services[service_id].status = heartbeat.status
        
        # Record status change
        status_changes.append({
            "timestamp": time.time(),
            "service_id": service_id,
            "old_status": old_status,
            "new_status": heartbeat.status
        })
    
    # Update metadata if provided
    if heartbeat.metadata:
        if not services[service_id].metadata:
            services[service_id].metadata = {}
        services[service_id].metadata.update(heartbeat.metadata)
    
    return {"status": "heartbeat_recorded", "service_id": service_id}

@app.post("/services/query", tags=["Discovery"])
async def query_services(query: ServiceQuery):
    """
    Query services based on capabilities and other criteria
    
    - **query**: Query parameters including capabilities, status
    """
    results = []
    
    for service in services.values():
        # Filter by capabilities if provided
        if query.capabilities:
            # Check if service has all required capabilities
            if not all(cap in service.capabilities for cap in query.capabilities):
                continue
        
        # Filter by status if provided
        if query.status and service.status != query.status:
            continue
        
        # Filter by scaling factor if provided
        if query.min_scaling_factor is not None and service.scaling_factor < query.min_scaling_factor:
            continue
        
        # Service passed all filters
        results.append(service)
    
    return results

@app.get("/services/{service_id}/history", tags=["History"])
async def get_service_history(service_id: str):
    """
    Get the history of a service
    
    - **service_id**: ID of the service
    """
    if service_id not in service_history:
        raise HTTPException(status_code=404, detail="Service history not found")
    
    return service_history[service_id]

@app.get("/status/changes", tags=["History"])
async def get_status_changes(limit: int = 100):
    """
    Get recent service status changes
    
    - **limit**: Maximum number of changes to return
    """
    return status_changes[-limit:]

@app.get("/status/summary", tags=["Status"])
async def get_status_summary():
    """Get a summary of service statuses"""
    summary = {
        "total": len(services),
        "by_status": {},
        "by_capability": {}
    }
    
    # Count by status
    for service in services.values():
        status = service.status
        if status not in summary["by_status"]:
            summary["by_status"][status] = 0
        summary["by_status"][status] += 1
        
        # Count by capability
        for capability in service.capabilities:
            if capability not in summary["by_capability"]:
                summary["by_capability"][capability] = 0
            summary["by_capability"][capability] += 1
    
    return summary

@app.get("/capabilities", tags=["Discovery"])
async def get_capabilities():
    """Get all unique capabilities across registered services"""
    all_capabilities = set()
    capability_count = {}
    
    for service in services.values():
        for capability in service.capabilities:
            all_capabilities.add(capability)
            if capability not in capability_count:
                capability_count[capability] = 0
            capability_count[capability] += 1
    
    return {
        "capabilities": sorted(list(all_capabilities)),
        "count_by_capability": capability_count
    }

# Background tasks
async def periodic_health_check():
    """Periodically check service health based on heartbeats"""
    while True:
        try:
            logger.info("Running service health check")
            now = time.time()
            
            for service_id, service in list(services.items()):
                # Check for heartbeat timeout
                if service.last_heartbeat and now - service.last_heartbeat > HEARTBEAT_TIMEOUT:
                    # Service missed heartbeats, mark as potentially unhealthy
                    if service.status == "active":
                        old_status = service.status
                        service.status = "degraded"
                        
                        # Record status change
                        status_changes.append({
                            "timestamp": now,
                            "service_id": service_id,
                            "old_status": old_status,
                            "new_status": "degraded",
                            "reason": "heartbeat_timeout"
                        })
                        
                        logger.warning(f"Service {service_id} marked as degraded due to missed heartbeats")
                
                # If a service has been degraded for too long, mark it as offline
                elif service.status == "degraded" and now - service.last_heartbeat > HEARTBEAT_TIMEOUT * 2:
                    old_status = service.status
                    service.status = "offline"
                    
                    # Record status change
                    status_changes.append({
                        "timestamp": now,
                        "service_id": service_id,
                        "old_status": old_status,
                        "new_status": "offline",
                        "reason": "extended_heartbeat_timeout"
                    })
                    
                    logger.warning(f"Service {service_id} marked as offline due to extended missed heartbeats")
        
        except Exception as e:
            logger.error(f"Error in health check: {str(e)}")
        
        # Run health check at the specified interval
        await asyncio.sleep(HEALTH_CHECK_INTERVAL)

async def notify_service_change(service_id: str, action: str):
    """Notify interested parties about service changes"""
    # This would integrate with event buses, message queues, etc. in a production environment
    logger.info(f"Service change notification: {service_id} - {action}")
    
    # For now, just log the notification
    # In a real system, this might call other services or publish to a message bus
    if service_id in services:
        logger.info(f"Service {service_id} {action}: {services[service_id].status}")
    else:
        logger.info(f"Service {service_id} {action}: removed")

# Initialize startup time
startup_time = time.time()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8040)