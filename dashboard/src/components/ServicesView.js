import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useMetamorphic } from "../context/MetamorphicContext";

function ServicesView() {
  const { serviceId } = useParams();
  const navigate = useNavigate();
  const { services, loading } = useMetamorphic();
  const [selectedService, setSelectedService] = useState(null);
  const [metrics, setMetrics] = useState({});

  // Handle service selection
  useEffect(() => {
    if (serviceId && services.length > 0) {
      const service = services.find((s) => s.service_id === serviceId);
      setSelectedService(service || null);

      if (service) {
        // Fetch service metrics
        fetchServiceMetrics(service.service_id);
      }
    } else if (services.length > 0 && !serviceId) {
      // No service selected, clear selection
      setSelectedService(null);
    }
  }, [serviceId, services]);

  // Fetch service metrics from API
  const fetchServiceMetrics = async (serviceId) => {
    try {
      const response = await fetch(`/api/metrics/${serviceId}`);
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error("Error fetching service metrics:", error);
    }
  };

  // Handle service selection
  const handleServiceSelect = (service) => {
    navigate(`/services/${service.service_id}`);
  };

  // Get status class for styling
  const getStatusClass = (status) => {
    switch (status) {
      case "active":
        return "status-healthy";
      case "degraded":
        return "status-degraded";
      case "offline":
        return "status-offline";
      default:
        return "status-unknown";
    }
  };

  if (loading) {
    return <div className="loading-message">Loading services...</div>;
  }

  return (
    <div className="services-view">
      <h1>Services</h1>

      <div className="services-container">
        <div className="services-list">
          <div className="list-header">
            <h2>Available Services</h2>
            <div className="service-count">{services.length} services</div>
          </div>

          <div className="service-items">
            {services.map((service) => (
              <div
                key={service.service_id}
                className={`service-item ${
                  selectedService &&
                  selectedService.service_id === service.service_id
                    ? "selected"
                    : ""
                }`}
                onClick={() => handleServiceSelect(service)}
              >
                <div
                  className={`service-status ${getStatusClass(service.status)}`}
                ></div>
                <div className="service-info">
                  <div className="service-name">{service.service_id}</div>
                  <div className="service-endpoint">{service.endpoint}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="service-details">
          {selectedService ? (
            <>
              <div className="detail-header">
                <h2>{selectedService.service_id}</h2>
                <div
                  className={`service-status-badge ${getStatusClass(
                    selectedService.status
                  )}`}
                >
                  {selectedService.status}
                </div>
              </div>

              <div className="detail-cards">
                <div className="detail-card">
                  <h3>Capabilities</h3>
                  <div className="capabilities-list">
                    {selectedService.capabilities.map((capability, index) => (
                      <div key={index} className="capability-tag">
                        {capability}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="detail-card">
                  <h3>Resource Allocation</h3>
                  <div className="resource-metrics">
                    <div className="resource-metric">
                      <span>CPU:</span>
                      <div className="resource-bar">
                        <div
                          className="resource-progress"
                          style={{
                            width: `${
                              (selectedService.resource_allocation.cpu || 0) *
                              100
                            }%`,
                          }}
                        ></div>
                      </div>
                      <span>
                        {selectedService.resource_allocation.cpu?.toFixed(1) ||
                          0}
                      </span>
                    </div>
                    <div className="resource-metric">
                      <span>Memory:</span>
                      <div className="resource-bar">
                        <div
                          className="resource-progress"
                          style={{
                            width: `${
                              (selectedService.resource_allocation.memory ||
                                0) * 100
                            }%`,
                          }}
                        ></div>
                      </div>
                      <span>
                        {selectedService.resource_allocation.memory?.toFixed(
                          1
                        ) || 0}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="detail-card">
                  <h3>Dependencies</h3>
                  {selectedService.dependencies &&
                  selectedService.dependencies.length > 0 ? (
                    <div className="dependencies-list">
                      {selectedService.dependencies.map((dep, index) => (
                        <div
                          key={index}
                          className="dependency-item"
                          onClick={() => navigate(`/services/${dep}`)}
                        >
                          {dep}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-message">No dependencies</div>
                  )}
                </div>

                <div className="detail-card full-width">
                  <h3>Performance Metrics</h3>
                  {Object.keys(metrics).length > 0 ? (
                    <div className="metrics-grid">
                      <div className="metric-box">
                        <div className="metric-value">
                          {metrics.avg_cpu
                            ? (metrics.avg_cpu * 100).toFixed(1)
                            : 0}
                          %
                        </div>
                        <div className="metric-label">CPU Usage</div>
                      </div>
                      <div className="metric-box">
                        <div className="metric-value">
                          {metrics.avg_memory
                            ? (metrics.avg_memory * 100).toFixed(1)
                            : 0}
                          %
                        </div>
                        <div className="metric-label">Memory Usage</div>
                      </div>
                      <div className="metric-box">
                        <div className="metric-value">
                          {metrics.avg_latency?.toFixed(2) || 0}ms
                        </div>
                        <div className="metric-label">Avg Latency</div>
                      </div>
                      <div className="metric-box">
                        <div className="metric-value">
                          {metrics.total_requests || 0}
                        </div>
                        <div className="metric-label">Requests</div>
                      </div>
                      <div className="metric-box">
                        <div className="metric-value">
                          {metrics.error_rate
                            ? (metrics.error_rate * 100).toFixed(2)
                            : 0}
                          %
                        </div>
                        <div className="metric-label">Error Rate</div>
                      </div>
                    </div>
                  ) : (
                    <div className="empty-message">No metrics available</div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="no-selection">
              <div className="empty-state">
                <i className="empty-icon">📊</i>
                <h3>Select a service to view details</h3>
                <p>
                  Choose a service from the list to view its capabilities,
                  resources, and metrics.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Additional styles
const styles = `
  .services-view h1 {
    margin-bottom: 20px;
    color: var(--dark-color);
  }
  
  .services-container {
    display: flex;
    gap: 20px;
    height: calc(100vh - 200px);
  }
  
  .services-list {
    width: 300px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
  }
  
  .list-header {
    padding: 15px;
    border-bottom: 1px solid var(--gray-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .list-header h2 {
    font-size: 1.2rem;
    margin: 0;
  }
  
  .service-count {
    font-size: 0.9rem;
    color: #777;
  }
  
  .service-items {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
  }
  
  .service-item {
    display: flex;
    align-items: center;
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .service-item:hover {
    background-color: var(--gray-color);
  }
  
  .service-item.selected {
    background-color: var(--primary-color);
    color: white;
  }
  
  .service-item.selected .service-endpoint {
    color: rgba(255, 255, 255, 0.8);
  }
  
  .service-status {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 12px;
  }
  
  .status-healthy {
    background-color: var(--success-color);
  }
  
  .status-degraded {
    background-color: var(--warning-color);
  }
  
  .status-offline {
    background-color: var(--danger-color);
  }
  
  .status-unknown {
    background-color: #999;
  }
  
  .service-info {
    flex: 1;
  }
  
  .service-name {
    font-weight: 500;
    margin-bottom: 4px;
  }
  
  .service-endpoint {
    font-size: 0.85rem;
    color: #666;
  }
  
  .service-details {
    flex: 1;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    padding: 20px;
    overflow-y: auto;
  }
  
  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .detail-header h2 {
    margin: 0;
    font-size: 1.5rem;
  }
  
  .service-status-badge {
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 500;
    text-transform: uppercase;
  }
  
  .status-healthy {
    background-color: var(--success-color);
    color: white;
  }
  
  .status-degraded {
    background-color: var(--warning-color);
    color: var(--text-color);
  }
  
  .status-offline {
    background-color: var(--danger-color);
    color: white;
  }
  
  .detail-cards {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
  }
  
  .detail-card {
    background: #f9f9f9;
    border-radius: 6px;
    padding: 15px;
  }
  
  .detail-card.full-width {
    grid-column: span 2;
  }
  
  .detail-card h3 {
    margin-top: 0;
    margin-bottom: 15px;
    font-size: 1.1rem;
    color: var(--dark-color);
  }
  
  .capabilities-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .capability-tag {
    background: var(--primary-color);
    color: white;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 0.9rem;
  }
  
  .resource-metrics {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .resource-metric {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .resource-bar {
    flex: 1;
    height: 8px;
    background: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
  }
  
  .resource-progress {
    height: 100%;
    background: var(--primary-color);
  }
  
  .dependencies-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .dependency-item {
    background: #eee;
    padding: 8px 12px;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .dependency-item:hover {
    background: var(--primary-color);
    color: white;
  }
  
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 15px;
  }
  
  .metric-box {
    background: white;
    border-radius: 6px;
    padding: 15px;
    text-align: center;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
  }
  
  .metric-value {
    font-size: 1.8rem;
    font-weight: 600;
    color: var(--primary-color);
    margin-bottom: 5px;
  }
  
  .metric-label {
    font-size: 0.9rem;
    color: #666;
  }
  
  .no-selection {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .empty-state {
    text-align: center;
    padding: 40px;
  }
  
  .empty-icon {
    font-size: 3rem;
    margin-bottom: 15px;
    display: block;
  }
  
  .empty-message {
    color: #777;
    font-style: italic;
  }
  
  @media (max-width: 768px) {
    .services-container {
      flex-direction: column;
      height: auto;
    }
    
    .services-list {
      width: 100%;
    }
    
    .detail-cards {
      grid-template-columns: 1fr;
    }
    
    .detail-card.full-width {
      grid-column: span 1;
    }
    
    .metrics-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }
`;

// Inject the component styles
const styleSheet = document.createElement("style");
styleSheet.type = "text/css";
styleSheet.innerText = styles;
document.head.appendChild(styleSheet);

export default ServicesView;
