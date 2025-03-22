import os
import json
import logging
import requests
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import httpx
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Architectural Plasticity Layer")

# Models
class ServiceConfig(BaseModel):
    service_id: str
    endpoint: str
    capabilities: List[str]
    dependencies: List[str]
    scaling_factor: float = 1.0
    resource_allocation: Dict[str, float]
    status: str = "active"

class ArchitectureTransition(BaseModel):
    transition_id: str
    from_state: Dict[str, Any]
    to_state: Dict[str, Any]
    status: str = "pending"
    transition_plan: Optional[List[Dict[str, Any]]] = None

# In-memory store (would use a database in production)
service_registry = {}
active_transitions = {}
architecture_history = []
current_architecture_state = {"version": 0, "services": {}}

SERVICE_REGISTRY_URL = os.environ.get("SERVICE_REGISTRY_URL", "http://service-registry:8040")

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Architectural Plasticity Layer")
    try:
        # Load initial configuration from service registry
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVICE_REGISTRY_URL}/services")
            if response.status_code == 200:
                services = response.json()
                for service in services:
                    service_registry[service["service_id"]] = ServiceConfig(**service)
                logger.info(f"Loaded {len(services)} services from registry")
                
                # Initialize current architecture state
                current_architecture_state["services"] = {
                    s_id: {"status": s.status, "capabilities": s.capabilities, 
                           "resource_allocation": s.resource_allocation}
                    for s_id, s in service_registry.items()
                }
                current_architecture_state["version"] = 1
                architecture_history.append(current_architecture_state.copy())
            else:
                logger.warning("Failed to load services from registry, starting with empty configuration")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

# API Endpoints
@app.get("/")
async def root():
    return {"status": "Architectural Plasticity Layer operational"}

@app.get("/services")
async def get_services():
    return list(service_registry.values())

@app.get("/services/{service_id}")
async def get_service(service_id: str):
    if service_id not in service_registry:
        raise HTTPException(status_code=404, detail="Service not found")
    return service_registry[service_id]

@app.post("/services")
async def register_service(service: ServiceConfig):
    service_registry[service.service_id] = service
    # Update current architecture state
    current_architecture_state["services"][service.service_id] = {
        "status": service.status, 
        "capabilities": service.capabilities,
        "resource_allocation": service.resource_allocation
    }
    current_architecture_state["version"] += 1
    architecture_history.append(current_architecture_state.copy())
    
    # Notify service registry
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{SERVICE_REGISTRY_URL}/services", json=service.dict())
    except Exception as e:
        logger.error(f"Failed to notify service registry: {str(e)}")
        
    return {"status": "Service registered", "service_id": service.service_id}

@app.put("/services/{service_id}")
async def update_service(service_id: str, service: ServiceConfig):
    if service_id not in service_registry:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service_registry[service_id] = service
    
    # Update current architecture state
    current_architecture_state["services"][service_id] = {
        "status": service.status, 
        "capabilities": service.capabilities,
        "resource_allocation": service.resource_allocation
    }
    current_architecture_state["version"] += 1
    architecture_history.append(current_architecture_state.copy())
    
    # Notify service registry
    try:
        async with httpx.AsyncClient() as client:
            await client.put(f"{SERVICE_REGISTRY_URL}/services/{service_id}", json=service.dict())
    except Exception as e:
        logger.error(f"Failed to notify service registry: {str(e)}")
    
    return {"status": "Service updated", "service_id": service_id}

@app.delete("/services/{service_id}")
async def deregister_service(service_id: str):
    if service_id not in service_registry:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service = service_registry.pop(service_id)
    
    # Update current architecture state
    if service_id in current_architecture_state["services"]:
        del current_architecture_state["services"][service_id]
        current_architecture_state["version"] += 1
        architecture_history.append(current_architecture_state.copy())
    
    # Notify service registry
    try:
        async with httpx.AsyncClient() as client:
            await client.delete(f"{SERVICE_REGISTRY_URL}/services/{service_id}")
    except Exception as e:
        logger.error(f"Failed to notify service registry: {str(e)}")
    
    return {"status": "Service deregistered", "service_id": service_id}

# Architecture transition management
@app.post("/transitions")
async def start_transition(transition: ArchitectureTransition, background_tasks: BackgroundTasks):
    active_transitions[transition.transition_id] = transition
    
    # Start the transition process in the background
    background_tasks.add_task(execute_transition, transition)
    
    return {"status": "Transition started", "transition_id": transition.transition_id}

@app.get("/transitions/{transition_id}")
async def get_transition_status(transition_id: str):
    if transition_id not in active_transitions:
        raise HTTPException(status_code=404, detail="Transition not found")
    return active_transitions[transition_id]

@app.get("/architecture/current")
async def get_current_architecture():
    return current_architecture_state

@app.get("/architecture/history")
async def get_architecture_history():
    return architecture_history

async def execute_transition(transition: ArchitectureTransition):
    """Execute an architecture transition plan"""
    try:
        logger.info(f"Starting transition {transition.transition_id}")
        transition.status = "in_progress"
        
        # Here we would implement the actual transition logic
        # This would involve:
        # 1. Service reconfiguration
        # 2. Traffic routing updates
        # 3. Resource allocation changes
        # 4. State migration if needed
        
        # For this example, we'll just simulate a transition with delays
        if not transition.transition_plan:
            # Generate a simple transition plan if none provided
            transition.transition_plan = generate_transition_plan(
                transition.from_state, transition.to_state)
        
        for step in transition.transition_plan:
            logger.info(f"Executing step: {step['description']}")
            
            # Execute the actual step based on type
            if step["type"] == "service_update":
                await update_service_configuration(step["service_id"], step["config"])
            elif step["type"] == "service_create":
                await create_service(step["service_id"], step["config"])
            elif step["type"] == "service_delete":
                await remove_service(step["service_id"])
            elif step["type"] == "routing_update":
                await update_routing(step["routing_config"])
            
            # Simulate work with a delay
            await asyncio.sleep(2)
            step["status"] = "completed"
        
        # Update the current architecture state
        global current_architecture_state
        current_architecture_state = transition.to_state.copy()
        current_architecture_state["version"] += 1
        architecture_history.append(current_architecture_state.copy())
        
        transition.status = "completed"
        logger.info(f"Transition {transition.transition_id} completed successfully")
    
    except Exception as e:
        logger.error(f"Transition {transition.transition_id} failed: {str(e)}")
        transition.status = "failed"

def generate_transition_plan(from_state, to_state):
    """Generate a plan to transition between architecture states"""
    plan = []
    
    # Identify services to remove
    for service_id in from_state.get("services", {}):
        if service_id not in to_state.get("services", {}):
            plan.append({
                "type": "service_delete",
                "service_id": service_id,
                "description": f"Remove service {service_id}",
                "status": "pending"
            })
    
    # Identify services to update
    for service_id, service in to_state.get("services", {}).items():
        if service_id in from_state.get("services", {}):
            # Service exists in both states, check for changes
            if service != from_state["services"][service_id]:
                plan.append({
                    "type": "service_update",
                    "service_id": service_id,
                    "config": service,
                    "description": f"Update service {service_id}",
                    "status": "pending"
                })
        else:
            # New service
            plan.append({
                "type": "service_create",
                "service_id": service_id,
                "config": service,
                "description": f"Create new service {service_id}",
                "status": "pending"
            })
    
    # Add routing updates if needed
    if "routing" in to_state and to_state["routing"] != from_state.get("routing"):
        plan.append({
            "type": "routing_update",
            "routing_config": to_state["routing"],
            "description": "Update routing configuration",
            "status": "pending"
        })
    
    return plan

async def update_service_configuration(service_id, config):
    """Update a service's configuration"""
    # In a real system, this would make API calls to the service
    # to update its configuration, scaling, etc.
    if service_id in service_registry:
        service = service_registry[service_id]
        # Update service properties
        for key, value in config.items():
            if hasattr(service, key):
                setattr(service, key, value)
        
        # Notify the service of configuration changes
        try:
            async with httpx.AsyncClient() as client:
                await client.put(f"{service.endpoint}/config", json=config)
        except Exception as e:
            logger.error(f"Failed to update service {service_id}: {str(e)}")
            # In a real system, we might want to retry or rollback

async def create_service(service_id, config):
    """Create a new service"""
    # In a real system, this might involve container orchestration
    # For this example, we'll just update our registry
    service_registry[service_id] = ServiceConfig(
        service_id=service_id,
        endpoint=config.get("endpoint", f"http://{service_id}:8000"),
        capabilities=config.get("capabilities", []),
        dependencies=config.get("dependencies", []),
        scaling_factor=config.get("scaling_factor", 1.0),
        resource_allocation=config.get("resource_allocation", {"cpu": 1.0, "memory": 1.0}),
        status="starting"
    )
    
    # Simulate service startup
    await asyncio.sleep(1)
    service_registry[service_id].status = "active"

async def remove_service(service_id):
    """Remove a service"""
    if service_id in service_registry:
        # Gracefully shut down the service
        try:
            service = service_registry[service_id]
            async with httpx.AsyncClient() as client:
                await client.post(f"{service.endpoint}/shutdown")
        except Exception as e:
            logger.error(f"Failed to gracefully shut down service {service_id}: {str(e)}")
        
        # Remove from registry
        service_registry.pop(service_id)

async def update_routing(routing_config):
    """Update the routing configuration"""
    # In a real system, this would update API gateways,
    # service meshes, or load balancers
    logger.info(f"Updating routing configuration: {routing_config}")
    # Simulate work
    await asyncio.sleep(1)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)