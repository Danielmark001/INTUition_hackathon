import React, { useState, useEffect } from "react";
import { useMetamorphic } from "../context/MetamorphicContext";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";

function TelemetryView() {
  const { services, loading } = useMetamorphic();
  const [selectedService, setSelectedService] = useState(null);
  const [timeRange, setTimeRange] = useState("1h");
  const [telemetryData, setTelemetryData] = useState([]);
  const [transactionTraces, setTransactionTraces] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Load initial data when component mounts
  useEffect(() => {
    if (services.length > 0) {
      setSelectedService(services[0].service_id);
    }
  }, [services]);

  // Fetch telemetry when service or time range changes
  useEffect(() => {
    if (selectedService) {
      fetchServiceTelemetry(selectedService, timeRange);
      fetchTransactionTraces();
    }
  }, [selectedService, timeRange]);

  // Fetch telemetry data for a service
  const fetchServiceTelemetry = async (serviceId, range) => {
    try {
      setIsLoading(true);

      // Convert time range to seconds
      const timeWindowMap = {
        "1h": 3600,
        "3h": 10800,
        "12h": 43200,
        "24h": 86400,
      };

      const timeWindow = timeWindowMap[range] || 3600;

      const response = await fetch(
        `/api/metrics/${serviceId}?time_window=${timeWindow}`
      );
      const data = await response.json();

      // Process the data for charts
      const processedData = data.map((point) => ({
        timestamp: new Date(point.timestamp * 1000).toLocaleString(),
        rawTimestamp: point.timestamp,
        cpuUsage: (point.cpu_usage * 100).toFixed(1),
        memoryUsage: (point.memory_usage * 100).toFixed(1),
        latency: point.latency,
        requestCount: point.request_count,
        errorRate: (point.error_rate * 100).toFixed(2) || 0,
      }));

      setTelemetryData(processedData);
    } catch (error) {
      console.error("Error fetching telemetry:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch recent transaction traces
  const fetchTransactionTraces = async () => {
    try {
      const response = await fetch("/api/data/transactions/recent");
      const data = await response.json();
      setTransactionTraces(data);
    } catch (error) {
      console.error("Error fetching transaction traces:", error);
    }
  };

  // Handle service selection
  const handleServiceChange = (event) => {
    setSelectedService(event.target.value);
  };

  // Handle time range selection
  const handleTimeRangeChange = (event) => {
    setTimeRange(event.target.value);
  };

  // Format timestamp for tooltip
  const formatXAxis = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  if (loading) {
    return <div className="loading-message">Loading telemetry data...</div>;
  }

  return (
    <div className="telemetry-view">
      <h1>System Telemetry</h1>

      <div className="telemetry-controls">
        <div className="control-group">
          <label>Service:</label>
          <select value={selectedService || ""} onChange={handleServiceChange}>
            {services.map((service) => (
              <option key={service.service_id} value={service.service_id}>
                {service.service_id}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Time Range:</label>
          <select value={timeRange} onChange={handleTimeRangeChange}>
            <option value="1h">Last Hour</option>
            <option value="3h">Last 3 Hours</option>
            <option value="12h">Last 12 Hours</option>
            <option value="24h">Last 24 Hours</option>
          </select>
        </div>
      </div>

      <div className="telemetry-container">
        <div className="chart-container">
          {isLoading ? (
            <div className="loading-charts">Loading telemetry data...</div>
          ) : telemetryData.length > 0 ? (
            <>
              <div className="chart-card">
                <h2>Resource Utilization</h2>
                <div className="chart-area">
                  <ResponsiveContainer width="100%" height={240}>
                    <LineChart data={telemetryData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="timestamp"
                        tickFormatter={(tick) => {
                          const date = new Date(tick);
                          return (
                            date.getHours() +
                            ":" +
                            date.getMinutes().toString().padStart(2, "0")
                          );
                        }}
                      />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="cpuUsage"
                        name="CPU (%)"
                        stroke="#8884d8"
                        activeDot={{ r: 8 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="memoryUsage"
                        name="Memory (%)"
                        stroke="#82ca9d"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="chart-card">
                <h2>Request Throughput</h2>
                <div className="chart-area">
                  <ResponsiveContainer width="100%" height={240}>
                    <AreaChart data={telemetryData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="timestamp" />
                      <YAxis />
                      <Tooltip />
                      <Area
                        type="monotone"
                        dataKey="requestCount"
                        name="Requests"
                        stroke="#4a90e2"
                        fill="#4a90e2"
                        fillOpacity={0.2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="chart-card">
                <h2>Response Latency</h2>
                <div className="chart-area">
                  <ResponsiveContainer width="100%" height={240}>
                    <LineChart data={telemetryData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="timestamp" />
                      <YAxis />
                      <Tooltip />
                      <Line
                        type="monotone"
                        dataKey="latency"
                        name="Latency (ms)"
                        stroke="#ff7f0e"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="chart-card">
                <h2>Error Rate</h2>
                <div className="chart-area">
                  <ResponsiveContainer width="100%" height={240}>
                    <LineChart data={telemetryData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="timestamp" />
                      <YAxis />
                      <Tooltip />
                      <Line
                        type="monotone"
                        dataKey="errorRate"
                        name="Error Rate (%)"
                        stroke="#ff6b6b"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          ) : (
            <div className="no-data">
              <div className="empty-state">
                <i className="empty-icon">📊</i>
                <h3>No telemetry data available</h3>
                <p>
                  There is no telemetry data for the selected service and time
                  range.
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="traces-container">
          <h2>Recent Transaction Traces</h2>

          {transactionTraces.length > 0 ? (
            <div className="traces-list">
              {transactionTraces.map((trace, index) => (
                <div key={index} className="trace-item">
                  <div className="trace-header">
                    <div className="trace-id">
                      {trace.transaction_id.substring(0, 8)}...
                    </div>
                    <div className="trace-time">
                      {new Date(trace.start_time * 1000).toLocaleTimeString()}
                    </div>
                  </div>

                  <div className="trace-services">
                    {trace.services.map((service, i) => (
                      <div key={i} className="trace-service">
                        {service}
                        {i < trace.services.length - 1 && (
                          <span className="trace-arrow">→</span>
                        )}
                      </div>
                    ))}
                  </div>

                  <div className="trace-metrics">
                    <div className="trace-metric">
                      <span className="metric-label">Duration:</span>
                      <span className="metric-value">
                        {trace.total_latency.toFixed(1)}ms
                      </span>
                    </div>
                    <div className="trace-metric">
                      <span className="metric-label">Spans:</span>
                      <span className="metric-value">{trace.spans.length}</span>
                    </div>
                  </div>

                  <div className="trace-spans">
                    {trace.spans.slice(0, 3).map((span, i) => (
                      <div key={i} className="trace-span">
                        <div className="span-service">{span.service_id}</div>
                        <div className="span-latency">
                          {span.latency.toFixed(1)}ms
                        </div>
                      </div>
                    ))}
                    {trace.spans.length > 3 && (
                      <div className="more-spans">
                        +{trace.spans.length - 3} more spans
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-traces">
              <p>No recent transaction traces available.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Additional styles
const styles = `
  .telemetry-view h1 {
    margin-bottom: 20px;
    color: var(--dark-color);
  }
  
  .telemetry-controls {
    display: flex;
    gap: 20px;
    margin-bottom: 20px;
    background: white;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  .control-group {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .control-group label {
    font-weight: 500;
  }
  
  .control-group select {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: white;
  }
  
  .telemetry-container {
    display: flex;
    gap: 20px;
  }
  
  .chart-container {
    flex: 3;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }
  
  .traces-container {
    flex: 1;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    padding: 20px;
    overflow-y: auto;
    max-height: calc(100vh - 250px);
  }
  
  .chart-card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    padding: 20px;
  }
  
  .chart-card h2 {
    margin-top: 0;
    margin-bottom: 15px;
    font-size: 1.2rem;
    color: var(--dark-color);
  }
  
  .chart-area {
    height: 240px;
  }
  
  .loading-charts {
    grid-column: span 2;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 300px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    color: #666;
    font-style: italic;
  }
  
  .no-data {
    grid-column: span 2;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px;
  }
  
  .empty-state {
    text-align: center;
  }
  
  .empty-icon {
    font-size: 3rem;
    margin-bottom: 15px;
    display: block;
  }
  
  .empty-state h3 {
    margin-bottom: 10px;
  }
  
  .traces-container h2 {
    margin-top: 0;
    margin-bottom: 20px;
    font-size: 1.2rem;
    color: var(--dark-color);
  }
  
  .traces-list {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }
  
  .trace-item {
    background: #f9f9f9;
    border-radius: 6px;
    padding: 12px;
  }
  
  .trace-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
  }
  
  .trace-id {
    font-family: monospace;
    font-weight: 500;
  }
  
  .trace-time {
    font-size: 0.85rem;
    color: #666;
  }
  
  .trace-services {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-bottom: 10px;
  }
  
  .trace-service {
    display: flex;
    align-items: center;
    font-size: 0.9rem;
  }
  
  .trace-arrow {
    margin: 0 5px;
    color: #999;
  }
  
  .trace-metrics {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
    padding-bottom: 10px;
    border-bottom: 1px solid #eee;
  }
  
  .trace-metric {
    display: flex;
    flex-direction: column;
  }
  
  .metric-label {
    font-size: 0.8rem;
    color: #666;
  }
  
  .metric-value {
    font-weight: 500;
  }
  
  .trace-spans {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  
  .trace-span {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    padding: 4px 0;
  }
  
  .span-service {
    color: var(--primary-color);
  }
  
  .span-latency {
    font-family: monospace;
  }
  
  .more-spans {
    text-align: center;
    font-size: 0.8rem;
    color: #666;
    padding: 5px 0;
  }
  
  .empty-traces {
    padding: 20px 0;
    text-align: center;
    color: #666;
    font-style: italic;
  }
  
  @media (max-width: 1200px) {
    .telemetry-container {
      flex-direction: column;
    }
    
    .traces-container {
      max-height: none;
    }
  }
  
  @media (max-width: 768px) {
    .telemetry-controls {
      flex-direction: column;
      gap: 10px;
    }
    
    .chart-container {
      grid-template-columns: 1fr;
    }
    
    .loading-charts {
      grid-column: span 1;
    }
    
    .no-data {
      grid-column: span 1;
    }
  }
`;

// Inject the component styles
const styleSheet = document.createElement("style");
styleSheet.type = "text/css";
styleSheet.innerText = styles;
document.head.appendChild(styleSheet);

export default TelemetryView;
