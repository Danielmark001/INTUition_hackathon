#!/bin/bash

# Metamorphic Architecture Load Generation Script
# This script generates load on the system to demonstrate its adaptive capabilities

set -e  # Exit on error

# Display welcome message
echo "====================================================="
echo "      Metamorphic Architecture Load Generator"
echo "====================================================="
echo ""

# Check command-line arguments
SCENARIO="balanced"
DURATION=300
SERVICES=()

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --scenario|-s)
            SCENARIO="$2"
            shift
            ;;
        --duration|-d)
            DURATION="$2"
            shift
            ;;
        --intensity|-i)
            INTENSITY="$2"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options] [service1 service2 ...]"
            echo ""
            echo "Options:"
            echo "  --scenario, -s   Load scenario (balanced, service-coupling, uneven, spike)"
            echo "  --duration, -d   Duration in seconds (default: 300)"
            echo "  --intensity, -i  Load intensity (1-10, default: 5)"
            echo ""
            echo "If specific services are listed, load will focus on those."
            echo "Otherwise, load will be distributed according to the scenario."
            echo ""
            echo "Available scenarios:"
            echo "  balanced         - Balanced load across all services"
            echo "  service-coupling - Generate load that shows service coupling"
            echo "  uneven           - Uneven load to demonstrate resource adaptation"
            echo "  spike            - Periodic load spikes to test resilience"
            exit 0
            ;;
        *)
            SERVICES+=("$1")
            ;;
    esac
    shift
done

# Set default intensity
if [[ -z "$INTENSITY" ]]; then
    INTENSITY=5
fi

# Validate intensity
if ! [[ "$INTENSITY" =~ ^[1-9]|10$ ]]; then
    echo "Error: Intensity must be between 1 and 10."
    exit 1
fi

# Calculate rate parameters based on intensity
BASE_RATE=$(( INTENSITY * 2 ))
BURST_RATE=$(( INTENSITY * 5 ))

# If no specific services specified, use defaults
if [ ${#SERVICES[@]} -eq 0 ]; then
    SERVICES=("user-service" "order-service" "payment-service")
fi

echo "Generating load with scenario: $SCENARIO"
echo "Duration: $DURATION seconds"
echo "Intensity: $INTENSITY"
echo "Target services: ${SERVICES[*]}"
echo ""

# Define API endpoints
USER_SERVICE="http://localhost:9000"
ORDER_SERVICE="http://localhost:9010"
PAYMENT_SERVICE="http://localhost:9020"

# Create temporary user data file
TEMP_USER_FILE=$(mktemp)
cat > "$TEMP_USER_FILE" << EOF
{
  "users": [
    {"id": "user1", "username": "alice", "email": "alice@example.com"},
    {"id": "user2", "username": "bob", "email": "bob@example.com"},
    {"id": "user3", "username": "charlie", "email": "charlie@example.com"},
    {"id": "user4", "username": "dave", "email": "dave@example.com"},
    {"id": "user5", "username": "eve", "email": "eve@example.com"}
  ],
  "products": [
    {"id": "product1", "name": "Laptop", "price": 999.99},
    {"id": "product2", "name": "Smartphone", "price": 499.99},
    {"id": "product3", "name": "Headphones", "price": 149.99},
    {"id": "product4", "name": "Monitor", "price": 299.99},
    {"id": "product5", "name": "Keyboard", "price": 79.99}
  ]
}
EOF

# Function to send user-service requests
generate_user_requests() {
    local rate=$1
    local duration=$2
    local iteration_sleep=$3
    
    echo "Generating user service requests at rate: $rate req/s for $duration seconds"
    
    end_time=$((SECONDS + duration))
    
    while [ $SECONDS -lt $end_time ]; do
        for i in $(seq 1 $rate); do
            # Choose a random action
            action=$((RANDOM % 4))
            
            case $action in
                0)
                    # Create a new user
                    username="user_${RANDOM}"
                    curl -s -X POST "$USER_SERVICE/users" \
                         -H "Content-Type: application/json" \
                         -d "{\"username\":\"$username\",\"email\":\"$username@example.com\"}" > /dev/null &
                    ;;
                1)
                    # Get all users
                    curl -s "$USER_SERVICE/users" > /dev/null &
                    ;;
                2)
                    # Get a specific user
                    user_id=$((RANDOM % 5 + 1))
                    curl -s "$USER_SERVICE/users/user$user_id" > /dev/null &
                    ;;
                3)
                    # Update a user
                    user_id=$((RANDOM % 5 + 1))
                    curl -s -X PUT "$USER_SERVICE/users/user$user_id" \
                         -H "Content-Type: application/json" \
                         -d "{\"username\":\"updated_user$user_id\",\"email\":\"updated$user_id@example.com\"}" > /dev/null &
                    ;;
            esac
        done
        
        sleep $iteration_sleep
    done
}

# Function to send order-service requests
generate_order_requests() {
    local rate=$1
    local duration=$2
    local iteration_sleep=$3
    
    echo "Generating order service requests at rate: $rate req/s for $duration seconds"
    
    end_time=$((SECONDS + duration))
    
    while [ $SECONDS -lt $end_time ]; do
        for i in $(seq 1 $rate); do
            # Choose a random action
            action=$((RANDOM % 3))
            
            case $action in
                0)
                    # Create a new order
                    user_id=$((RANDOM % 5 + 1))
                    product_id=$((RANDOM % 5 + 1))
                    quantity=$((RANDOM % 3 + 1))
                    price=$(awk -v seed=$RANDOM 'BEGIN { srand(seed); print 10 + rand() * 100 }')
                    
                    curl -s -X POST "$ORDER_SERVICE/orders" \
                         -H "Content-Type: application/json" \
                         -d "{\"user_id\":\"user$user_id\",\"items\":[{\"product_id\":\"product$product_id\",\"quantity\":$quantity,\"price\":$price}]}" > /dev/null &
                    ;;
                1)
                    # Get all orders
                    curl -s "$ORDER_SERVICE/orders" > /dev/null &
                    ;;
                2)
                    # Get order details
                    curl -s "$ORDER_SERVICE/orders" | grep -o '"id":"[^"]*' | head -1 | sed 's/"id":"//g' | xargs -I{} \
                        curl -s "$ORDER_SERVICE/orders/{}" > /dev/null &
                    ;;
            esac
        done
        
        sleep $iteration_sleep
    done
}

# Function to send payment-service requests
generate_payment_requests() {
    local rate=$1
    local duration=$2
    local iteration_sleep=$3
    
    echo "Generating payment service requests at rate: $rate req/s for $duration seconds"
    
    end_time=$((SECONDS + duration))
    
    while [ $SECONDS -lt $end_time ]; do
        for i in $(seq 1 $rate); do
            # Choose a random action
            action=$((RANDOM % 3))
            
            case $action in
                0)
                    # Create a new payment
                    user_id=$((RANDOM % 5 + 1))
                    order_id=$((RANDOM % 100 + 1))
                    amount=$(awk -v seed=$RANDOM 'BEGIN { srand(seed); print 50 + rand() * 500 }')
                    
                    curl -s -X POST "$PAYMENT_SERVICE/payments" \
                         -H "Content-Type: application/json" \
                         -d "{\"order_id\":\"order$order_id\",\"user_id\":\"user$user_id\",\"amount\":$amount}" > /dev/null &
                    ;;
                1)
                    # Get all payments
                    curl -s "$PAYMENT_SERVICE/payments" > /dev/null &
                    ;;
                2)
                    # Get payment details
                    curl -s "$PAYMENT_SERVICE/payments" | grep -o '"id":"[^"]*' | head -1 | sed 's/"id":"//g' | xargs -I{} \
                        curl -s "$PAYMENT_SERVICE/payments/{}" > /dev/null &
                    ;;
            esac
        done
        
        sleep $iteration_sleep
    done
}

# Generate loads based on scenario
case $SCENARIO in
    "balanced")
        # Balanced load across all services
        echo "Running balanced load scenario..."
        
        for service in "${SERVICES[@]}"; do
            case $service in
                "user-service")
                    generate_user_requests $BASE_RATE $DURATION 1 &
                    ;;
                "order-service")
                    generate_order_requests $BASE_RATE $DURATION 1 &
                    ;;
                "payment-service")
                    generate_payment_requests $BASE_RATE $DURATION 1 &
                    ;;
            esac
        done
        ;;
        
    "service-coupling")
        # Scenario to demonstrate service coupling
        echo "Running service coupling scenario..."
        
        # This creates a coupled flow: create user -> create order -> process payment
        end_time=$((SECONDS + DURATION))
        
        while [ $SECONDS -lt $end_time ]; do
            # Create a random number of users
            for i in $(seq 1 $((RANDOM % 3 + 1))); do
                username="user_${RANDOM}"
                # Create user
                user_response=$(curl -s -X POST "$USER_SERVICE/users" \
                     -H "Content-Type: application/json" \
                     -d "{\"username\":\"$username\",\"email\":\"$username@example.com\"}")
                
                user_id=$(echo $user_response | grep -o '"id":"[^"]*' | head -1 | sed 's/"id":"//g')
                
                if [ -n "$user_id" ]; then
                    # For each user, create 1-3 orders
                    for j in $(seq 1 $((RANDOM % 3 + 1))); do
                        # Create order for this user
                        product_id=$((RANDOM % 5 + 1))
                        quantity=$((RANDOM % 3 + 1))
                        price=$(awk -v seed=$RANDOM 'BEGIN { srand(seed); print 10 + rand() * 100 }')
                        
                        order_response=$(curl -s -X POST "$ORDER_SERVICE/orders" \
                             -H "Content-Type: application/json" \
                             -d "{\"user_id\":\"$user_id\",\"items\":[{\"product_id\":\"product$product_id\",\"quantity\":$quantity,\"price\":$price}]}")
                        
                        order_id=$(echo $order_response | grep -o '"payment_id":"[^"]*' | head -1 | sed 's/"payment_id":"//g')
                        
                        # Even without a valid order ID, create a payment to generate the traffic pattern
                        amount=$(awk -v seed=$RANDOM 'BEGIN { srand(seed); print 50 + rand() * 500 }')
                        
                        curl -s -X POST "$PAYMENT_SERVICE/payments" \
                             -H "Content-Type: application/json" \
                             -d "{\"order_id\":\"$order_id\",\"user_id\":\"$user_id\",\"amount\":$amount}" > /dev/null
                    done
                fi
            done
            
            # Get some order details to generate additional coupling
            curl -s "$ORDER_SERVICE/orders" | grep -o '"id":"[^"]*' | head -3 | sed 's/"id":"//g' | while read order_id; do
                curl -s "$ORDER_SERVICE/orders/$order_id" > /dev/null
                
                # For each order, check the user
                user_id=$(curl -s "$ORDER_SERVICE/orders/$order_id" | grep -o '"user_id":"[^"]*' | sed 's/"user_id":"//g')
                if [ -n "$user_id" ]; then
                    curl -s "$USER_SERVICE/users/$user_id" > /dev/null
                fi
            done
            
            sleep 1
        done
        ;;
        
    "uneven")
        # Uneven load to demonstrate resource adaptation
        echo "Running uneven load scenario..."
        
        # Determine which service gets higher load
        high_load_service=${SERVICES[0]}
        
        for service in "${SERVICES[@]}"; do
            rate=$BASE_RATE
            
            if [ "$service" == "$high_load_service" ]; then
                rate=$((BASE_RATE * 5))  # 5x more load on first service
                echo "Applying high load to $service"
            else
                echo "Applying normal load to $service"
            fi
            
            case $service in
                "user-service")
                    generate_user_requests $rate $DURATION 1 &
                    ;;
                "order-service")
                    generate_order_requests $rate $DURATION 1 &
                    ;;
                "payment-service")
                    generate_payment_requests $rate $DURATION 1 &
                    ;;
            esac
        done
        ;;
        
    "spike")
        # Periodic load spikes to test resilience
        echo "Running spike load scenario..."
        
        # Normal phase duration: 30 seconds, spike duration: 15 seconds
        normal_duration=30
        spike_duration=15
        cycles=$((DURATION / (normal_duration + spike_duration)))
        
        for (( cycle=1; cycle<=cycles; cycle++ )); do
            echo "Cycle $cycle/$cycles - Normal load phase"
            
            # Start normal load in background
            for service in "${SERVICES[@]}"; do
                case $service in
                    "user-service")
                        generate_user_requests $BASE_RATE $normal_duration 1 &
                        ;;
                    "order-service")
                        generate_order_requests $BASE_RATE $normal_duration 1 &
                        ;;
                    "payment-service")
                        generate_payment_requests $BASE_RATE $normal_duration 1 &
                        ;;
                esac
            done
            
            # Wait for normal phase to complete
            sleep $normal_duration
            
            echo "Cycle $cycle/$cycles - Spike load phase"
            
            # Start spike load in background
            for service in "${SERVICES[@]}"; do
                case $service in
                    "user-service")
                        generate_user_requests $BURST_RATE $spike_duration 0.5 &
                        ;;
                    "order-service")
                        generate_order_requests $BURST_RATE $spike_duration 0.5 &
                        ;;
                    "payment-service")
                        generate_payment_requests $BURST_RATE $spike_duration 0.5 &
                        ;;
                esac
            done
            
            # Wait for spike phase to complete
            sleep $spike_duration
        done
        ;;
        
    *)
        echo "Unknown scenario: $SCENARIO"
        exit 1
        ;;
esac

# Wait for all background processes to finish
wait

# Cleanup
rm -f "$TEMP_USER_FILE"

echo ""
echo "Load generation completed."
echo "Check the dashboard at http://localhost:3000 to see how the system adapted."