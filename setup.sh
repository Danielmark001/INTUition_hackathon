#!/bin/bash

# Metamorphic Architecture Setup Script
# This script helps set up and deploy the entire Metamorphic Architecture system

set -e  # Exit on error

# Display welcome message
echo "====================================================="
echo "      Metamorphic Architecture Setup Script"
echo "====================================================="
echo ""
echo "This script will help you set up and deploy the"
echo "Metamorphic Architecture demonstration system."
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "Prerequisites satisfied."
echo ""

# Ensure we're in the right directory
echo "Setting up environment..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Create necessary directories
mkdir -p shared-data
mkdir -p logs

# Ask whether to build from scratch or use prebuilt images
echo "How would you like to deploy the system?"
echo "1. Build all containers from scratch (recommended for first run)"
echo "2. Use prebuilt images if available (faster)"
echo "3. Rebuild only specific components"
echo "4. Clean everything and start fresh"

read -p "Enter your choice [1-4]: " deploy_choice

case $deploy_choice in
    1)
        echo "Building all containers from scratch..."
        docker-compose build --no-cache
        ;;
    2)
        echo "Using prebuilt images where available..."
        docker-compose pull
        docker-compose build
        ;;
    3)
        echo "Which components would you like to rebuild?"
        echo "1. Core system (metamorphosis-engine, plasticity-layer, etc.)"
        echo "2. Services (user-service, order-service, payment-service)"
        echo "3. Dashboard"
        echo "4. All of the above"
        
        read -p "Enter your choice [1-4]: " rebuild_choice
        
        case $rebuild_choice in
            1)
                echo "Rebuilding core system components..."
                docker-compose build metamorphosis-engine plasticity-layer pattern-intelligence optimizer service-registry telemetry architecture-analyzer
                ;;
            2)
                echo "Rebuilding services..."
                docker-compose build user-service order-service payment-service
                ;;
            3)
                echo "Rebuilding dashboard..."
                docker-compose build dashboard
                ;;
            4)
                echo "Rebuilding all components..."
                docker-compose build
                ;;
            *)
                echo "Invalid choice. Exiting."
                exit 1
                ;;
        esac
        ;;
    4)
        echo "Cleaning everything and starting fresh..."
        docker-compose down -v
        docker-compose rm -f
        rm -rf shared-data/*
        rm -rf logs/*
        docker-compose build --no-cache
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

# Start the system
echo ""
echo "Starting the Metamorphic Architecture system..."
docker-compose up -d

# Wait for services to initialize
echo "Waiting for services to initialize..."
sleep 10

# Check if all services are running
echo "Checking service status..."
running_services=$(docker-compose ps --services --filter "status=running" | wc -l)
total_services=$(docker-compose ps --services | wc -l)

if [ "$running_services" -eq "$total_services" ]; then
    echo "All services are running."
else
    echo "Warning: Not all services are running. Please check with 'docker-compose ps'"
fi

# Display URLs
echo ""
echo "====================================================="
echo "Metamorphic Architecture is now running!"
echo "====================================================="
echo ""
echo "Dashboard URL: http://localhost:3000"
echo ""
echo "API Documentation:"
echo "- Metamorphosis Engine: http://localhost:8000/docs"
echo "- Architectural Plasticity Layer: http://localhost:8010/docs"
echo "- Usage Pattern Intelligence: http://localhost:8020/docs"
echo "- Multi-Objective Optimizer: http://localhost:8030/docs"
echo "- Service Registry: http://localhost:8040/docs"
echo "- Telemetry Collector: http://localhost:8050/docs"
echo "- Architecture Analyzer: http://localhost:8060/docs"
echo ""
echo "Example Services:"
echo "- User Service: http://localhost:9000"
echo "- Order Service: http://localhost:9010"
echo "- Payment Service: http://localhost:9020"
echo ""
echo "To demonstrate the system's capabilities, run:"
echo "./scripts/generate_load.sh"
echo ""
echo "To stop the system:"
echo "docker-compose down"
echo ""
echo "Enjoy exploring Metamorphic Architecture!"