import os
import json
import uuid
import logging
import time
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any, Union
import httpx
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Metamorphosis Engine")

# Add CORS middleware for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ArchitectureState(BaseModel):
    version: int
    services: Dict[str, Any]
    routing: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class TransformationPlan(BaseModel):
    id: str
    name: str
    description: str
    source_recommendations: Optional[List[Dict[str, Any]]] = None
    current_state: ArchitectureState
    target_state: ArchitectureState
    transformation_steps: List[Dict[str, Any]]
    status: str = "created"
    created_at: float
    updated_at: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None

class PatternReport(BaseModel):
    patterns: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    confidence: float
    timestamp: float

class TransformationRequest(BaseModel):
    name: str
    description: str
    recommendations: Optional[List[Dict[str, Any]]] = None
    target_state: Optional[Dict[str, Any]] = None
    auto_generate: Optional[bool] = False

# Environment variables
APL_SERVICE_URL = os.environ.get("APL_SERVICE_URL", "http://plasticity-layer:8010")
PATTERN_INTELLIGENCE_URL = os.environ.get("PATTERN_INTELLIGENCE_URL", "http://pattern-intelligence:8020")
OPTIMIZER_URL = os.environ.get("OPTIMIZER_URL", "http://optimizer:8030")

# In-memory data stores (would be a database in production)
transformation_plans = {}
active_transformations = {}
system_architecture_history = []
current_system_state = None
detected_patterns = []

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Metamorphosis Engine")
    # Start background tasks
    asyncio.create_task(periodic_pattern_check())
    asyncio.create_task(load_initial_state())

# API Endpoints
@app.get("/")
async def root():
    return {"status": "Metamorphosis Engine operational"}

@app.get("/architecture/current")
async def get_current_architecture():
    """Get the current architecture state"""
    global current_system_state
    if not current_system_state:
        raise HTTPException(status_code=404, detail="System state not initialized")
    return current_system_state

@app.get("/architecture/history")
async def get_architecture_history(limit: int = 10):
    """Get architecture state history"""
    return system_architecture_history[-limit:] if system_architecture_history else []

@app.get("/patterns")
async def get_detected_patterns():
    """Get detected system patterns"""
    return detected_patterns

@app.post("/transformations")
async def create_transformation(
    request: TransformationRequest,
    background_tasks: BackgroundTasks
):
    """Create a new architectural transformation plan"""
    global current_system_state
    
    if current_system_state is None:
        raise HTTPException(status_code=400, detail="System state not initialized")
    
    plan_id = str(uuid.uuid4())
    now = time.time()
    
    # Create a new transformation plan
    new_plan = TransformationPlan(
        id=plan_id,
        name=request.name,
        description=request.description,
        source_recommendations=request.recommendations,
        current_state=current_system_state,
        target_state=current_system_state.copy() if not request.target_state else ArchitectureState(**request.target_state),
        transformation_steps=[],
        status="created",
        created_at=now,
        updated_at=now
    )
    
    # Store the plan
    transformation_plans[plan_id] = new_plan
    
    # If auto-generate is enabled, generate the transformation steps
    if request.auto_generate:
        background_tasks.add_task(generate_transformation_plan, plan_id)
        new_plan.status = "generating"
    
    return {"status": "created", "plan_id": plan_id}

@app.get("/transformations")
async def list_transformations():
    """List all transformation plans"""
    return list(transformation_plans.values())

@app.get("/transformations/{plan_id}")
async def get_transformation(plan_id: str):
    """Get a specific transformation plan"""
    if plan_id not in transformation_plans:
        raise HTTPException(status_code=404, detail="Transformation plan not found")
    return transformation_plans[plan_id]

@app.post("/transformations/{plan_id}/execute")
async def execute_transformation(
    plan_id: str,
    background_tasks: BackgroundTasks
):
    """Execute a transformation plan"""
    if plan_id not in transformation_plans:
        raise HTTPException(status_code=404, detail="Transformation plan not found")
    
    plan = transformation_plans[plan_id]
    if plan.status not in ["ready", "failed"]:
        raise HTTPException(status_code=400, detail=f"Plan cannot be executed in status: {plan.status}")
    
    if not plan.transformation_steps:
        raise HTTPException(status_code=400, detail="Plan has no transformation steps")
    
    # Update status
    plan.status = "executing"
    plan.updated_at = time.time()
    
    # Start execution in background
    background_tasks.add_task(execute_transformation_plan, plan_id)
    
    return {"status": "executing", "plan_id": plan_id}

@app.post("/transformations/{plan_id}/generate")
async def generate_plan(
    plan_id: str,
    background_tasks: BackgroundTasks
):
    """Generate transformation steps for a plan"""
    if plan_id not in transformation_plans:
        raise HTTPException(status_code=404, detail="Transformation plan not found")
    
    plan = transformation_plans[plan_id]
    if plan.status != "created":
        raise HTTPException(status_code=400, detail=f"Plan generation not allowed in status: {plan.status}")
    
    # Update status
    plan.status = "generating"
    plan.updated_at = time.time()
    
    # Start generation in background
    background_tasks.add_task(generate_transformation_plan, plan_id)
    
    return {"status": "generating", "plan_id": plan_id}

@app.post("/analyze")
async def analyze_system(background_tasks: BackgroundTasks):
    """Trigger a system analysis to detect patterns and generate recommendations"""
    background_tasks.add_task(analyze_system_patterns)
    return {"status": "Analysis started"}

@app.get("/recommendations")
async def get_recommendations():
    """Get architectural recommendations based on detected patterns"""
    recommendations = []
    for pattern in detected_patterns:
        if "recommendations" in pattern:
            recommendations.extend(pattern["recommendations"])
    
    return recommendations

@app.get("/status")
async def get_system_status():
    """Get overall system status"""
    active_count = sum(1 for plan in transformation_plans.values() if plan.status == "executing")
    
    return {
        "system_initialized": current_system_state is not None,
        "detected_pattern_count": len(detected_patterns),
        "transformation_plans": {
            "total": len(transformation_plans),
            "active": active_count,
            "completed": sum(1 for plan in transformation_plans.values() if plan.status == "completed"),
            "failed": sum(1 for plan in transformation_plans.values() if plan.status == "failed")
        },
        "last_analysis": detected_patterns[-1]["timestamp"] if detected_patterns else None
    }

@app.post("/apply-recommendation/{recommendation_id}")
async def apply_recommendation(
    recommendation_id: str,
    background_tasks: BackgroundTasks
):
    """Create a transformation plan from a specific recommendation"""
    # Find the recommendation
    recommendation = None
    source_pattern = None
    
    for pattern in detected_patterns:
        if "recommendations" not in pattern:
            continue
            
        for rec in pattern["recommendations"]:
            if rec.get("id") == recommendation_id:
                recommendation = rec
                source_pattern = pattern
                break
        
        if recommendation:
            break
    
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    # Create a transformation plan
    plan_id = str(uuid.uuid4())
    now = time.time()
    
    # Create a basic transformation based on the recommendation
    new_plan = TransformationPlan(
        id=plan_id,
        name=f"Apply recommendation: {recommendation.get('description', 'Unnamed')}",
        description=f"Auto-generated plan from recommendation {recommendation_id}",
        source_recommendations=[recommendation],
        current_state=current_system_state,
        target_state=current_system_state.copy(),
        transformation_steps=[],
        status="generating",
        created_at=now,
        updated_at=now
    )
    
    # Store the plan
    transformation_plans[plan_id] = new_plan
    
    # Generate the transformation steps based on the recommendation
    background_tasks.add_task(generate_plan_from_recommendation, plan_id, recommendation, source_pattern)
    
    return {"status": "generating", "plan_id": plan_id}

@app.get("/dashboard-data")
async def get_dashboard_data():
    """Get aggregated data for the dashboard"""
    if not current_system_state:
        raise HTTPException(status_code=404, detail="System state not initialized")
    
    # Get service health metrics
    service_metrics = {}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PATTERN_INTELLIGENCE_URL}/metrics")
            if response.status_code == 200:
                metrics_data = response.json()
                # Process metrics for dashboard format
                for service_id, metrics in metrics_data.items():
                    if metrics:
                        latest = metrics[-1]
                        service_metrics[service_id] = {
                            "cpu": latest.get("cpu_usage", 0),
                            "memory": latest.get("memory_usage", 0),
                            "requests": latest.get("request_count", 0),
                            "errors": latest.get("error_count", 0),
                            "latency": latest.get("latency", 0)
                        }
    except Exception as e:
        logger.error(f"Error fetching service metrics: {str(e)}")
    
    # Calculate transformation statistics
    transform_stats = {
        "total": len(transformation_plans),
        "active": sum(1 for p in transformation_plans.values() if p.status == "executing"),
        "completed": sum(1 for p in transformation_plans.values() if p.status == "completed"),
        "failed": sum(1 for p in transformation_plans.values() if p.status == "failed"),
        "recent": sorted(
            [p for p in transformation_plans.values()],
            key=lambda p: p.updated_at or 0, 
            reverse=True
        )[:5]
    }
    
    # Get recommendations count
    recommendation_count = sum(
        len(pattern.get("recommendations", [])) 
        for pattern in detected_patterns
    )
    
    return {
        "current_state": current_system_state,
        "service_count": len(current_system_state.services) if current_system_state else 0,
        "service_metrics": service_metrics,
        "transformation_stats": transform_stats,
        "pattern_count": len(detected_patterns),
        "recommendation_count": recommendation_count,
        "system_health": {
            "overall": "healthy",  # Simplified for this example
            "services": {
                s_id: "healthy" for s_id in current_system_state.services
            } if current_system_state else {}
        }
    }

# Background tasks
async def periodic_pattern_check():
    """Periodically check for new system patterns"""
    while True:
        try:
            await analyze_system_patterns()
        except Exception as e:
            logger.error(f"Error in periodic pattern check: {str(e)}")
        
        # Check every 5 minutes
        await asyncio.sleep(300)

async def load_initial_state():
    """Load initial system state"""
    global current_system_state
    try:
        # Get the current state from the Architectural Plasticity Layer
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{APL_SERVICE_URL}/architecture/current")
            if response.status_code == 200:
                state_data = response.json()
                current_system_state = ArchitectureState(**state_data)
                system_architecture_history.append(current_system_state)
                logger.info("Loaded initial system state")
            else:
                logger.warning(f"Failed to load initial state: {response.status_code}")
                # Create a basic initial state
                current_system_state = ArchitectureState(
                    version=1,
                    services={},
                    routing={},
                    resources={},
                    metadata={"initialized": time.time()}
                )
                system_architecture_history.append(current_system_state)
    except Exception as e:
        logger.error(f"Error loading initial state: {str(e)}")
        # Create a fallback initial state
        current_system_state = ArchitectureState(
            version=1,
            services={},
            routing={},
            resources={},
            metadata={"initialized": time.time(), "error": str(e)}
        )
        system_architecture_history.append(current_system_state)

async def analyze_system_patterns():
    """Analyze system for patterns and generate recommendations"""
    global detected_patterns
    
    logger.info("Analyzing system patterns")
    
    try:
        # Request pattern analysis from the Pattern Intelligence service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PATTERN_INTELLIGENCE_URL}/patterns/system",
                json={"time_window": 3600, "min_confidence": 0.6}
            )
            
            if response.status_code == 200:
                patterns = response.json()
                if patterns:
                    # Add timestamp and IDs to patterns
                    now = time.time()
                    for i, pattern in enumerate(patterns):
                        pattern["timestamp"] = now
                        pattern["id"] = f"pattern_{now}_{i}"
                        
                        # Add IDs to recommendations
                        if "recommendations" in pattern:
                            for j, rec in enumerate(pattern["recommendations"]):
                                rec["id"] = f"rec_{now}_{i}_{j}"
                    
                    # Store patterns
                    detected_patterns.extend(patterns)
                    logger.info(f"Detected {len(patterns)} new patterns")
                else:
                    logger.info("No new patterns detected")
            else:
                logger.warning(f"Failed to analyze patterns: {response.status_code}")
    except Exception as e:
        logger.error(f"Error analyzing patterns: {str(e)}")

async def generate_transformation_plan(plan_id: str):
    """Generate a transformation plan based on target state and recommendations"""
    if plan_id not in transformation_plans:
        logger.error(f"Plan {plan_id} not found")
        return
    
    plan = transformation_plans[plan_id]
    try:
        logger.info(f"Generating transformation plan {plan_id}")
        
        # 1. Identify differences between current and target states
        changes = identify_state_changes(plan.current_state, plan.target_state)
        
        # 2. Generate transformation steps
        steps = []
        
        # Process service changes
        for service_id, change in changes.get("services", {}).items():
            if change["action"] == "add":
                steps.append({
                    "id": f"step_{len(steps)+1}",
                    "type": "add_service",
                    "service_id": service_id,
                    "config": change["config"],
                    "description": f"Add new service: {service_id}",
                    "status": "pending",
                    "dependencies": []
                })
            elif change["action"] == "remove":
                steps.append({
                    "id": f"step_{len(steps)+1}",
                    "type": "remove_service",
                    "service_id": service_id,
                    "description": f"Remove service: {service_id}",
                    "status": "pending",
                    "dependencies": []
                })
            elif change["action"] == "update":
                steps.append({
                    "id": f"step_{len(steps)+1}",
                    "type": "update_service",
                    "service_id": service_id,
                    "config": change["config"],
                    "changes": change["changes"],
                    "description": f"Update service: {service_id}",
                    "status": "pending",
                    "dependencies": []
                })
        
        # Process routing changes
        if "routing" in changes:
            steps.append({
                "id": f"step_{len(steps)+1}",
                "type": "update_routing",
                "routing_config": plan.target_state.routing,
                "description": "Update routing configuration",
                "status": "pending",
                "dependencies": [s["id"] for s in steps if s["type"] in ["add_service", "update_service"]]
            })
        
        # 3. Resolve dependencies between steps
        steps = resolve_step_dependencies(steps)
        
        # 4. Update the plan
        plan.transformation_steps = steps
        plan.status = "ready"
        plan.updated_at = time.time()
        
        logger.info(f"Generated transformation plan with {len(steps)} steps")
    
    except Exception as e:
        logger.error(f"Error generating transformation plan: {str(e)}")
        plan.status = "failed"
        plan.updated_at = time.time()
        plan.metadata = plan.metadata or {}
        plan.metadata["error"] = str(e)

async def execute_transformation_plan(plan_id: str):
    """Execute a transformation plan"""
    global current_system_state
    
    if plan_id not in transformation_plans:
        logger.error(f"Plan {plan_id} not found")
        return
    
    plan = transformation_plans[plan_id]
    
    try:
        logger.info(f"Executing transformation plan {plan_id}")
        
        # Track execution metrics
        start_time = time.time()
        step_results = []
        
        # Execute steps in order based on dependencies
        for step in plan.transformation_steps:
            # Check if dependencies are fulfilled
            dependencies_met = all(
                any(s["id"] == dep and s["status"] == "completed" for s in plan.transformation_steps)
                for dep in step["dependencies"]
            )
            
            if not dependencies_met:
                logger.warning(f"Skipping step {step['id']} as dependencies are not met")
                step["status"] = "skipped"
                continue
            
            logger.info(f"Executing step: {step['description']}")
            step["status"] = "executing"
            
            # Execute the step based on type
            try:
                if step["type"] == "add_service":
                    await execute_add_service_step(step)
                elif step["type"] == "remove_service":
                    await execute_remove_service_step(step)
                elif step["type"] == "update_service":
                    await execute_update_service_step(step)
                elif step["type"] == "update_routing":
                    await execute_update_routing_step(step)
                else:
                    logger.warning(f"Unknown step type: {step['type']}")
                    step["status"] = "failed"
                    step["error"] = "Unknown step type"
                    continue
                
                step["status"] = "completed"
                step["completed_at"] = time.time()
                step_results.append({
                    "step_id": step["id"],
                    "success": True,
                    "duration": step.get("completed_at", time.time()) - start_time
                })
            
            except Exception as e:
                logger.error(f"Error executing step {step['id']}: {str(e)}")
                step["status"] = "failed"
                step["error"] = str(e)
                step_results.append({
                    "step_id": step["id"],
                    "success": False,
                    "error": str(e)
                })
                
                # Mark the plan as failed
                plan.status = "failed"
                plan.updated_at = time.time()
                plan.metrics = {
                    "total_steps": len(plan.transformation_steps),
                    "completed_steps": sum(1 for s in plan.transformation_steps if s["status"] == "completed"),
                    "failed_steps": sum(1 for s in plan.transformation_steps if s["status"] == "failed"),
                    "duration": time.time() - start_time,
                    "step_results": step_results
                }
                return
        
        # Update system state
        current_system_state = plan.target_state.copy()
        current_system_state.version += 1
        current_system_state.metadata = current_system_state.metadata or {}
        current_system_state.metadata["last_updated"] = time.time()
        current_system_state.metadata["transformation_plan"] = plan_id
        
        # Add to history
        system_architecture_history.append(current_system_state)
        
        # Mark the plan as completed
        plan.status = "completed"
        plan.updated_at = time.time()
        plan.metrics = {
            "total_steps": len(plan.transformation_steps),
            "completed_steps": sum(1 for s in plan.transformation_steps if s["status"] == "completed"),
            "failed_steps": sum(1 for s in plan.transformation_steps if s["status"] == "failed"),
            "duration": time.time() - start_time,
            "step_results": step_results
        }
        
        logger.info(f"Transformation plan {plan_id} completed successfully")
    
    except Exception as e:
        logger.error(f"Error executing transformation plan: {str(e)}")
        plan.status = "failed"
        plan.updated_at = time.time()
        plan.metadata = plan.metadata or {}
        plan.metadata["error"] = str(e)

async def generate_plan_from_recommendation(plan_id: str, recommendation: Dict[str, Any], source_pattern: Dict[str, Any]):
    """Generate a transformation plan from a specific recommendation"""
    if plan_id not in transformation_plans:
        logger.error(f"Plan {plan_id} not found")
        return
    
    plan = transformation_plans[plan_id]
    
    try:
        logger.info(f"Generating plan from recommendation: {recommendation.get('description')}")
        
        # Create target state based on recommendation type
        target_state = plan.current_state.copy()
        recommendation_type = recommendation.get("type")
        
        if recommendation_type == "service_coupling":
            # Handle service merging recommendation
            if recommendation.get("action") == "merge_services" and "services" in source_pattern:
                services_to_merge = source_pattern["services"]
                if len(services_to_merge) >= 2:
                    # Create a new merged service
                    new_service_id = f"merged_{'_'.join(services_to_merge)}"
                    
                    # Combine capabilities and resources
                    merged_capabilities = []
                    merged_resources = {"cpu": 0, "memory": 0}
                    
                    for service_id in services_to_merge:
                        if service_id in plan.current_state.services:
                            service = plan.current_state.services[service_id]
                            if "capabilities" in service:
                                merged_capabilities.extend(service.get("capabilities", []))
                            if "resource_allocation" in service:
                                for resource, value in service.get("resource_allocation", {}).items():
                                    merged_resources[resource] = merged_resources.get(resource, 0) + value
                    
                    # Create the merged service
                    target_state.services[new_service_id] = {
                        "status": "active",
                        "capabilities": list(set(merged_capabilities)),  # Deduplicate
                        "resource_allocation": merged_resources,
                        "created_from": services_to_merge
                    }
                    
                    # Remove the original services
                    for service_id in services_to_merge:
                        if service_id in target_state.services:
                            target_state.services.pop(service_id)
        
        elif recommendation_type == "resource_utilization":
            # Handle resource adjustment recommendation
            if "service_id" in source_pattern:
                service_id = source_pattern["service_id"]
                if service_id in target_state.services:
                    action = recommendation.get("action")
                    if action == "reduce_resources":
                        # Reduce resources by 30%
                        if "resource_allocation" in target_state.services[service_id]:
                            for resource, value in target_state.services[service_id]["resource_allocation"].items():
                                target_state.services[service_id]["resource_allocation"][resource] = value * 0.7
                    elif action == "increase_resources":
                        # Increase resources by 30%
                        if "resource_allocation" in target_state.services[service_id]:
                            for resource, value in target_state.services[service_id]["resource_allocation"].items():
                                target_state.services[service_id]["resource_allocation"][resource] = value * 1.3
        
        # Update the plan with target state
        plan.target_state = target_state
        
        # Now generate the transformation steps
        await generate_transformation_plan(plan_id)
    
    except Exception as e:
        logger.error(f"Error generating plan from recommendation: {str(e)}")
        plan.status = "failed"
        plan.updated_at = time.time()
        plan.metadata = plan.metadata or {}
        plan.metadata["error"] = str(e)

# Helper functions
def identify_state_changes(current_state: ArchitectureState, target_state: ArchitectureState):
    """Identify differences between current and target states"""
    changes = {"services": {}}
    
    # Compare services
    current_services = current_state.services or {}
    target_services = target_state.services or {}
    
    # Find services to add or update
    for service_id, target_service in target_services.items():
        if service_id not in current_services:
            # New service
            changes["services"][service_id] = {
                "action": "add",
                "config": target_service
            }
        else:
            # Compare existing service
            current_service = current_services[service_id]
            service_changes = {}
            
            # Compare each field
            for key, value in target_service.items():
                if key not in current_service or current_service[key] != value:
                    service_changes[key] = value
            
            if service_changes:
                changes["services"][service_id] = {
                    "action": "update",
                    "changes": service_changes,
                    "config": target_service
                }
    
    # Find services to remove
    for service_id in current_services:
        if service_id not in target_services:
            changes["services"][service_id] = {
                "action": "remove"
            }
    
    # Compare routing configuration
    if hasattr(target_state, "routing") and target_state.routing:
        if not hasattr(current_state, "routing") or current_state.routing != target_state.routing:
            changes["routing"] = target_state.routing
    
    # Compare resource configuration
    if hasattr(target_state, "resources") and target_state.resources:
        if not hasattr(current_state, "resources") or current_state.resources != target_state.resources:
            changes["resources"] = target_state.resources
    
    return changes

def resolve_step_dependencies(steps):
    """Resolve dependencies between transformation steps"""
    # Build a basic dependency graph
    for i, step in enumerate(steps):
        # Service removals should happen after all other operations
        if step["type"] == "remove_service":
            for j, other_step in enumerate(steps):
                if i != j and other_step["type"] != "remove_service":
                    if step["id"] not in other_step["dependencies"]:
                        other_step["dependencies"].append(step["id"])
        
        # Service updates should happen after service additions
        if step["type"] == "update_service":
            for j, other_step in enumerate(steps):
                if other_step["type"] == "add_service" and other_step["service_id"] == step["service_id"]:
                    if other_step["id"] not in step["dependencies"]:
                        step["dependencies"].append(other_step["id"])
    
    # Topologically sort steps based on dependencies
    # (simplified for this example - in a real system this would be more sophisticated)
    sorted_steps = []
    visited = set()
    
    def visit(step):
        if step["id"] in visited:
            return
        visited.add(step["id"])
        
        for dep_id in step["dependencies"]:
            dep_step = next((s for s in steps if s["id"] == dep_id), None)
            if dep_step:
                visit(dep_step)
        
        sorted_steps.append(step)
    
    for step in steps:
        if step["id"] not in visited:
            visit(step)
    
    return sorted_steps

async def execute_add_service_step(step):
    """Execute a step to add a new service"""
    service_id = step["service_id"]
    config = step["config"]
    
    try:
        # Call the Architectural Plasticity Layer to register the service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{APL_SERVICE_URL}/services",
                json={
                    "service_id": service_id,
                    "endpoint": config.get("endpoint", f"http://{service_id}:8000"),
                    "capabilities": config.get("capabilities", []),
                    "dependencies": config.get("dependencies", []),
                    "scaling_factor": config.get("scaling_factor", 1.0),
                    "resource_allocation": config.get("resource_allocation", {"cpu": 1.0, "memory": 1.0}),
                    "status": "starting"
                }
            )
            
            if response.status_code not in [200, 201]:
                raise Exception(f"Failed to add service: {response.status_code}")
            
            # In a real system, we would also trigger container creation, etc.
            logger.info(f"Service {service_id} added successfully")
    
    except Exception as e:
        logger.error(f"Error adding service {service_id}: {str(e)}")
        raise

async def execute_remove_service_step(step):
    """Execute a step to remove a service"""
    service_id = step["service_id"]
    
    try:
        # Call the Architectural Plasticity Layer to deregister the service
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{APL_SERVICE_URL}/services/{service_id}")
            
            if response.status_code not in [200, 204]:
                raise Exception(f"Failed to remove service: {response.status_code}")
            
            # In a real system, we would also trigger container removal, etc.
            logger.info(f"Service {service_id} removed successfully")
    
    except Exception as e:
        logger.error(f"Error removing service {service_id}: {str(e)}")
        raise

async def execute_update_service_step(step):
    """Execute a step to update a service"""
    service_id = step["service_id"]
    config = step["config"]
    
    try:
        # Call the Architectural Plasticity Layer to update the service
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{APL_SERVICE_URL}/services/{service_id}",
                json={
                    "service_id": service_id,
                    "endpoint": config.get("endpoint", f"http://{service_id}:8000"),
                    "capabilities": config.get("capabilities", []),
                    "dependencies": config.get("dependencies", []),
                    "scaling_factor": config.get("scaling_factor", 1.0),
                    "resource_allocation": config.get("resource_allocation", {"cpu": 1.0, "memory": 1.0}),
                    "status": config.get("status", "active")
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to update service: {response.status_code}")
            
            # In a real system, we would also update container configuration, etc.
            logger.info(f"Service {service_id} updated successfully")
    
    except Exception as e:
        logger.error(f"Error updating service {service_id}: {str(e)}")
        raise

async def execute_update_routing_step(step):
    """Execute a step to update routing configuration"""
    routing_config = step["routing_config"]
    
    try:
        # Create a transition request to the Architectural Plasticity Layer
        async with httpx.AsyncClient() as client:
            # Get current architecture
            current_response = await client.get(f"{APL_SERVICE_URL}/architecture/current")
            if current_response.status_code != 200:
                raise Exception(f"Failed to get current architecture: {current_response.status_code}")
            
            current_arch = current_response.json()
            
            # Create target architecture with updated routing
            target_arch = current_arch.copy()
            target_arch["routing"] = routing_config
            
            # Create transition
            transition_response = await client.post(
                f"{APL_SERVICE_URL}/transitions",
                json={
                    "transition_id": f"routing_update_{int(time.time())}",
                    "from_state": current_arch,
                    "to_state": target_arch
                }
            )
            
            if transition_response.status_code not in [200, 201]:
                raise Exception(f"Failed to create routing transition: {transition_response.status_code}")
            
            transition_data = transition_response.json()
            transition_id = transition_data.get("transition_id")
            
            # Wait for transition to complete
            max_wait_time = 60  # seconds
            wait_time = 0
            while wait_time < max_wait_time:
                status_response = await client.get(f"{APL_SERVICE_URL}/transitions/{transition_id}")
                if status_response.status_code != 200:
                    raise Exception(f"Failed to get transition status: {status_response.status_code}")
                
                status_data = status_response.json()
                if status_data.get("status") == "completed":
                    logger.info(f"Routing update completed successfully")
                    break
                elif status_data.get("status") == "failed":
                    raise Exception(f"Routing transition failed: {status_data.get('error', 'Unknown error')}")
                
                await asyncio.sleep(5)
                wait_time += 5
            
            if wait_time >= max_wait_time:
                raise Exception("Routing transition timed out")
    
    except Exception as e:
        logger.error(f"Error updating routing: {str(e)}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)