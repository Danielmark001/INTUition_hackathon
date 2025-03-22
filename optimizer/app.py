import os
import json
import logging
import time
import random
import numpy as np
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any, Tuple
import httpx
import asyncio
from scipy.optimize import differential_evolution

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-Objective Optimizer")

# Models
class OptimizationGoal(BaseModel):
    name: str
    weight: float = 1.0
    target: Optional[float] = None
    minimize: bool = True

class OptimizationConstraint(BaseModel):
    name: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    target_value: Optional[float] = None

class OptimizationRequest(BaseModel):
    goals: List[OptimizationGoal]
    constraints: List[OptimizationConstraint]
    current_state: Dict[str, Any]
    possible_actions: List[Dict[str, Any]]
    max_iterations: Optional[int] = 100

class OptimizationResult(BaseModel):
    optimization_id: str
    status: str
    iterations: int = 0
    best_solution: Optional[Dict[str, Any]] = None
    all_solutions: Optional[List[Dict[str, Any]]] = None
    metrics: Optional[Dict[str, Any]] = None

class EvaluationRequest(BaseModel):
    state: Dict[str, Any]
    goals: List[OptimizationGoal]
    constraints: List[OptimizationConstraint]

# Environment variables
ANALYZER_URL = os.environ.get("ANALYZER_URL", "http://architecture-analyzer:8060")

# In-memory store
optimizations = {}
cached_evaluations = {}

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Multi-Objective Optimizer")

# API Endpoints
@app.get("/")
async def root():
    return {"status": "Multi-Objective Optimizer operational"}

@app.post("/optimize")
async def optimize(request: OptimizationRequest, background_tasks: BackgroundTasks):
    """Start a new optimization process"""
    optimization_id = f"opt_{int(time.time())}_{random.randint(1000, 9999)}"
    
    # Initialize the optimization
    optimization = OptimizationResult(
        optimization_id=optimization_id,
        status="initializing"
    )
    optimizations[optimization_id] = optimization
    
    # Start optimization in background
    background_tasks.add_task(run_optimization, optimization_id, request)
    
    return {"optimization_id": optimization_id, "status": "started"}

@app.get("/optimize/{optimization_id}")
async def get_optimization_status(optimization_id: str):
    """Get the status of an optimization process"""
    if optimization_id not in optimizations:
        raise HTTPException(status_code=404, detail="Optimization not found")
    
    return optimizations[optimization_id]

@app.post("/evaluate")
async def evaluate_state(request: EvaluationRequest):
    """Evaluate a single state against optimization goals"""
    results = await evaluate_architecture_state(request.state, request.goals, request.constraints)
    return results

# Background tasks
async def run_optimization(optimization_id: str, request: OptimizationRequest):
    """Run the optimization process"""
    optimization = optimizations[optimization_id]
    
    try:
        logger.info(f"Starting optimization {optimization_id}")
        optimization.status = "running"
        
        # Choose optimization strategy based on problem characteristics
        if len(request.possible_actions) <= 10:
            # For small action spaces, exhaustive evaluation
            results = await exhaustive_search(request)
        else:
            # For larger action spaces, evolutionary algorithm
            results = await evolutionary_optimization(request)
        
        # Update optimization with results
        optimization.status = "completed"
        optimization.best_solution = results["best_solution"]
        optimization.all_solutions = results["all_solutions"]
        optimization.iterations = results["iterations"]
        optimization.metrics = results["metrics"]
        
        logger.info(f"Optimization {optimization_id} completed successfully")
    
    except Exception as e:
        logger.error(f"Error in optimization {optimization_id}: {str(e)}")
        optimization.status = "failed"
        optimization.metrics = optimization.metrics or {}
        optimization.metrics["error"] = str(e)

async def exhaustive_search(request: OptimizationRequest):
    """Exhaustive search through all possible actions"""
    logger.info("Using exhaustive search optimization strategy")
    
    start_time = time.time()
    all_solutions = []
    
    # Evaluate the current state as baseline
    baseline_score, baseline_metrics = await evaluate_architecture_state(
        request.current_state, request.goals, request.constraints)
    
    # Try each possible action
    for i, action in enumerate(request.possible_actions):
        # Apply action to current state
        new_state = apply_action_to_state(request.current_state, action)
        
        # Evaluate the new state
        score, metrics = await evaluate_architecture_state(
            new_state, request.goals, request.constraints)
        
        # Add to solutions
        all_solutions.append({
            "action": action,
            "resulting_state": new_state,
            "score": score,
            "metrics": metrics,
            "improvement": score - baseline_score
        })
    
    # Sort solutions by score (lower is better for minimization)
    all_solutions.sort(key=lambda x: x["score"])
    
    # Return results
    return {
        "best_solution": all_solutions[0] if all_solutions else None,
        "all_solutions": all_solutions,
        "iterations": len(request.possible_actions),
        "metrics": {
            "baseline_score": baseline_score,
            "baseline_metrics": baseline_metrics,
            "time_taken": time.time() - start_time,
            "strategy": "exhaustive_search"
        }
    }

async def evolutionary_optimization(request: OptimizationRequest):
    """Use evolutionary algorithm for optimization"""
    logger.info("Using evolutionary optimization strategy")
    
    start_time = time.time()
    
    # Map actions to integers for the optimizer
    action_mapping = {i: action for i, action in enumerate(request.possible_actions)}
    
    # Define objective function for the optimizer
    async def objective_function(x):
        # Round the continuous variables to integers
        action_indices = np.round(x).astype(int)
        
        # Apply selected actions to current state
        state = request.current_state.copy()
        selected_actions = []
        
        for idx in action_indices:
            if 0 <= idx < len(request.possible_actions):
                action = request.possible_actions[idx]
                state = apply_action_to_state(state, action)
                selected_actions.append(action)
        
        # Evaluate the resulting state
        score, _ = await evaluate_architecture_state(
            state, request.goals, request.constraints)
        
        return score
    
    # Define bounds for the optimizer (one dimension per action)
    bounds = [(0, len(request.possible_actions) - 1)] * min(5, len(request.possible_actions))
    
    # Run the optimizer
    all_solutions = []
    iterations = 0
    
    # Wrapper for the objective function that records solutions
    async def wrapper_objective(x):
        nonlocal iterations
        iterations += 1
        return await objective_function(x)
    
    # Execute optimization
    population_size = min(20, len(request.possible_actions) * 4)
    max_iterations = min(request.max_iterations, 100)
    
    # Use a simpler approach for demo purposes
    best_score = float('inf')
    best_solution = None
    best_state = None
    
    # Sample random combinations of actions
    for _ in range(max_iterations):
        # Select a random number of actions
        num_actions = random.randint(1, min(5, len(request.possible_actions)))
        action_indices = random.sample(range(len(request.possible_actions)), num_actions)
        
        # Apply actions to state
        state = request.current_state.copy()
        applied_actions = []
        
        for idx in action_indices:
            action = request.possible_actions[idx]
            state = apply_action_to_state(state, action)
            applied_actions.append(action)
        
        # Evaluate
        score, metrics = await evaluate_architecture_state(
            state, request.goals, request.constraints)
        
        solution = {
            "actions": applied_actions,
            "resulting_state": state,
            "score": score,
            "metrics": metrics
        }
        
        all_solutions.append(solution)
        
        if score < best_score:
            best_score = score
            best_solution = solution
    
    # Evaluate baseline for comparison
    baseline_score, baseline_metrics = await evaluate_architecture_state(
        request.current_state, request.goals, request.constraints)
    
    # Sort solutions by score
    all_solutions.sort(key=lambda x: x["score"])
    
    return {
        "best_solution": best_solution,
        "all_solutions": all_solutions,
        "iterations": iterations,
        "metrics": {
            "baseline_score": baseline_score,
            "baseline_metrics": baseline_metrics,
            "time_taken": time.time() - start_time,
            "strategy": "evolutionary_optimization"
        }
    }

async def evaluate_architecture_state(
    state: Dict[str, Any], 
    goals: List[OptimizationGoal], 
    constraints: List[OptimizationConstraint]
) -> Tuple[float, Dict[str, Any]]:
    """Evaluate an architecture state against goals and constraints"""
    
    # Create cache key
    cache_key = hash(str(state) + str([g.dict() for g in goals]) + str([c.dict() for c in constraints]))
    if cache_key in cached_evaluations:
        return cached_evaluations[cache_key]
    
    try:
        # Get architecture analysis from the analyzer service
        metrics = await analyze_architecture(state)
        
        # Calculate goal scores
        goal_scores = {}
        total_score = 0
        total_weight = 0
        
        for goal in goals:
            score = calculate_goal_score(goal, metrics)
            weighted_score = score * goal.weight
            
            goal_scores[goal.name] = {
                "raw_score": score,
                "weighted_score": weighted_score,
                "weight": goal.weight
            }
            
            total_score += weighted_score
            total_weight += goal.weight
        
        # Normalize the total score
        if total_weight > 0:
            normalized_score = total_score / total_weight
        else:
            normalized_score = 0
        
        # Apply constraint penalties
        constraint_violations = []
        for constraint in constraints:
            violation = check_constraint_violation(constraint, metrics)
            if violation:
                constraint_violations.append({
                    "constraint": constraint.name,
                    "violation": violation,
                    "penalty": 100 * violation  # Severe penalty for constraint violations
                })
                normalized_score += 100 * violation
        
        # Create result
        evaluation_result = {
            "score": normalized_score,
            "goal_scores": goal_scores,
            "constraint_violations": constraint_violations,
            "raw_metrics": metrics
        }
        
        # Cache the result
        cached_evaluations[cache_key] = (normalized_score, evaluation_result)
        
        return normalized_score, evaluation_result
    
    except Exception as e:
        logger.error(f"Error evaluating architecture state: {str(e)}")
        # Return a high score (bad) for failed evaluations
        return 1000, {"error": str(e)}

def apply_action_to_state(state: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
    """Apply an action to the current state to produce a new state"""
    new_state = state.copy()
    
    action_type = action.get("type")
    
    if action_type == "merge_services":
        # Merge two services into one
        services_to_merge = action.get("services", [])
        if len(services_to_merge) >= 2 and "services" in new_state:
            # Create a new service with combined properties
            merged_service = {}
            for service_id in services_to_merge:
                if service_id in new_state["services"]:
                    service = new_state["services"][service_id]
                    for key, value in service.items():
                        if key not in merged_service:
                            merged_service[key] = value
                        elif isinstance(value, list):
                            # Combine lists (e.g., capabilities)
                            if isinstance(merged_service[key], list):
                                merged_service[key].extend(value)
                        elif isinstance(value, dict):
                            # Combine dictionaries (e.g., resource allocations)
                            if isinstance(merged_service[key], dict):
                                for subkey, subvalue in value.items():
                                    if subkey in merged_service[key]:
                                        merged_service[key][subkey] += subvalue
                                    else:
                                        merged_service[key][subkey] = subvalue
            
            # Add the merged service
            new_service_id = f"merged_{'_'.join(services_to_merge)}"
            new_state["services"][new_service_id] = merged_service
            
            # Remove the original services
            for service_id in services_to_merge:
                if service_id in new_state["services"]:
                    del new_state["services"][service_id]
    
    elif action_type == "split_service":
        # Split a service into two
        service_id = action.get("service_id")
        split_config = action.get("split_config", {})
        
        if service_id and "services" in new_state and service_id in new_state["services"]:
            original_service = new_state["services"][service_id]
            
            # Create two new services based on the split configuration
            service1 = {}
            service2 = {}
            
            # Split capabilities
            if "capabilities" in original_service:
                capabilities = original_service["capabilities"]
                split_point = len(capabilities) // 2
                
                if "capabilities_split" in split_config:
                    service1["capabilities"] = split_config["capabilities_split"].get("service1", [])
                    service2["capabilities"] = split_config["capabilities_split"].get("service2", [])
                else:
                    service1["capabilities"] = capabilities[:split_point]
                    service2["capabilities"] = capabilities[split_point:]
            
            # Split resource allocation
            if "resource_allocation" in original_service:
                resources = original_service["resource_allocation"]
                
                if "resource_split" in split_config:
                    ratio = split_config["resource_split"].get("ratio", 0.5)
                    service1["resource_allocation"] = {k: v * ratio for k, v in resources.items()}
                    service2["resource_allocation"] = {k: v * (1 - ratio) for k, v in resources.items()}
                else:
                    service1["resource_allocation"] = {k: v * 0.5 for k, v in resources.items()}
                    service2["resource_allocation"] = {k: v * 0.5 for k, v in resources.items()}
            
            # Add the new services
            new_state["services"][f"{service_id}_1"] = service1
            new_state["services"][f"{service_id}_2"] = service2
            
            # Remove the original service
            del new_state["services"][service_id]
    
    elif action_type == "adjust_resources":
        # Adjust resources for a service
        service_id = action.get("service_id")
        adjustments = action.get("adjustments", {})
        
        if service_id and "services" in new_state and service_id in new_state["services"]:
            service = new_state["services"][service_id]
            
            if "resource_allocation" in service:
                for resource, factor in adjustments.items():
                    if resource in service["resource_allocation"]:
                        service["resource_allocation"][resource] *= factor
    
    elif action_type == "add_capability":
        # Add a capability to a service
        service_id = action.get("service_id")
        capability = action.get("capability")
        
        if service_id and capability and "services" in new_state and service_id in new_state["services"]:
            service = new_state["services"][service_id]
            
            if "capabilities" in service:
                if capability not in service["capabilities"]:
                    service["capabilities"].append(capability)
            else:
                service["capabilities"] = [capability]
    
    elif action_type == "remove_capability":
        # Remove a capability from a service
        service_id = action.get("service_id")
        capability = action.get("capability")
        
        if service_id and capability and "services" in new_state and service_id in new_state["services"]:
            service = new_state["services"][service_id]
            
            if "capabilities" in service and capability in service["capabilities"]:
                service["capabilities"].remove(capability)
    
    elif action_type == "custom":
        # Apply a custom transformation function
        if "apply_func" in action and callable(action["apply_func"]):
            new_state = action["apply_func"](new_state)
    
    return new_state

async def analyze_architecture(state: Dict[str, Any]) -> Dict[str, Any]:
    """Get architecture analysis metrics from the analyzer service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ANALYZER_URL}/analyze",
                json={"architecture": state}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Architecture analyzer returned error: {response.status_code}")
                # Fallback to simplified local analysis
                return perform_local_analysis(state)
    
    except Exception as e:
        logger.error(f"Error communicating with architecture analyzer: {str(e)}")
        # Fallback to simplified local analysis
        return perform_local_analysis(state)

def perform_local_analysis(state: Dict[str, Any]) -> Dict[str, Any]:
    """Perform simplified local analysis when the analyzer service is unavailable"""
    metrics = {}
    
    # Basic service metrics
    if "services" in state:
        services = state["services"]
        metrics["service_count"] = len(services)
        
        # Calculate total resources
        total_cpu = 0
        total_memory = 0
        for service_id, service in services.items():
            if "resource_allocation" in service:
                resources = service["resource_allocation"]
                total_cpu += resources.get("cpu", 0)
                total_memory += resources.get("memory", 0)
        
        metrics["total_cpu"] = total_cpu
        metrics["total_memory"] = total_memory
        
        # Calculate average service complexity
        total_capabilities = 0
        for service_id, service in services.items():
            total_capabilities += len(service.get("capabilities", []))
        
        if len(services) > 0:
            metrics["avg_capabilities_per_service"] = total_capabilities / len(services)
        else:
            metrics["avg_capabilities_per_service"] = 0
    
    # Estimate coupling (simplified)
    coupling_score = 0
    if "services" in state:
        # The more services, the higher potential coupling
        # This is a very simplified heuristic
        service_count = len(state["services"])
        if service_count > 1:
            coupling_score = (service_count - 1) * 0.1  # Crude approximation
    
    metrics["estimated_coupling"] = coupling_score
    
    # Estimate resilience (simplified)
    resilience_score = 0
    if "services" in state and len(state["services"]) > 0:
        # The more distributed the system, the more resilient (simplified assumption)
        resilience_score = min(1.0, len(state["services"]) * 0.2)
    
    metrics["estimated_resilience"] = resilience_score
    
    return metrics

def calculate_goal_score(goal: OptimizationGoal, metrics: Dict[str, Any]) -> float:
    """Calculate a score for a single optimization goal"""
    metric_value = metrics.get(goal.name)
    
    if metric_value is None:
        # Metric not available, neutral score
        return 0.5
    
    if goal.target is not None:
        # Target-based scoring (distance from target)
        distance = abs(metric_value - goal.target)
        
        # Normalize to 0-1 range (closer to 0 is better)
        # The scale factor determines how quickly the score increases with distance
        scale_factor = goal.target * 0.2 if goal.target != 0 else 0.2
        score = min(1.0, distance / scale_factor)
    else:
        # Minimize or maximize
        if goal.minimize:
            # For minimization, normalize higher values to be closer to 1 (worse)
            # Assume reasonable bounds based on the metric type
            if goal.name in ["total_cpu", "total_memory"]:
                # For resource metrics, normalize against a maximum expected value
                max_expected = 10.0  # Arbitrary maximum for demo purposes
                score = min(1.0, metric_value / max_expected)
            elif goal.name == "service_count":
                # For service count, normalize against a maximum expected count
                max_expected = 20  # Arbitrary maximum for demo purposes
                score = min(1.0, metric_value / max_expected)
            elif goal.name == "estimated_coupling":
                # Coupling is already normalized to 0-1
                score = metric_value
            else:
                # Default normalization for unknown metrics
                score = min(1.0, metric_value)
        else:
            # For maximization, normalize higher values to be closer to 0 (better)
            if goal.name == "estimated_resilience":
                # Resilience is already normalized to 0-1, invert for scoring
                score = 1.0 - metric_value
            else:
                # Default normalization for unknown metrics
                # Assume 1.0 is a good target for maximization
                score = max(0.0, 1.0 - metric_value)
    
    return score

def check_constraint_violation(constraint: OptimizationConstraint, metrics: Dict[str, Any]) -> float:
    """Check if a constraint is violated and return the violation amount"""
    metric_value = metrics.get(constraint.name)
    
    if metric_value is None:
        # Metric not available, no violation
        return 0.0
    
    violation = 0.0
    
    if constraint.min_value is not None and metric_value < constraint.min_value:
        # Violation of minimum constraint
        violation = (constraint.min_value - metric_value) / constraint.min_value
    
    if constraint.max_value is not None and metric_value > constraint.max_value:
        # Violation of maximum constraint
        violation = (metric_value - constraint.max_value) / constraint.max_value
    
    if constraint.target_value is not None:
        # For target constraints, calculate normalized distance
        distance = abs(metric_value - constraint.target_value)
        # Normalize distance as a percentage of target
        if constraint.target_value != 0:
            violation = distance / abs(constraint.target_value)
        else:
            violation = distance
        
        # Only count as violation if distance is significant
        if violation < 0.1:  # 10% tolerance
            violation = 0.0
    
    return violation

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8030)