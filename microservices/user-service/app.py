import os
import json
import time
import logging
import asyncio
import random
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import httpx
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="User Service")

# Models
class User(BaseModel):
    id: str
    username: str
    email: str
    created_at: float
    metadata: Optional[Dict[str, Any]] = None

class UserCreateRequest(BaseModel):
    username: str
    email: str
    metadata: Optional[Dict[str, Any]] = None

class ServiceConfig(BaseModel):
    capabilities: List[str] = ["user_management", "user_authentication"]
    scaling_factor: float = 1.0
    resource_allocation: Dict[str, float] = {"cpu": 1.0, "memory": 1.0}
    additional_config: Optional[Dict[str, Any]] = None

# Service state
users = {}
service_config = ServiceConfig()
service_id = os.environ.get("SERVICE_ID", "user-service")
service_health = "healthy"
registered_with_apl = False

# Environment variables
APL_URL = os.environ.get("APL_URL", "http://plasticity-layer:8010")
TELEMETRY_URL = os.environ.get("TELEMETRY_URL", "http://telemetry:8050")

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {service_id}")
    asyncio.create_task(register_with_apl())
    asyncio.create_task(send_telemetry())
    
    # Add some test data
    for i in range(10):
        user_id = str(uuid.uuid4())
        users[user_id] = User(
            id=user_id,
            username=f"user{i}",
            email=f"user{i}@example.com",
            created_at=time.time()
        )

# API Endpoints
@app.get("/")
async def root():
    return {
        "service": service_id,
        "status": service_health,
        "capabilities": service_config.capabilities,
        "user_count": len(users)
    }

@app.get("/health")
async def health_check():
    return {"status": service_health}

@app.get("/users")
async def get_users():
    return list(users.values())

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    return users[user_id]

@app.post("/users")
async def create_user(request: UserCreateRequest):
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username=request.username,
        email=request.email,
        created_at=time.time(),
        metadata=request.metadata
    )
    users[user_id] = user
    
    # Simulate some load
    await asyncio.sleep(random.uniform(0.05, 0.2))
    
    return user

@app.put("/users/{user_id}")
async def update_user(user_id: str, request: UserCreateRequest):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_user = users[user_id]
    updated_user = User(
        id=user_id,
        username=request.username,
        email=request.email,
        created_at=existing_user.created_at,
        metadata=request.metadata
    )
    users[user_id] = updated_user
    
    # Simulate some load
    await asyncio.sleep(random.uniform(0.05, 0.2))
    
    return updated_user

@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    deleted_user = users.pop(user_id)
    
    return {"status": "deleted", "user_id": user_id}

@app.get("/config")
async def get_config():
    return service_config

@app.put("/config")
async def update_config(config: ServiceConfig):
    global service_config
    
    # Apply the updated configuration
    old_config = service_config
    service_config = config
    
    logger.info(f"Configuration updated: {config}")
    
    # If capabilities changed, we might need to adjust service behavior
    if set(old_config.capabilities) != set(config.capabilities):
        logger.info(f"Capabilities changed from {old_config.capabilities} to {config.capabilities}")
        await adapt_to_capability_changes(old_config.capabilities, config.capabilities)
    
    # If resource allocation changed, we might need to adjust performance characteristics
    if old_config.resource_allocation != config.resource_allocation:
        logger.info(f"Resource allocation changed")
        await adapt_to_resource_changes(old_config.resource_allocation, config.resource_allocation)
    
    return {"status": "updated", "config": service_config}

@app.post("/shutdown")
async def shutdown():
    """Handle graceful shutdown request"""
    logger.info(f"Shutdown requested for {service_id}")
    
    # In a real system, we would start graceful shutdown procedures
    # For this example, we'll just mark the service as shutting down
    global service_health
    service_health = "shutting_down"
    
    # Deregister from APL
    try:
        async with httpx.AsyncClient() as client:
            await client.delete(f"{APL_URL}/services/{service_id}")
            logger.info(f"Deregistered from APL")
    except Exception as e:
        logger.error(f"Error deregistering from APL: {str(e)}")
    
    # In a real system, we would trigger the actual shutdown with a delay
    # asyncio.create_task(shutdown_after_delay())
    
    return {"status": "shutting_down"}

# Background tasks
async def register_with_apl():
    """Register this service with the Architectural Plasticity Layer"""
    global registered_with_apl
    
    # Wait a short time for everything to start up
    await asyncio.sleep(5)
    
    try:
        logger.info(f"Registering {service_id} with APL")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{APL_URL}/services",
                json={
                    "service_id": service_id,
                    "endpoint": f"http://{service_id}:9000",
                    "capabilities": service_config.capabilities,
                    "dependencies": [],
                    "scaling_factor": service_config.scaling_factor,
                    "resource_allocation": service_config.resource_allocation,
                    "status": "active"
                }
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully registered with APL")
                registered_with_apl = True
            else:
                logger.error(f"Failed to register with APL: {response.status_code}")
    except Exception as e:
        logger.error(f"Error registering with APL: {str(e)}")

async def send_telemetry():
    """Periodically send telemetry data"""
    while True:
        try:
            # Only send if registered
            if registered_with_apl:
                # Gather metrics
                cpu_usage = random.uniform(0.1, 0.5)  # Simulated CPU usage
                memory_usage = random.uniform(0.2, 0.6)  # Simulated memory usage
                request_count = random.randint(5, 20)  # Simulated request count
                error_count = random.randint(0, 2)  # Simulated error count
                
                # Send telemetry
                telemetry_data = {
                    "timestamp": time.time(),
                    "service_id": service_id,
                    "endpoint": f"http://{service_id}:9000",
                    "latency": random.uniform(10, 100),  # ms
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "request_count": request_count,
                    "error_count": error_count
                }
                
                async with httpx.AsyncClient() as client:
                    await client.post(f"{TELEMETRY_URL}/data", json=telemetry_data)
                    logger.debug(f"Sent telemetry data")
        except Exception as e:
            logger.error(f"Error sending telemetry: {str(e)}")
        
        # Send telemetry every 10 seconds
        await asyncio.sleep(10)

async def adapt_to_capability_changes(old_capabilities, new_capabilities):
    """Adapt the service behavior based on capability changes"""
    # In a real system, this would dynamically adjust service behavior
    # For this example, we'll just log the changes
    
    added_capabilities = set(new_capabilities) - set(old_capabilities)
    removed_capabilities = set(old_capabilities) - set(new_capabilities)
    
    if added_capabilities:
        logger.info(f"Added capabilities: {added_capabilities}")
        # Enable new functionality based on added capabilities
        for capability in added_capabilities:
            if capability == "user_profile_management":
                # Simulate adding user profile features
                logger.info("Enabling user profile management features")
                # In a real system, we might load additional modules, etc.
    
    if removed_capabilities:
        logger.info(f"Removed capabilities: {removed_capabilities}")
        # Disable functionality based on removed capabilities
        for capability in removed_capabilities:
            if capability == "user_authentication":
                # Simulate removing authentication features
                logger.info("Disabling user authentication features")
                # In a real system, we might unload modules, etc.

async def adapt_to_resource_changes(old_resources, new_resources):
    """Adapt the service behavior based on resource allocation changes"""
    # In a real system, this would adjust resource usage
    # For this example, we'll just log the changes
    
    for resource, new_value in new_resources.items():
        old_value = old_resources.get(resource, 0)
        if new_value != old_value:
            logger.info(f"Resource {resource} changed from {old_value} to {new_value}")
            
            # Adjust behavior based on resource changes
            if resource == "cpu" and new_value < old_value:
                # Less CPU available, might need to throttle certain operations
                logger.info("Adjusting processing limits due to reduced CPU allocation")
            elif resource == "memory" and new_value < old_value:
                # Less memory available, might need to adjust caching
                logger.info("Adjusting memory usage due to reduced memory allocation")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)