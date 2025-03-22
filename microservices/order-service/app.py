import os
import json
import time
import logging
import asyncio
import random
import uuid
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Response, Request
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Order Service")

# Models
class Order(BaseModel):
    id: str
    user_id: str
    items: List[Dict[str, Any]]
    total_amount: float
    status: str
    created_at: float
    updated_at: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class OrderCreateRequest(BaseModel):
    user_id: str
    items: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None

class ServiceConfig(BaseModel):
    capabilities: List[str] = ["order_management", "inventory_check"]
    scaling_factor: float = 1.0
    resource_allocation: Dict[str, float] = {"cpu": 1.0, "memory": 1.3}
    additional_config: Optional[Dict[str, Any]] = None

# Service state
orders = {}
service_config = ServiceConfig()
service_id = os.environ.get("SERVICE_ID", "order-service")
service_health = "healthy"
registered_with_apl = False

# Environment variables
APL_URL = os.environ.get("APL_URL", "http://plasticity-layer:8010")
TELEMETRY_URL = os.environ.get("TELEMETRY_URL", "http://telemetry:8050")
USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL", "http://user-service:9000")
PAYMENT_SERVICE_URL = os.environ.get("PAYMENT_SERVICE_URL", "http://payment-service:9020")

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {service_id}")
    asyncio.create_task(register_with_apl())
    asyncio.create_task(send_telemetry())
    
    # Add some test data
    for i in range(5):
        order_id = str(uuid.uuid4())
        orders[order_id] = Order(
            id=order_id,
            user_id=f"user{i}",
            items=[
                {"product_id": f"product{j}", "quantity": random.randint(1, 3), "price": random.uniform(10, 100)}
                for j in range(random.randint(1, 5))
            ],
            total_amount=random.uniform(50, 500),
            status="completed" if random.random() > 0.3 else "pending",
            created_at=time.time() - random.randint(0, 86400)
        )

# API Endpoints
@app.get("/")
async def root():
    return {
        "service": service_id,
        "status": service_health,
        "capabilities": service_config.capabilities,
        "order_count": len(orders)
    }

@app.get("/health")
async def health_check():
    return {"status": service_health}

@app.get("/orders")
async def get_orders():
    return list(orders.values())

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders[order_id]

@app.post("/orders")
async def create_order(request: OrderCreateRequest, background_tasks: BackgroundTasks):
    # Create a new order
    order_id = str(uuid.uuid4())
    
    # Calculate total amount
    total_amount = sum(item.get("price", 0) * item.get("quantity", 1) for item in request.items)
    
    # Create order object
    order = Order(
        id=order_id,
        user_id=request.user_id,
        items=request.items,
        total_amount=total_amount,
        status="pending",
        created_at=time.time(),
        metadata=request.metadata
    )
    
    # Store order
    orders[order_id] = order
    
    # Simulate order processing
    background_tasks.add_task(process_order, order_id)
    
    # Simulate some load
    await asyncio.sleep(random.uniform(0.1, 0.3))
    
    # Add transaction ID for tracking
    transaction_id = str(uuid.uuid4())
    if not order.metadata:
        order.metadata = {}
    order.metadata["transaction_id"] = transaction_id
    
    return order

@app.put("/orders/{order_id}/cancel")
async def cancel_order(order_id: str):
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders[order_id]
    
    if order.status == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel a completed order")
    
    order.status = "cancelled"
    order.updated_at = time.time()
    
    # Simulate some load
    await asyncio.sleep(random.uniform(0.05, 0.2))
    
    return order

@app.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str):
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders[order_id]
    order.status = status
    order.updated_at = time.time()
    
    return order

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

# Order Processing Background Tasks
async def process_order(order_id: str):
    """Process an order in the background"""
    if order_id not in orders:
        logger.error(f"Order {order_id} not found during processing")
        return
    
    order = orders[order_id]
    
    try:
        # Check inventory first
        inventory_check = await check_inventory(order)
        
        if not inventory_check["success"]:
            order.status = "failed"
            order.updated_at = time.time()
            if not order.metadata:
                order.metadata = {}
            order.metadata["failure_reason"] = "Inventory check failed"
            return
        
        # Check if user exists (optional)
        try:
            user_check = await verify_user(order.user_id)
            if not user_check["success"]:
                logger.warning(f"User {order.user_id} verification failed, but continuing")
                # We'll continue anyway for demo purposes
        except Exception as e:
            logger.warning(f"User verification error: {str(e)}")
        
        # Process payment
        try:
            payment = await process_payment(order)
            
            if payment["success"]:
                order.status = "completed"
                if not order.metadata:
                    order.metadata = {}
                order.metadata["payment_id"] = payment.get("payment_id")
            else:
                order.status = "failed"
                if not order.metadata:
                    order.metadata = {}
                order.metadata["failure_reason"] = "Payment failed"
        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}")
            order.status = "failed"
            if not order.metadata:
                order.metadata = {}
            order.metadata["failure_reason"] = str(e)
        
        order.updated_at = time.time()
    
    except Exception as e:
        logger.error(f"Error processing order {order_id}: {str(e)}")
        order.status = "failed"
        order.updated_at = time.time()
        if not order.metadata:
            order.metadata = {}
        order.metadata["failure_reason"] = str(e)

async def check_inventory(order: Order) -> Dict[str, Any]:
    """Check if items are in inventory"""
    # This would call an inventory service in a real system
    # For demo purposes, we'll simulate success most of the time
    await asyncio.sleep(random.uniform(0.05, 0.2))
    
    # 90% chance of success
    success = random.random() < 0.9
    
    # Record the transaction for telemetry
    transaction_id = order.metadata.get("transaction_id", str(uuid.uuid4()))
    await send_transaction_telemetry(
        transaction_id=transaction_id,
        action="inventory_check",
        success=success
    )
    
    return {"success": success}

async def verify_user(user_id: str) -> Dict[str, Any]:
    """Verify that the user exists"""
    try:
        # Make an actual API call to the user service
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
            
            if response.status_code == 200:
                return {"success": True, "user": response.json()}
            else:
                return {"success": False, "error": f"User not found: {response.status_code}"}
    except Exception as e:
        logger.error(f"Error verifying user: {str(e)}")
        # Fallback to simulation
        await asyncio.sleep(random.uniform(0.05, 0.1))
        return {"success": random.random() < 0.95}  # 95% chance of success

async def process_payment(order: Order) -> Dict[str, Any]:
    """Process payment for the order"""
    try:
        # Make an actual API call to the payment service if available
        payment_data = {
            "order_id": order.id,
            "user_id": order.user_id,
            "amount": order.total_amount,
            "metadata": {
                "transaction_id": order.metadata.get("transaction_id") if order.metadata else None
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PAYMENT_SERVICE_URL}/payments",
                json=payment_data
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Payment service error: {response.status_code}")
                # Fallback to simulation
                return fallback_payment_simulation(order)
    except Exception as e:
        logger.error(f"Error calling payment service: {str(e)}")
        # Fallback to simulation
        return fallback_payment_simulation(order)

def fallback_payment_simulation(order: Order) -> Dict[str, Any]:
    """Simulate payment processing when the payment service is unavailable"""
    # 85% chance of payment success
    success = random.random() < 0.85
    
    # Record transaction for telemetry
    transaction_id = order.metadata.get("transaction_id", str(uuid.uuid4())) if order.metadata else str(uuid.uuid4())
    
    # This is synchronous so we can't await
    # We'd want to make this async in a real implementation
    asyncio.create_task(send_transaction_telemetry(
        transaction_id=transaction_id,
        action="payment_processing",
        success=success
    ))
    
    return {
        "success": success,
        "payment_id": str(uuid.uuid4()) if success else None,
        "simulation": True
    }

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
                    "endpoint": f"http://{service_id}:9010",
                    "capabilities": service_config.capabilities,
                    "dependencies": ["user-service", "payment-service"],
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
                cpu_usage = random.uniform(0.2, 0.6)  # Simulated CPU usage
                memory_usage = random.uniform(0.3, 0.7)  # Simulated memory usage
                request_count = random.randint(8, 25)  # Simulated request count
                error_count = random.randint(0, 2)  # Simulated error count
                
                # Send telemetry
                telemetry_data = {
                    "timestamp": time.time(),
                    "service_id": service_id,
                    "endpoint": f"http://{service_id}:9010",
                    "latency": random.uniform(20, 120),  # ms
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

async def send_transaction_telemetry(transaction_id: str, action: str, success: bool):
    """Send transaction-specific telemetry"""
    try:
        if registered_with_apl:
            telemetry_data = {
                "timestamp": time.time(),
                "service_id": service_id,
                "endpoint": f"http://{service_id}:9010/orders",
                "latency": random.uniform(20, 120),  # ms
                "cpu_usage": random.uniform(0.3, 0.7),
                "memory_usage": random.uniform(0.3, 0.7),
                "request_count": 1,
                "error_count": 0 if success else 1,
                "additional_metrics": {
                    "transaction_id": transaction_id,
                    "action": action,
                    "success": success
                }
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(f"{TELEMETRY_URL}/data", json=telemetry_data)
                logger.debug(f"Sent transaction telemetry for {transaction_id}")
    except Exception as e:
        logger.error(f"Error sending transaction telemetry: {str(e)}")

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
            if capability == "order_analytics":
                # Simulate adding analytics features
                logger.info("Enabling order analytics features")
                # In a real system, we might load additional modules, etc.
    
    if removed_capabilities:
        logger.info(f"Removed capabilities: {removed_capabilities}")
        # Disable functionality based on removed capabilities
        for capability in removed_capabilities:
            if capability == "inventory_check":
                # Simulate removing inventory check features
                logger.info("Disabling inventory check features")
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
    uvicorn.run(app, host="0.0.0.0", port=9010)