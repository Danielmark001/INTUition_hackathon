# Metamorphic Architecture Dashboard

A React-based dashboard for visualizing and controlling the Metamorphic Architecture system.

## Overview

This dashboard provides a user interface for monitoring and interacting with the Metamorphic Architecture system. It features:

- System overview with key metrics
- Service management and visualization
- Transformation plan execution and monitoring
- Architecture visualization
- Recommendation management
- Telemetry visualization

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Metamorphic Architecture backend services running

### Installation

1. Clone the repository (if you haven't already):
   ```bash
   git clone https://github.com/your-username/metamorphic-architecture.git
   cd metamorphic-architecture/dashboard
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables (optional):
   Create a `.env` file in the dashboard directory:
   ```
   REACT_APP_API_URL=http://localhost:8000/api
   ```

   If not set, the dashboard will default to `/api` as the base URL.

4. Start the development server:
   ```bash
   npm start
   ```

5. Build for production:
   ```bash
   npm run build
   ```

## Project Structure

```
dashboard/
├── public/                 # Public assets
├── src/                    # Source code
│   ├── components/         # React components
│   │   ├── common/         # Shared components
│   │   ├── SystemOverview.js
│   │   ├── ServicesView.js
│   │   ├── TransformationsView.js
│   │   ├── ArchitectureView.js
│   │   ├── RecommendationsView.js
│   │   └── TelemetryView.js
│   ├── context/            # React context for state management
│   │   └── MetamorphicContext.js
│   ├── utils/              # Utility functions
│   │   ├── apiClient.js    # API client for backend services
│   │   └── telemetryUtils.js # Telemetry processing utilities
│   ├── App.js              # Main application component
│   ├── App.css             # Application styles
│   ├── index.js            # Application entry point
│   └── index.css           # Global styles
└── package.json            # npm package configuration
```

## Key Features

### System Overview

The dashboard provides a high-level overview of the entire Metamorphic Architecture system, including:

- Service health and status
- Active transformations
- System resource utilization
- Recent activity

### Service Management

- View all services and their capabilities
- Monitor service health and metrics
- View service dependencies

### Transformation Management

- View and execute transformation plans
- Monitor transformation progress
- View transformation history

### Architecture Visualization

- Interactive visualization of the system architecture
- Different views (dependency, resource, status)
- Service details and metrics

### Recommendations

- View AI-generated recommendations for system improvement
- Apply recommendations to create transformation plans
- Track applied recommendations

### Telemetry Visualization

- Real-time and historical metrics
- Resource utilization charts
- Request and error monitoring
- Transaction traces

## Technologies Used

- React 18
- React Router for navigation
- Recharts for data visualization
- D3.js for architecture visualization
- Context API for state management

## API Communication

The dashboard communicates with the Metamorphic Architecture backend services through a REST API. The API client in `src/utils/apiClient.js` handles all API requests and responses.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.