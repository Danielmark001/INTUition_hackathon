# Metamorphic Architecture

A system that fundamentally transforms software architecture from static design decisions to living systems that continuously reshape themselves.

## Overview

Metamorphic Architecture eliminates traditional architectural boundaries, allowing applications to autonomously evolve their structure, component relationships, and resource allocation in response to changing conditions, user behavior, and system goals.

This project implements a proof-of-concept system that demonstrates key capabilities of Metamorphic Architecture:

1. **Continuous Architectural Evolution**: Structure adapts automatically to changing conditions
2. **Context-Aware Optimization**: System morphs itself based on actual usage patterns
3. **Autonomous Boundary Shifts**: Components grow, shrink, merge, or split as needed
4. **Dynamic Trust Perimeters**: Security boundaries adjust based on threat intelligence

## System Components

The system consists of the following components:

- **Metamorphosis Engine**: Orchestrates architectural transformations
- **Architectural Plasticity Layer**: Abstracts components and enables reshaping
- **Usage Pattern Intelligence**: Analyzes patterns and identifies optimization opportunities
- **Multi-Objective Optimizer**: Balances competing concerns in architectural decisions
- **Service Registry**: Tracks all system components and their relationships
- **Telemetry Collector**: Gathers runtime data to inform architectural decisions
- **Architecture Analyzer**: Evaluates system characteristics and provides insights
- **Example Microservices**: Demonstrate metamorphic capabilities
- **Dashboard**: Visualizes the evolving architecture

## Prerequisites

- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) (v1.29.0+)
- [Node.js](https://nodejs.org/) (v16+) for dashboard development
- At least 4GB of available memory
- Internet connection (for pulling base images)

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/metamorphic-architecture.git
   cd metamorphic-architecture
   ```

2. Start the system with Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Access the dashboard:
   ```
   http://localhost:3000
   ```

4. View the API documentation:
   ```
   http://localhost:8000/docs  # Metamorphosis Engine API
   http://localhost:8010/docs  # Architectural Plasticity Layer API
   http://localhost:8020/docs  # Usage Pattern Intelligence API
   http://localhost:8030/docs  # Multi-Objective Optimizer API
   http://localhost:8040/docs  # Service Registry API
   http://localhost:8050/docs  # Telemetry Collector API
   http://localhost:8060/docs  # Architecture Analyzer API
   ```

## System Architecture

![System Architecture](./docs/architecture.png)

The system's components interact through well-defined APIs to enable architectural metamorphosis:

1. **Runtime Monitoring**: The Telemetry Collector gathers runtime data from all services
2. **Pattern Detection**: The Usage Pattern Intelligence analyzes telemetry to identify patterns
3. **Opportunity Identification**: The Architecture Analyzer evaluates the current architecture
4. **Transformation Planning**: The Multi-Objective Optimizer balances competing concerns
5. **Execution**: The Metamorphosis Engine orchestrates architectural transformations
6. **Adaptation**: The Architectural Plasticity Layer implements the transformations

## Demo Scenarios

### Scenario 1: Service Merging

This demo shows how the system automatically detects tightly coupled services and merges them.

1. Start with the default configuration
2. Generate load on the system using the provided script:
   ```bash
   ./scripts/generate_load.sh user-service order-service
   ```
3. Wait for the system to detect the coupling pattern (approximately 5 minutes)
4. Observe the automatic transformation in the dashboard

### Scenario 2: Resource Optimization

This demo shows how the system optimizes resource allocation based on actual usage.

1. Start with the default configuration
2. Generate uneven load on the system:
   ```bash
   ./scripts/generate_uneven_load.sh
   ```
3. Wait for the system to detect resource inefficiency (approximately 5 minutes)
4. Observe the automatic resource reallocation in the dashboard

### Scenario 3: Manual Transformation

This demo shows how to manually trigger architectural transformations.

1. Access the dashboard at http://localhost:3000
2. Go to the "Recommendations" tab
3. Select a recommendation and click "Apply Recommendation"
4. Observe the transformation process in the dashboard

## Component Details

### Metamorphosis Engine

The central orchestrator that manages architectural transformations. It:

- Evaluates the current system state
- Plans and executes transformations
- Maintains architecture history
- Provides decision-making APIs

**API Endpoints:**
- `GET /architecture/current` - Get current architecture
- `POST /transformations` - Create transformation plan
- `POST /transformations/{plan_id}/execute` - Execute transformation
- `GET /recommendations` - Get architecture recommendations

### Architectural Plasticity Layer

Enables architectural reconfiguration by providing abstractions over service interactions. It:

- Manages service registration and configuration
- Orchestrates transitions between states
- Controls traffic routing during transitions
- Ensures system stability during changes

**API Endpoints:**
- `GET /services` - List all registered services
- `POST /services` - Register a new service
- `POST /transitions` - Execute an architecture transition
- `GET /architecture/current` - Get current state

### Usage Pattern Intelligence

Monitors and analyzes system behavior to identify patterns. It:

- Processes telemetry data streams
- Detects usage patterns
- Identifies optimization opportunities
- Generates architectural recommendations

**API Endpoints:**
- `POST /telemetry` - Receive telemetry data
- `GET /patterns` - Get detected patterns
- `POST /patterns/system` - Analyze system-wide patterns
- `POST /recommendations` - Generate recommendations

### Multi-Objective Optimizer

Balances competing concerns in architectural decisions. It:

- Evaluates potential architectural states
- Optimizes for performance, reliability, cost, etc.
- Recommends optimal transformations
- Provides trade-off analysis

**API Endpoints:**
- `POST /optimize` - Start optimization process
- `POST /evaluate` - Evaluate an architecture state
- `GET /optimize/{optimization_id}` - Get optimization status

## Extending the System

### Adding New Services

1. Create a new service with the required metamorphic capabilities:
   - Register with Architectural Plasticity Layer
   - Send telemetry data
   - Implement configuration endpoint
   - Handle graceful shutdown

2. Add the service to `docker-compose.yml`:
   ```yaml
   new-service:
     build: ./microservices/new-service
     ports:
       - "9xxx:9xxx"
     environment:
       - APL_URL=http://plasticity-layer:8010
       - TELEMETRY_URL=http://telemetry:8050
     volumes:
       - ./shared-data:/app/data
     networks:
       - metamorphic-net
   ```

3. Start the service:
   ```bash
   docker-compose up -d new-service
   ```

### Adding New Transformation Types

1. Implement the transformation logic in `metamorphosis-engine/transformations/`
2. Register the transformation type in the Metamorphosis Engine
3. Add the necessary handlers in the Architectural Plasticity Layer

### Customizing Optimization Goals

1. Modify the optimization goals in `optimizer/goals/`
2. Adjust the weighting factors in `optimizer/config.json`
3. Restart the optimizer service:
   ```bash
   docker-compose restart optimizer
   ```

## Troubleshooting

### Common Issues

**Services fail to start:**
- Check Docker logs: `docker-compose logs [service-name]`
- Verify network connectivity between services
- Ensure sufficient system resources

**No patterns detected:**
- Verify telemetry is being collected: `curl http://localhost:8050/data/recent`
- Generate more load on the system
- Check Usage Pattern Intelligence logs

**Transformations fail:**
- Check Metamorphosis Engine logs: `docker-compose logs metamorphosis-engine`
- Verify service health in Service Registry
- Check for constraint violations in the optimizer

### Logs

Access logs for any component:
```bash
docker-compose logs -f [component-name]
```

Available components:
- `metamorphosis-engine`
- `plasticity-layer`
- `pattern-intelligence`
- `optimizer`
- `service-registry`
- `telemetry`
- `architecture-analyzer`
- `user-service`
- `order-service`
- `payment-service`
- `dashboard`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.