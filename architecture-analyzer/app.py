import os
import json
import logging
import time
import math
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import httpx
import networkx as nx
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Architecture Analyzer")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ArchitectureState(BaseModel):
    services: Dict[str, Any]
    routing: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class AnalysisRequest(BaseModel):
    architecture: ArchitectureState
    telemetry_window: Optional[int] = 3600  # Default: 1 hour in seconds

class ServiceDependencyAnalysis(BaseModel):
    service_id: str
    direct_dependencies: List[str]
    reverse_dependencies: List[str]
    coupling_scores: Dict[str, float]
    criticality_score: float

# API Endpoints
@app.get("/")
async def root():
    return {"status": "Architecture Analyzer operational"}

@app.post("/analyze")
async def analyze_architecture(request: AnalysisRequest):
    """Analyze an architecture state and return metrics"""
    logger.info("Analyzing architecture")
    
    # Start with basic metrics
    metrics = calculate_basic_metrics(request.architecture)
    
    # Add service coupling analysis
    coupling_metrics = analyze_service_coupling(request.architecture)
    metrics.update(coupling_metrics)
    
    # Add resilience analysis
    resilience_metrics = analyze_resilience(request.architecture)
    metrics.update(resilience_metrics)
    
    # Add performance efficiency analysis
    performance_metrics = analyze_performance_efficiency(request.architecture)
    metrics.update(performance_metrics)
    
    # Add complexity analysis
    complexity_metrics = analyze_complexity(request.architecture)
    metrics.update(complexity_metrics)
    
    # Add operational metrics if we have access to telemetry
    try:
        operational_metrics = await analyze_operational_metrics(
            request.architecture, request.telemetry_window)
        metrics.update(operational_metrics)
    except Exception as e:
        logger.error(f"Error analyzing operational metrics: {str(e)}")
        metrics["operational_metrics_error"] = str(e)
    
    return metrics

@app.get("/dependencies/{service_id}")
async def analyze_service_dependencies(service_id: str, architecture: ArchitectureState):
    """Analyze dependencies for a specific service"""
    if service_id not in architecture.services:
        raise HTTPException(status_code=404, detail="Service not found in architecture")
    
    # Build dependency graph
    graph = build_dependency_graph(architecture)
    
    # Get direct dependencies
    direct_dependencies = []
    if service_id in graph:
        direct_dependencies = list(graph.successors(service_id))
    
    # Get reverse dependencies (services that depend on this one)
    reverse_dependencies = []
    if service_id in graph:
        reverse_dependencies = list(graph.predecessors(service_id))
    
    # Calculate coupling scores
    coupling_scores = {}
    for other_service in architecture.services:
        if other_service != service_id:
            coupling_scores[other_service] = calculate_service_coupling_score(
                service_id, other_service, architecture)
    
    # Calculate criticality score
    criticality_score = calculate_service_criticality(service_id, graph)
    
    return ServiceDependencyAnalysis(
        service_id=service_id,
        direct_dependencies=direct_dependencies,
        reverse_dependencies=reverse_dependencies,
        coupling_scores=coupling_scores,
        criticality_score=criticality_score
    )

@app.post("/hotspots")
async def identify_architecture_hotspots(request: AnalysisRequest):
    """Identify architectural hotspots (areas that need attention)"""
    # Analyze architecture
    metrics = await analyze_architecture(request)
    
    # Identify hotspots
    hotspots = []
    
    # Check for highly coupled services
    if "service_coupling" in metrics:
        for pair, score in metrics["service_coupling"].items():
            if score > 0.7:  # High coupling threshold
                services = pair.split("-")
                hotspots.append({
                    "type": "high_coupling",
                    "services": services,
                    "score": score,
                    "description": f"High coupling between {services[0]} and {services[1]}",
                    "recommendation": "Consider merging services or refactoring interfaces"
                })
    
    # Check for low resilience
    if "resilience_score" in metrics and metrics["resilience_score"] < 0.4:
        hotspots.append({
            "type": "low_resilience",
            "score": metrics["resilience_score"],
            "description": "System has low overall resilience",
            "recommendation": "Improve fault tolerance, add redundancy, or implement circuit breakers"
        })
    
    # Check for bottleneck services
    if "service_criticality" in metrics:
        for service_id, score in metrics["service_criticality"].items():
            if score > 0.8:  # High criticality threshold
                hotspots.append({
                    "type": "critical_service",
                    "service_id": service_id,
                    "score": score,
                    "description": f"Service {service_id} is a critical bottleneck",
                    "recommendation": "Reduce dependencies on this service or improve its resilience"
                })
    
    # Check for high complexity
    if "complexity_score" in metrics and metrics["complexity_score"] > 0.7:
        hotspots.append({
            "type": "high_complexity",
            "score": metrics["complexity_score"],
            "description": "System has high architectural complexity",
            "recommendation": "Simplify architecture, consolidate services, or improve organization"
        })
    
    # Check for uneven resource allocation
    if "resource_distribution" in metrics and metrics["resource_distribution"] > 0.6:
        hotspots.append({
            "type": "uneven_resources",
            "score": metrics["resource_distribution"],
            "description": "Resources are unevenly distributed across services",
            "recommendation": "Rebalance resources based on actual service demands"
        })
    
    # Check operational issues if available
    if "service_error_rates" in metrics:
        for service_id, error_rate in metrics["service_error_rates"].items():
            if error_rate > 0.05:  # Error rate threshold (5%)
                hotspots.append({
                    "type": "high_error_rate",
                    "service_id": service_id,
                    "score": error_rate,
                    "description": f"Service {service_id} has high error rate ({error_rate*100:.1f}%)",
                    "recommendation": "Investigate errors and improve reliability"
                })
    
    return {
        "hotspots": hotspots,
        "hotspot_count": len(hotspots),
        "metrics_snapshot": metrics
    }

@app.post("/compare")
async def compare_architectures(current: ArchitectureState, proposed: ArchitectureState):
    """Compare two architecture states and highlight differences"""
    # Analyze both architectures
    current_metrics = calculate_basic_metrics(current)
    current_metrics.update(analyze_service_coupling(current))
    current_metrics.update(analyze_resilience(current))
    current_metrics.update(analyze_performance_efficiency(current))
    current_metrics.update(analyze_complexity(current))
    
    proposed_metrics = calculate_basic_metrics(proposed)
    proposed_metrics.update(analyze_service_coupling(proposed))
    proposed_metrics.update(analyze_resilience(proposed))
    proposed_metrics.update(analyze_performance_efficiency(proposed))
    proposed_metrics.update(analyze_complexity(proposed))
    
    # Compare service structure
    service_changes = compare_services(current, proposed)
    
    # Compare metrics
    metric_changes = {}
    for key in set(current_metrics.keys()) | set(proposed_metrics.keys()):
        if key in current_metrics and key in proposed_metrics:
            # Both have this metric, calculate percentage change
            if isinstance(current_metrics[key], (int, float)) and isinstance(proposed_metrics[key], (int, float)):
                if current_metrics[key] != 0:
                    change_pct = (proposed_metrics[key] - current_metrics[key]) / abs(current_metrics[key]) * 100
                else:
                    change_pct = float('inf') if proposed_metrics[key] != 0 else 0
                
                metric_changes[key] = {
                    "from": current_metrics[key],
                    "to": proposed_metrics[key],
                    "change": proposed_metrics[key] - current_metrics[key],
                    "change_pct": change_pct
                }
            elif isinstance(current_metrics[key], dict) and isinstance(proposed_metrics[key], dict):
                # For dictionary metrics, we'll show a summary
                metric_changes[key] = {
                    "keys_added": list(set(proposed_metrics[key].keys()) - set(current_metrics[key].keys())),
                    "keys_removed": list(set(current_metrics[key].keys()) - set(proposed_metrics[key].keys())),
                    "keys_changed": [k for k in set(current_metrics[key].keys()) & set(proposed_metrics[key].keys())
                                    if current_metrics[key][k] != proposed_metrics[key][k]]
                }
        elif key in current_metrics:
            metric_changes[key] = {"status": "removed", "old_value": current_metrics[key]}
        else:
            metric_changes[key] = {"status": "added", "new_value": proposed_metrics[key]}
    
    # Generate improvement/regression analysis
    improvements = []
    regressions = []
    
    # Check resilience
    if "resilience_score" in metric_changes:
        change = metric_changes["resilience_score"]["change"]
        if change > 0.05:  # 5% improvement threshold
            improvements.append({
                "metric": "resilience_score",
                "change": change,
                "description": "Improved system resilience"
            })
        elif change < -0.05:  # 5% regression threshold
            regressions.append({
                "metric": "resilience_score",
                "change": change,
                "description": "Decreased system resilience"
            })
    
    # Check complexity
    if "complexity_score" in metric_changes:
        change = metric_changes["complexity_score"]["change"]
        if change < -0.05:  # Lower complexity is better
            improvements.append({
                "metric": "complexity_score",
                "change": change,
                "description": "Reduced system complexity"
            })
        elif change > 0.05:
            regressions.append({
                "metric": "complexity_score",
                "change": change,
                "description": "Increased system complexity"
            })
    
    # Check resource efficiency
    if "resource_efficiency" in metric_changes:
        change = metric_changes["resource_efficiency"]["change"]
        if change > 0.05:
            improvements.append({
                "metric": "resource_efficiency",
                "change": change,
                "description": "Improved resource efficiency"
            })
        elif change < -0.05:
            regressions.append({
                "metric": "resource_efficiency",
                "change": change,
                "description": "Decreased resource efficiency"
            })
    
    # Check service coupling
    if "avg_service_coupling" in metric_changes:
        change = metric_changes["avg_service_coupling"]["change"]
        if change < -0.05:  # Lower coupling is better
            improvements.append({
                "metric": "avg_service_coupling",
                "change": change,
                "description": "Reduced service coupling"
            })
        elif change > 0.05:
            regressions.append({
                "metric": "avg_service_coupling",
                "change": change,
                "description": "Increased service coupling"
            })
    
    return {
        "service_changes": service_changes,
        "metric_changes": metric_changes,
        "improvements": improvements,
        "regressions": regressions,
        "current_metrics": current_metrics,
        "proposed_metrics": proposed_metrics
    }

# Analysis functions
def calculate_basic_metrics(architecture: ArchitectureState) -> Dict[str, Any]:
    """Calculate basic metrics about the architecture"""
    services = architecture.services or {}
    
    # Count services
    service_count = len(services)
    
    # Calculate total resources
    total_cpu = 0
    total_memory = 0
    for service_id, service in services.items():
        if "resource_allocation" in service:
            resources = service["resource_allocation"]
            total_cpu += resources.get("cpu", 0)
            total_memory += resources.get("memory", 0)
    
    # Count total capabilities across services
    all_capabilities = set()
    capability_counts = {}
    for service_id, service in services.items():
        caps = service.get("capabilities", [])
        all_capabilities.update(caps)
        for cap in caps:
            capability_counts[cap] = capability_counts.get(cap, 0) + 1
    
    # Identify duplicate capabilities (implemented by multiple services)
    duplicate_capabilities = {cap: count for cap, count in capability_counts.items() if count > 1}
    
    return {
        "service_count": service_count,
        "total_cpu": total_cpu,
        "total_memory": total_memory,
        "capability_count": len(all_capabilities),
        "duplicate_capabilities": duplicate_capabilities,
        "duplicate_capability_count": len(duplicate_capabilities)
    }

def analyze_service_coupling(architecture: ArchitectureState) -> Dict[str, Any]:
    """Analyze service coupling in the architecture"""
    services = architecture.services or {}
    
    # Build dependency graph
    graph = build_dependency_graph(architecture)
    
    # Calculate coupling for each service pair
    coupling_scores = {}
    for service1 in services:
        for service2 in services:
            if service1 < service2:  # To avoid duplicate pairs
                score = calculate_service_coupling_score(service1, service2, architecture)
                if score > 0:  # Only include non-zero coupling
                    coupling_scores[f"{service1}-{service2}"] = score
    
    # Calculate criticality scores for each service
    criticality_scores = {}
    for service_id in services:
        criticality_scores[service_id] = calculate_service_criticality(service_id, graph)
    
    # Calculate average coupling
    avg_coupling = sum(coupling_scores.values()) / len(coupling_scores) if coupling_scores else 0
    
    # Identify highly coupled pairs
    high_coupling_threshold = 0.7
    highly_coupled = {pair: score for pair, score in coupling_scores.items() if score >= high_coupling_threshold}
    
    return {
        "service_coupling": coupling_scores,
        "avg_service_coupling": avg_coupling,
        "high_coupling_pairs": highly_coupled,
        "high_coupling_pair_count": len(highly_coupled),
        "service_criticality": criticality_scores
    }

def analyze_resilience(architecture: ArchitectureState) -> Dict[str, Any]:
    """Analyze system resilience characteristics"""
    services = architecture.services or {}
    
    # Build dependency graph
    graph = build_dependency_graph(architecture)
    
    # Calculate single points of failure
    spof = identify_single_points_of_failure(graph)
    
    # Calculate dependency depth (longer chains = less resilient)
    max_path_length = 0
    if graph.nodes():
        try:
            # Find longest shortest path
            for source in graph.nodes():
                for target in graph.nodes():
                    if source != target and nx.has_path(graph, source, target):
                        path_length = len(nx.shortest_path(graph, source, target)) - 1
                        max_path_length = max(max_path_length, path_length)
        except Exception as e:
            logger.error(f"Error calculating path lengths: {str(e)}")
    
    # Normalize max path length to a resilience score
    path_length_factor = 1.0 / (1 + 0.5 * max_path_length) if max_path_length > 0 else 1.0
    
    # Calculate redundancy score
    duplicate_capabilities = 0
    total_capabilities = 0
    capability_services = {}
    
    for service_id, service in services.items():
        for cap in service.get("capabilities", []):
            if cap not in capability_services:
                capability_services[cap] = []
            capability_services[cap].append(service_id)
            total_capabilities += 1
    
    for cap, service_list in capability_services.items():
        if len(service_list) > 1:
            duplicate_capabilities += len(service_list) - 1
    
    redundancy_score = duplicate_capabilities / total_capabilities if total_capabilities > 0 else 0
    
    # Calculate overall resilience score (0-1, higher is better)
    spof_factor = 1.0 - (len(spof) / len(services) if services else 0)
    resilience_score = (spof_factor * 0.5 + path_length_factor * 0.3 + redundancy_score * 0.2)
    
    return {
        "single_points_of_failure": spof,
        "spof_count": len(spof),
        "max_dependency_depth": max_path_length,
        "capability_redundancy": redundancy_score,
        "resilience_score": resilience_score
    }

def analyze_performance_efficiency(architecture: ArchitectureState) -> Dict[str, Any]:
    """Analyze performance and efficiency characteristics"""
    services = architecture.services or {}
    
    # Calculate resource distribution across services
    cpu_allocations = []
    memory_allocations = []
    
    for service_id, service in services.items():
        if "resource_allocation" in service:
            resources = service["resource_allocation"]
            cpu_allocations.append(resources.get("cpu", 0))
            memory_allocations.append(resources.get("memory", 0))
    
    # Calculate Gini coefficient for resource distribution (0=equal, 1=unequal)
    cpu_gini = calculate_gini_coefficient(cpu_allocations) if cpu_allocations else 0
    memory_gini = calculate_gini_coefficient(memory_allocations) if memory_allocations else 0
    
    # Calculate average resources per capability
    total_capabilities = 0
    for service_id, service in services.items():
        total_capabilities += len(service.get("capabilities", []))
    
    cpu_per_capability = sum(cpu_allocations) / total_capabilities if total_capabilities > 0 else 0
    memory_per_capability = sum(memory_allocations) / total_capabilities if total_capabilities > 0 else 0
    
    # Calculate resource efficiency score (lower is better)
    total_cpu = sum(cpu_allocations)
    total_memory = sum(memory_allocations)
    
    # Assuming ideal resource allocation based on capability count
    ideal_cpu_per_capability = 0.5  # Arbitrary baseline for demo
    ideal_memory_per_capability = 0.5  # Arbitrary baseline for demo
    
    cpu_efficiency = ideal_cpu_per_capability / cpu_per_capability if cpu_per_capability > 0 else 0
    memory_efficiency = ideal_memory_per_capability / memory_per_capability if memory_per_capability > 0 else 0
    
    # Combined efficiency score (0-1, higher is better)
    efficiency_score = (cpu_efficiency * 0.5 + memory_efficiency * 0.5)
    
    return {
        "resource_distribution": (cpu_gini + memory_gini) / 2,
        "cpu_distribution_gini": cpu_gini,
        "memory_distribution_gini": memory_gini,
        "cpu_per_capability": cpu_per_capability,
        "memory_per_capability": memory_per_capability,
        "resource_efficiency": efficiency_score
    }

def analyze_complexity(architecture: ArchitectureState) -> Dict[str, Any]:
    """Analyze architectural complexity"""
    services = architecture.services or {}
    
    # Build dependency graph
    graph = build_dependency_graph(architecture)
    
    # Calculate graph density (0-1, higher means more interconnected)
    density = nx.density(graph) if graph.nodes() else 0
    
    # Calculate average connections per service
    total_connections = sum(len(list(graph.successors(n))) + len(list(graph.predecessors(n))) 
                          for n in graph.nodes()) if graph.nodes() else 0
    avg_connections = total_connections / (2 * len(graph.nodes())) if graph.nodes() else 0
    
    # Calculate capability dispersion (how spread out capabilities are)
    capability_dispersion = calculate_capability_dispersion(architecture)
    
    # Calculate normalized entropy of the system
    try:
        # Use degree distribution as a measure of system entropy
        degrees = [graph.degree(n) for n in graph.nodes()]
        entropy = calculate_entropy(degrees) if degrees else 0
        # Normalize by maximum possible entropy
        max_entropy = math.log(len(graph.nodes())) if len(graph.nodes()) > 1 else 1
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
    except Exception as e:
        logger.error(f"Error calculating entropy: {str(e)}")
        normalized_entropy = 0
    
    # Combined complexity score (0-1, higher is more complex)
    complexity_score = (density * 0.3 + avg_connections * 0.1 + 
                       capability_dispersion * 0.3 + normalized_entropy * 0.3)
    
    return {
        "graph_density": density,
        "avg_connections_per_service": avg_connections,
        "capability_dispersion": capability_dispersion,
        "normalized_entropy": normalized_entropy,
        "complexity_score": complexity_score
    }

async def analyze_operational_metrics(architecture: ArchitectureState, time_window: int) -> Dict[str, Any]:
    """Analyze operational metrics from telemetry"""
    services = architecture.services or {}
    
    # This would connect to telemetry service in a real implementation
    # For demo purposes, we'll generate synthetic metrics
    
    # In a real system, we would fetch telemetry:
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(
    #         "http://telemetry:8050/data/query",
    #         json={
    #             "service_ids": list(services.keys()),
    #             "start_time": time.time() - time_window,
    #             "end_time": time.time(),
    #             "metrics": ["latency", "error_count", "request_count"]
    #         }
    #     )
    #     telemetry_data = response.json()
    
    # Generate synthetic telemetry for demo
    telemetry_data = generate_synthetic_telemetry(services)
    
    # Calculate operational metrics
    service_latencies = {}
    service_error_rates = {}
    service_throughputs = {}
    
    for service_id, metrics in telemetry_data.items():
        service_latencies[service_id] = metrics["avg_latency"]
        service_error_rates[service_id] = metrics["error_rate"]
        service_throughputs[service_id] = metrics["throughput"]
    
    # Calculate critical path latency (if we have routing info)
    critical_path_latency = 0
    critical_path = []
    
    if architecture.routing and "paths" in architecture.routing:
        # Find the path with highest cumulative latency
        max_latency = 0
        for path_name, path_info in architecture.routing["paths"].items():
            if "services" in path_info:
                path_services = path_info["services"]
                path_latency = sum(service_latencies.get(s, 0) for s in path_services)
                if path_latency > max_latency:
                    max_latency = path_latency
                    critical_path = path_services
        
        critical_path_latency = max_latency
    
    # Calculate system throughput and error rates
    total_requests = sum(service_throughputs.values())
    weighted_error_rate = sum(rate * service_throughputs[s_id] for s_id, rate in service_error_rates.items()) / total_requests if total_requests > 0 else 0
    
    return {
        "service_latencies": service_latencies,
        "service_error_rates": service_error_rates,
        "service_throughputs": service_throughputs,
        "critical_path": critical_path,
        "critical_path_latency": critical_path_latency,
        "system_throughput": total_requests,
        "system_error_rate": weighted_error_rate
    }

# Helper functions
def build_dependency_graph(architecture: ArchitectureState) -> nx.DiGraph:
    """Build a directed graph representing service dependencies"""
    graph = nx.DiGraph()
    
    # Add all services as nodes
    for service_id in architecture.services:
        graph.add_node(service_id)
    
    # Add dependencies as edges
    for service_id, service in architecture.services.items():
        if "dependencies" in service:
            for dependency in service["dependencies"]:
                if dependency in architecture.services:
                    graph.add_edge(service_id, dependency)
    
    # Add routing-based dependencies if available
    if architecture.routing and "paths" in architecture.routing:
        for path_name, path_info in architecture.routing["paths"].items():
            if "services" in path_info:
                # Create edges for sequential services in the path
                services = path_info["services"]
                for i in range(len(services) - 1):
                    if services[i] in architecture.services and services[i+1] in architecture.services:
                        graph.add_edge(services[i], services[i+1])
    
    return graph

def calculate_service_coupling_score(service1: str, service2: str, architecture: ArchitectureState) -> float:
    """Calculate coupling score between two services (0-1, higher means more coupled)"""
    service1_data = architecture.services.get(service1, {})
    service2_data = architecture.services.get(service2, {})
    
    # Start with dependency-based coupling
    direct_dependency = 0
    if "dependencies" in service1_data and service2 in service1_data["dependencies"]:
        direct_dependency = 0.5
    if "dependencies" in service2_data and service1 in service2_data["dependencies"]:
        direct_dependency = max(direct_dependency, 0.5)
    
    # Check capability overlap
    service1_caps = set(service1_data.get("capabilities", []))
    service2_caps = set(service2_data.get("capabilities", []))
    
    capability_overlap = 0
    if service1_caps and service2_caps:
        overlap = len(service1_caps.intersection(service2_caps))
        union = len(service1_caps.union(service2_caps))
        capability_overlap = overlap / union if union > 0 else 0
    
    # Check routing-based coupling
    routing_coupling = 0
    if architecture.routing and "paths" in architecture.routing:
        # Count how many paths include both services sequentially
        path_count = 0
        total_paths = len(architecture.routing["paths"])
        
        for path_name, path_info in architecture.routing["paths"].items():
            if "services" in path_info:
                services = path_info["services"]
                
                # Check if both services are in the path
                if service1 in services and service2 in services:
                    # Check if they are adjacent
                    for i in range(len(services) - 1):
                        if (services[i] == service1 and services[i+1] == service2) or \
                           (services[i] == service2 and services[i+1] == service1):
                            path_count += 1
                            break
        
        routing_coupling = path_count / total_paths if total_paths > 0 else 0
    
    # Combined coupling score (weighted average)
    return direct_dependency * 0.5 + capability_overlap * 0.3 + routing_coupling * 0.2

def calculate_service_criticality(service_id: str, graph: nx.DiGraph) -> float:
    """Calculate criticality score for a service (0-1, higher means more critical)"""
    if not graph.has_node(service_id):
        return 0
    
    # Calculate betweenness centrality (how often this service is on the shortest path between others)
    try:
        betweenness = nx.betweenness_centrality(graph)
        service_betweenness = betweenness.get(service_id, 0)
    except Exception as e:
        logger.error(f"Error calculating betweenness: {str(e)}")
        service_betweenness = 0
    
    # Count incoming and outgoing dependencies
    in_degree = len(list(graph.predecessors(service_id)))
    out_degree = len(list(graph.successors(service_id)))
    
    # Total number of services
    n_services = len(graph.nodes())
    
    # Normalize degrees
    normalized_in = in_degree / (n_services - 1) if n_services > 1 else 0
    normalized_out = out_degree / (n_services - 1) if n_services > 1 else 0
    
    # Combined criticality score
    return service_betweenness * 0.5 + normalized_in * 0.3 + normalized_out * 0.2

def identify_single_points_of_failure(graph: nx.DiGraph) -> List[str]:
    """Identify services that are single points of failure"""
    spof = []
    
    # Check for articulation points (nodes that would disconnect the graph if removed)
    try:
        # Convert to undirected for articulation points
        undirected = graph.to_undirected()
        articulation_points = list(nx.articulation_points(undirected))
        spof.extend(articulation_points)
    except Exception as e:
        logger.error(f"Error calculating articulation points: {str(e)}")
    
    # Check for services with high in-degree (many services depend on them)
    for node in graph.nodes():
        in_degree = len(list(graph.predecessors(node)))
        if in_degree > len(graph.nodes()) / 3:  # Arbitrary threshold: 1/3 of services depend on it
            if node not in spof:
                spof.append(node)
    
    return spof

def calculate_gini_coefficient(values: List[float]) -> float:
    """Calculate Gini coefficient (measure of inequality, 0=equal, 1=unequal)"""
    if not values:
        return 0
    
    # Need at least 2 values
    if len(values) < 2:
        return 0
    
    values = sorted(values)
    n = len(values)
    index = np.arange(1, n + 1)
    
    return (2 * np.sum(index * values) / (n * np.sum(values))) - (n + 1) / n

def calculate_capability_dispersion(architecture: ArchitectureState) -> float:
    """Calculate how dispersed capabilities are across services (0-1, higher means more dispersed)"""
    services = architecture.services or {}
    
    # Count capabilities per service
    service_capability_count = {}
    capability_services = {}
    
    for service_id, service in services.items():
        caps = service.get("capabilities", [])
        service_capability_count[service_id] = len(caps)
        
        for cap in caps:
            if cap not in capability_services:
                capability_services[cap] = []
            capability_services[cap].append(service_id)
    
    # Calculate variance in capabilities per service
    cap_counts = list(service_capability_count.values())
    avg_caps = sum(cap_counts) / len(cap_counts) if cap_counts else 0
    variance = sum((c - avg_caps) ** 2 for c in cap_counts) / len(cap_counts) if cap_counts else 0
    
    # Calculate normalized variance (0-1)
    max_possible_variance = avg_caps * avg_caps if avg_caps > 0 else 1  # Theoretical maximum
    normalized_variance = min(1.0, variance / max_possible_variance) if max_possible_variance > 0 else 0
    
    # Calculate capability spread (how many services implement each capability)
    capability_spread = [len(services) for cap, services in capability_services.items()]
    avg_spread = sum(capability_spread) / len(capability_spread) if capability_spread else 0
    spread_variance = sum((s - avg_spread) ** 2 for s in capability_spread) / len(capability_spread) if capability_spread else 0
    
    # Normalize spread variance
    max_spread_variance = (len(services) - avg_spread) ** 2 if avg_spread < len(services) else 1
    normalized_spread = min(1.0, spread_variance / max_spread_variance) if max_spread_variance > 0 else 0
    
    # Combined dispersion score
    return (normalized_variance * 0.5 + normalized_spread * 0.5)

def calculate_entropy(values: List[float]) -> float:
    """Calculate the entropy of a distribution"""
    if not values:
        return 0
    
    # Calculate probability distribution
    total = sum(values)
    if total == 0:
        return 0
    
    probabilities = [v / total for v in values]
    
    # Calculate entropy
    return -sum(p * math.log(p) if p > 0 else 0 for p in probabilities)

def compare_services(current: ArchitectureState, proposed: ArchitectureState) -> Dict[str, Any]:
    """Compare services between two architecture states"""
    current_services = current.services or {}
    proposed_services = proposed.services or {}
    
    # Find added, removed, and modified services
    added_services = [s_id for s_id in proposed_services if s_id not in current_services]
    removed_services = [s_id for s_id in current_services if s_id not in proposed_services]
    
    # Check for modified services
    modified_services = {}
    for s_id in set(current_services.keys()) & set(proposed_services.keys()):
        changes = {}
        
        # Check capabilities
        current_caps = set(current_services[s_id].get("capabilities", []))
        proposed_caps = set(proposed_services[s_id].get("capabilities", []))
        
        added_caps = list(proposed_caps - current_caps)
        removed_caps = list(current_caps - proposed_caps)
        
        if added_caps or removed_caps:
            changes["capabilities"] = {
                "added": added_caps,
                "removed": removed_caps
            }
        
        # Check resource changes
        if "resource_allocation" in current_services[s_id] and "resource_allocation" in proposed_services[s_id]:
            resource_changes = {}
            curr_res = current_services[s_id]["resource_allocation"]
            prop_res = proposed_services[s_id]["resource_allocation"]
            
            for res_type in set(curr_res.keys()) | set(prop_res.keys()):
                curr_val = curr_res.get(res_type, 0)
                prop_val = prop_res.get(res_type, 0)
                
                if curr_val != prop_val:
                    resource_changes[res_type] = {
                        "from": curr_val,
                        "to": prop_val,
                        "change": prop_val - curr_val,
                        "change_pct": ((prop_val - curr_val) / curr_val * 100) if curr_val != 0 else float('inf')
                    }
            
            if resource_changes:
                changes["resources"] = resource_changes
        
        # Check dependency changes
        current_deps = set(current_services[s_id].get("dependencies", []))
        proposed_deps = set(proposed_services[s_id].get("dependencies", []))
        
        added_deps = list(proposed_deps - current_deps)
        removed_deps = list(current_deps - proposed_deps)
        
        if added_deps or removed_deps:
            changes["dependencies"] = {
                "added": added_deps,
                "removed": removed_deps
            }
        
        if changes:
            modified_services[s_id] = changes
    
    return {
        "added_services": added_services,
        "removed_services": removed_services,
        "modified_services": modified_services,
        "total_changes": len(added_services) + len(removed_services) + len(modified_services)
    }

def generate_synthetic_telemetry(services: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Generate synthetic telemetry data for demo purposes"""
    telemetry = {}
    
    for service_id, service in services.items():
        # Generate realistic-looking metrics
        avg_latency = random.uniform(20, 200)  # ms
        throughput = random.randint(10, 1000)  # requests per minute
        error_rate = random.uniform(0, 0.1)  # 0-10% error rate
        
        # Make larger services potentially slower
        if "resource_allocation" in service:
            resources = service["resource_allocation"]
            cpu = resources.get("cpu", 1.0)
            memory = resources.get("memory", 1.0)
            
            # More complex services have higher latency but higher throughput
            avg_latency += (cpu + memory) * 10
            throughput += int((cpu + memory) * 100)
        
        # Services with more capabilities might have more errors
        if "capabilities" in service:
            cap_count = len(service["capabilities"])
            error_rate += cap_count * 0.005  # 0.5% per capability
        
        telemetry[service_id] = {
            "avg_latency": avg_latency,
            "throughput": throughput,
            "error_rate": min(1.0, error_rate),  # Cap at 100%
            "samples": random.randint(100, 1000)  # Number of data points
        }
    
    return telemetry

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8060)