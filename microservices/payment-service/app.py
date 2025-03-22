import os
import json
import time
import logging
import asyncio
import random
import uuid
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Payment Service")

# Models
class Payment(BaseModel):
    id: str
    order_id: str
    user_id: str
    amount: float
    status: str
    created_at: float
    completed_at: Optional[float] = None
    payment_method: Optional[str] = "credit_card"
    transaction_details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class PaymentRequest(BaseModel):
    order_id: str
    user_id: str
    amount: float
    payment_method: Optional[str] = "credit_card"
    metadata: Optional[Dict[str, Any]] = None

class ServiceConfig(BaseModel):
    capabilities: List[str] = ["payment_processing", "fraud_detection"]
    scaling_factor: float = 1.0
    resource_allocation: Dict[str, float] = {"cpu": 0.8, "memory": 1.0}
    additional_config: Optional[Dict[str, Any]] = None

# Service state
payments = {}
service_config = ServiceConfig()
service_id = os.environ.get("SERVICE_ID", "payment-service")
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
    for i in range(5):
        payment_id = str(uuid.uuid4())
        payments[payment_id] = Payment(
            id=payment_id,
            order_id=f"order{i}",
            user_id=f"user{i}",
            amount=random.uniform(50, 500),
            status="completed" if random.random() > 0.2 else "pending",
            created_at=time.time() - random.randint(0, 86400),
            completed_at=time.time() - random.randint(0, 3600) if random.random() > 0.2 else None,
            payment_method=random.choice(["credit_card", "paypal", "bank_transfer"]),
            transaction_details={
                "transaction_id": str(uuid.uuid4()),
                "processor_response": "approved"
            }
        )

# API Endpoints
@app.get("/")
async def root():
    return {
        "service": service_id,
        "status": service_health,
        "capabilities": service_config.capabilities,
        "payment_count": len(payments)
    }

@app.get("/health")
async def health_check():
    return {"status": service_health}

@app.get("/payments")
async def get_payments():
    return list(payments.values())

@app.get("/payments/{payment_id}")
async def get_payment(payment_id: str):
    if payment_id not in payments:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payments[payment_id]

@app.post("/payments")
async def create_payment(request: PaymentRequest, background_tasks: BackgroundTasks):
    # Create a new payment
    payment_id = str(uuid.uuid4())
    
    # Create payment object
    payment = Payment(
        id=payment_id,
        order_id=request.order_id,
        user_id=request.user_id,
        amount=request.amount,
        status="pending",
        created_at=time.time(),
        payment_method=request.payment_method,
        metadata=request.metadata
    )
    
    # Store payment
    payments[payment_id] = payment
    
    # Process payment in background
    background_tasks.add_task(process_payment, payment_id)
    
    # Simulate some load
    await asyncio.sleep(random.uniform(0.1, 0.3))
    
    return {
        "success": True,
        "payment_id": payment_id,
        "status": "pending"
    }

@app.put("/payments/{payment_id}/cancel")
async def cancel_payment(payment_id: str):
    if payment_id not in payments:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment = payments[payment_id]
    
    if payment.status == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel a completed payment")
    
    payment.status = "cancelled"
    
    # Simulate some load
    await asyncio.sleep(random.uniform(0.05, 0.2))
    
    return payment

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

# Payment Processing
async def process_payment(payment_id: str):
    """Process a payment in the background"""
    if payment_id not in payments:
        logger.error(f"Payment {payment_id} not found during processing")
        return
    
    payment = payments[payment_id]
    
    try:
        # First, check for fraud
        fraud_result = await check_for_fraud(payment)
        
        if fraud_result["is_fraud"]:
            payment.status = "rejected"
            payment.transaction_details = {
                "rejection_reason": "Potential fraud detected",
                "fraud_score": fraud_result["fraud_score"]
            }
            return
        
        # Simulate payment processing
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Determine success (90% success rate)
        success = random.random() < 0.9
        
        if success:
            payment.status = "completed"
            payment.completed_at = time.time()
            payment.transaction_details = {
                "transaction_id": str(uuid.uuid4()),
                "processor_response": "approved",
                "authorization_code": f"AUTH{random.randint(100000, 999999)}"
            }
        else:
            payment.status = "failed"
            payment.transaction_details = {
                "transaction_id": str(uuid.uuid4()),
                "processor_response": "declined",
                "decline_reason": random.choice([
                    "insufficient_funds",
                    "card_expired",
                    "processing_error"
                ])
            }
        
        # Send transaction telemetry
        transaction_id = payment.metadata.get("transaction_id", str(uuid.uuid4())) if payment.metadata else str(uuid.uuid4())
        await send_transaction_telemetry(
            transaction_id=transaction_id,
            action="payment_processing",
            success=success
        )
    
    except Exception as e:
        logger.error(f"Error processing payment {payment_id}: {str(e)}")
        payment.status = "failed"
        payment.transaction_details = {
            "error": str(e)
        }

async def check_for_fraud(payment: Payment) -> Dict[str, Any]:
    """Check for potential fraud in a payment"""
    # For demo purposes, we'll simulate fraud detection
    # In a real system, this would use complex fraud detection algorithms
    
    # Generate a random fraud score (0-100, higher is more suspicious)
    fraud_score = random.uniform(0, 100)
    
    # Consider high scores as potential fraud
    is_fraud = fraud_score > 90  # Only 10% of transactions marked as fraud
    
    # Record transaction for telemetry if we have transaction ID
    if payment.metadata and "transaction_id" in payment.metadata:
        await send_transaction_telemetry(
            transaction_id=payment.metadata["transaction_id"],
            action="fraud_check",
            success=not is_fraud  # Success means no fraud
        )
    
    # Simulate processing time
    await asyncio.sleep(random.uniform(0.1, 0.5))
    
    return {
        "is_fraud": is_fraud,
        "fraud_score": fraud_score,
        "reasons": ["unusual_location", "high_amount"] if is_fraud else []
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
                    "endpoint": f"http://{service_id}:9020",
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
                cpu_usage = random.uniform(0.1, 0.4)  # Simulated CPU usage
                memory_usage = random.uniform(0.2, 0.5)  # Simulated memory usage
                request_count = random.randint(5, 15)  # Simulated request count
                error_count = random.randint(0, 1)  # Simulated error count
                
                # Send telemetry
                telemetry_data = {
                    "timestamp": time.time(),
                    "service_id": service_id,
                    "endpoint": f"http://{service_id}:9020",
                    "latency": random.uniform(30, 150),  # ms
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
                "endpoint": f"http://{service_id}:9020/payments",
                "latency": random.uniform(30, 150),  # ms
                "cpu_usage": random.uniform(0.2, 0.6),
                "memory_usage": random.uniform(0.2, 0.5),
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
            if capability == "subscription_management":
                # Simulate adding subscription features
                logger.info("Enabling subscription management features")
                # In a real system, we might load additional modules, etc.
    
    if removed_capabilities:
        logger.info(f"Removed capabilities: {removed_capabilities}")
        # Disable functionality based on removed capabilities
        for capability in removed_capabilities:
            if capability == "fraud_detection":
                # Simulate removing fraud detection features
                logger.info("Disabling fraud detection features")
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
    uvicorn.run(app, host="0.0.0.0", port=9020)