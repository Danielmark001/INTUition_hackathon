import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import * as d3 from "d3";

// Styles
const styles = {
  container: {
    fontFamily: "Inter, sans-serif",
    padding: "20px",
    background: "#f5f7fa",
    minHeight: "100vh",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px",
  },
  title: {
    fontSize: "24px",
    fontWeight: "bold",
    color: "#2a3f5f",
  },
  refreshButton: {
    padding: "8px 16px",
    background: "#4a90e2",
    color: "white",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(450px, 1fr))",
    gap: "20px",
    marginBottom: "20px",
  },
  card: {
    background: "white",
    borderRadius: "8px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
    padding: "20px",
  },
  cardHeader: {
    fontSize: "18px",
    fontWeight: "bold",
    marginBottom: "15px",
    color: "#2a3f5f",
  },
  fullWidthCard: {
    gridColumn: "1 / -1",
    background: "white",
    borderRadius: "8px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
    padding: "20px",
  },
  serviceGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
    gap: "15px",
  },
  serviceCard: {
    background: "#f0f5ff",
    borderRadius: "6px",
    padding: "15px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
  },
  serviceName: {
    fontWeight: "bold",
    marginBottom: "8px",
  },
  serviceStatus: {
    display: "flex",
    alignItems: "center",
    marginBottom: "5px",
  },
  statusIndicator: {
    width: "10px",
    height: "10px",
    borderRadius: "50%",
    marginRight: "8px",
  },
  metricRow: {
    display: "flex",
    justifyContent: "space-between",
    margin: "3px 0",
    fontSize: "14px",
  },
  metricLabel: {
    color: "#666",
  },
  metricValue: {
    fontWeight: "500",
  },
  transformationRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "10px 0",
    borderBottom: "1px solid #eee",
  },
  transformationName: {
    fontWeight: "500",
  },
  statusBadge: {
    padding: "4px 8px",
    borderRadius: "4px",
    fontSize: "12px",
    fontWeight: "500",
  },
  patternCard: {
    display: "flex",
    background: "#f9f9f9",
    padding: "12px",
    borderRadius: "6px",
    marginBottom: "10px",
    boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
  },
  patternIcon: {
    marginRight: "15px",
    color: "#4a90e2",
    fontSize: "24px",
  },
  patternContent: {
    flex: 1,
  },
  patternTitle: {
    fontWeight: "500",
    marginBottom: "5px",
  },
  patternDescription: {
    fontSize: "14px",
    color: "#666",
    marginBottom: "8px",
  },
  recommendationButton: {
    padding: "4px 8px",
    background: "#f0f5ff",
    color: "#4a90e2",
    border: "1px solid #4a90e2",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "12px",
  },
  architectureView: {
    height: "400px",
    border: "1px solid #ddd",
    borderRadius: "6px",
    overflow: "hidden",
  },
};

// Colors
const COLORS = [
  "#0088FE",
  "#00C49F",
  "#FFBB28",
  "#FF8042",
  "#A28DFF",
  "#FF6E76",
];
const STATUS_COLORS = {
  healthy: "#00C49F",
  warning: "#FFBB28",
  critical: "#FF8042",
  inactive: "#B8B8B8",
};

// Mock API calls (would be real API calls in production)
const fetchDashboardData = async () => {
  // In a real application, this would call your actual API
  // For demo purposes, we'll simulate API data

  // Simulate API latency
  await new Promise((resolve) => setTimeout(resolve, 500));

  return {
    current_state: {
      version: 3,
      services: {
        "user-service": {
          status: "active",
          capabilities: ["user_management", "user_authentication"],
          resource_allocation: { cpu: 1.2, memory: 1.5 },
        },
        "order-service": {
          status: "active",
          capabilities: ["order_management", "inventory_check"],
          resource_allocation: { cpu: 1.0, memory: 1.3 },
        },
        "payment-service": {
          status: "active",
          capabilities: ["payment_processing", "fraud_detection"],
          resource_allocation: { cpu: 0.8, memory: 1.0 },
        },
        "notification-service": {
          status: "active",
          capabilities: ["email_notification", "push_notification"],
          resource_allocation: { cpu: 0.5, memory: 0.8 },
        },
      },
      routing: {
        default_routes: {
          "/users": "user-service",
          "/orders": "order-service",
          "/payments": "payment-service",
          "/notifications": "notification-service",
        },
      },
    },
    service_metrics: {
      "user-service": {
        cpu: 0.65,
        memory: 0.72,
        requests: 145,
        errors: 2,
        latency: 48,
      },
      "order-service": {
        cpu: 0.58,
        memory: 0.63,
        requests: 98,
        errors: 1,
        latency: 65,
      },
      "payment-service": {
        cpu: 0.3,
        memory: 0.42,
        requests: 56,
        errors: 0,
        latency: 87,
      },
      "notification-service": {
        cpu: 0.25,
        memory: 0.35,
        requests: 32,
        errors: 0,
        latency: 22,
      },
    },
    transformation_stats: {
      total: 5,
      active: 1,
      completed: 3,
      failed: 1,
      recent: [
        {
          id: "t1",
          name: "Merge User and Auth Services",
          status: "completed",
          created_at: Date.now() - 86400000,
          updated_at: Date.now() - 84600000,
        },
        {
          id: "t2",
          name: "Optimize Payment Processing",
          status: "executing",
          created_at: Date.now() - 3600000,
          updated_at: Date.now() - 1800000,
        },
        {
          id: "t3",
          name: "Scale Down Notification Service",
          status: "failed",
          created_at: Date.now() - 259200000,
          updated_at: Date.now() - 258000000,
        },
      ],
    },
    pattern_count: 6,
    recommendation_count: 4,
    system_health: {
      overall: "healthy",
      services: {
        "user-service": "healthy",
        "order-service": "healthy",
        "payment-service": "healthy",
        "notification-service": "healthy",
      },
    },
  };
};

const fetchRecommendations = async () => {
  // Simulate API latency
  await new Promise((resolve) => setTimeout(resolve, 300));

  return [
    {
      id: "rec1",
      type: "service_coupling",
      description:
        "Merge user-service and notification-service due to high coupling (83% co-occurrence)",
      confidence: 0.83,
      impact: "medium",
    },
    {
      id: "rec2",
      type: "resource_optimization",
      description:
        "Reduce resources for payment-service (CPU utilization below 40%)",
      confidence: 0.91,
      impact: "low",
    },
    {
      id: "rec3",
      type: "architectural",
      description:
        "Split order-service into order-management and inventory-service",
      confidence: 0.72,
      impact: "high",
    },
    {
      id: "rec4",
      type: "performance",
      description:
        "Optimize database queries in order-service to reduce latency",
      confidence: 0.85,
      impact: "medium",
    },
  ];
};

const fetchHistoricalMetrics = async (serviceId) => {
  // Simulate API latency
  await new Promise((resolve) => setTimeout(resolve, 200));

  // Generate some random historical data
  const now = Date.now();
  const data = [];

  for (let i = 0; i < 24; i++) {
    data.push({
      timestamp: new Date(now - (23 - i) * 3600000).toISOString(),
      cpu: 0.2 + Math.random() * 0.6,
      memory: 0.3 + Math.random() * 0.5,
      requests: Math.floor(Math.random() * 200),
      latency: 20 + Math.random() * 100,
    });
  }

  return data;
};

const applyRecommendation = async (recommendationId) => {
  // Simulate API latency
  await new Promise((resolve) => setTimeout(resolve, 800));

  // This would call your API to create a transformation plan based on the recommendation
  return {
    success: true,
    plan_id: "auto_plan_" + Date.now(),
  };
};

// Dashboard Components
const App = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [historicalMetrics, setHistoricalMetrics] = useState({});
  const [selectedService, setSelectedService] = useState(null);
  const [applyingRecommendation, setApplyingRecommendation] = useState(null);

  // Load dashboard data
  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchDashboardData();
      setDashboardData(data);

      const recs = await fetchRecommendations();
      setRecommendations(recs);

      // Load initial historical metrics for the first service
      if (data && data.current_state && data.current_state.services) {
        const serviceIds = Object.keys(data.current_state.services);
        if (serviceIds.length > 0) {
          const firstServiceId = serviceIds[0];
          const metrics = await fetchHistoricalMetrics(firstServiceId);
          setHistoricalMetrics({
            [firstServiceId]: metrics,
          });
          setSelectedService(firstServiceId);
        }
      }
    } catch (error) {
      console.error("Error loading dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    // Set up automatic refresh every 30 seconds
    const interval = setInterval(() => {
      loadData();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const handleServiceSelect = async (serviceId) => {
    if (serviceId === selectedService) return;

    setSelectedService(serviceId);

    // Load historical metrics if not already loaded
    if (!historicalMetrics[serviceId]) {
      try {
        const metrics = await fetchHistoricalMetrics(serviceId);
        setHistoricalMetrics((prev) => ({
          ...prev,
          [serviceId]: metrics,
        }));
      } catch (error) {
        console.error(`Error loading metrics for ${serviceId}:`, error);
      }
    }
  };

  const handleApplyRecommendation = async (recommendationId) => {
    setApplyingRecommendation(recommendationId);
    try {
      const result = await applyRecommendation(recommendationId);
      if (result.success) {
        // Show success notification or update UI
        alert(
          `Recommendation applied! Transformation plan created: ${result.plan_id}`
        );
        // Refresh data
        loadData();
      }
    } catch (error) {
      console.error("Error applying recommendation:", error);
      alert("Failed to apply recommendation. See console for details.");
    } finally {
      setApplyingRecommendation(null);
    }
  };

  if (loading && !dashboardData) {
    return (
      <div style={styles.container}>
        <div style={{ textAlign: "center", padding: "100px 0" }}>
          <h2>Loading Metamorphic Architecture Dashboard...</h2>
          <p>Please wait while we gather system information</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Metamorphic Architecture Dashboard</h1>
        <button style={styles.refreshButton} onClick={loadData}>
          Refresh Data
        </button>
      </div>

      {/* System Overview Cards */}
      <div style={styles.grid}>
        <div style={styles.card}>
          <h2 style={styles.cardHeader}>System Health</h2>
          <div>
            <div
              style={{
                ...styles.statusIndicator,
                width: "20px",
                height: "20px",
                display: "inline-block",
                background:
                  STATUS_COLORS[
                    dashboardData?.system_health?.overall || "healthy"
                  ],
              }}
            ></div>
            <span
              style={{
                fontSize: "18px",
                marginLeft: "10px",
                fontWeight: "500",
              }}
            >
              {dashboardData?.system_health?.overall === "healthy"
                ? "Healthy"
                : "Needs Attention"}
            </span>

            <div style={{ marginTop: "20px" }}>
              <SystemHealthPieChart data={dashboardData} />
            </div>
          </div>
        </div>

        <div style={styles.card}>
          <h2 style={styles.cardHeader}>Transformations</h2>
          <div>
            <TransformationStatusChart
              data={dashboardData?.transformation_stats}
            />
            <div style={{ marginTop: "15px" }}>
              <h3 style={{ fontSize: "16px", marginBottom: "10px" }}>
                Recent Transformations
              </h3>
              {dashboardData?.transformation_stats?.recent.map(
                (transformation) => (
                  <div key={transformation.id} style={styles.transformationRow}>
                    <div style={styles.transformationName}>
                      {transformation.name}
                    </div>
                    <div
                      style={{
                        ...styles.statusBadge,
                        background:
                          transformation.status === "completed"
                            ? "#e6f7f2"
                            : transformation.status === "executing"
                            ? "#fff8e6"
                            : "#ffeded",
                        color:
                          transformation.status === "completed"
                            ? "#00a36e"
                            : transformation.status === "executing"
                            ? "#d89600"
                            : "#d84040",
                      }}
                    >
                      {transformation.status}
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Services Section */}
      <div style={styles.fullWidthCard}>
        <h2 style={styles.cardHeader}>Services</h2>
        <div style={styles.serviceGrid}>
          {dashboardData &&
            dashboardData.current_state &&
            dashboardData.current_state.services &&
            Object.entries(dashboardData.current_state.services).map(
              ([serviceId, service]) => {
                const metrics = dashboardData.service_metrics[serviceId] || {};
                const health =
                  dashboardData.system_health.services[serviceId] || "healthy";

                return (
                  <div
                    key={serviceId}
                    style={{
                      ...styles.serviceCard,
                      border:
                        selectedService === serviceId
                          ? "2px solid #4a90e2"
                          : "none",
                      cursor: "pointer",
                    }}
                    onClick={() => handleServiceSelect(serviceId)}
                  >
                    <div style={styles.serviceName}>{serviceId}</div>
                    <div style={styles.serviceStatus}>
                      <div
                        style={{
                          ...styles.statusIndicator,
                          background: STATUS_COLORS[health],
                        }}
                      ></div>
                      <span>{health}</span>
                    </div>

                    <div style={styles.metricRow}>
                      <span style={styles.metricLabel}>CPU:</span>
                      <span style={styles.metricValue}>
                        {(metrics.cpu * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div style={styles.metricRow}>
                      <span style={styles.metricLabel}>Memory:</span>
                      <span style={styles.metricValue}>
                        {(metrics.memory * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div style={styles.metricRow}>
                      <span style={styles.metricLabel}>Requests:</span>
                      <span style={styles.metricValue}>
                        {metrics.requests || 0}
                      </span>
                    </div>
                    <div style={styles.metricRow}>
                      <span style={styles.metricLabel}>Latency:</span>
                      <span style={styles.metricValue}>
                        {metrics.latency || 0}ms
                      </span>
                    </div>
                  </div>
                );
              }
            )}
        </div>
      </div>

      {/* Service Metrics Chart */}
      <div style={styles.fullWidthCard}>
        <h2 style={styles.cardHeader}>
          Service Metrics: {selectedService || "Select a service"}
        </h2>
        {selectedService && historicalMetrics[selectedService] ? (
          <div style={{ height: "300px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={historicalMetrics[selectedService]}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(timestamp) => {
                    const date = new Date(timestamp);
                    return `${date.getHours()}:00`;
                  }}
                />
                <YAxis />
                <Tooltip
                  formatter={(value, name) => {
                    if (name === "cpu" || name === "memory") {
                      return [(value * 100).toFixed(1) + "%", name];
                    }
                    return [value, name];
                  }}
                  labelFormatter={(timestamp) => {
                    const date = new Date(timestamp);
                    return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="cpu"
                  stroke="#8884d8"
                  name="CPU Usage"
                />
                <Line
                  type="monotone"
                  dataKey="memory"
                  stroke="#82ca9d"
                  name="Memory Usage"
                />
                <Line
                  type="monotone"
                  dataKey="requests"
                  stroke="#ffc658"
                  name="Requests"
                  yAxisId={1}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div style={{ padding: "40px 0", textAlign: "center" }}>
            {selectedService
              ? "Loading metrics..."
              : "Select a service to view metrics"}
          </div>
        )}
      </div>

      {/* Architecture View */}
      <div style={styles.fullWidthCard}>
        <h2 style={styles.cardHeader}>Architecture View</h2>
        <div style={styles.architectureView}>
          <ArchitectureGraph data={dashboardData} />
        </div>
      </div>

      {/* Recommendations */}
      <div style={styles.fullWidthCard}>
        <h2 style={styles.cardHeader}>Recommendations</h2>
        {recommendations.length > 0 ? (
          <div>
            {recommendations.map((recommendation) => (
              <div key={recommendation.id} style={styles.patternCard}>
                <div style={styles.patternIcon}>
                  {recommendation.type === "service_coupling"
                    ? "🔄"
                    : recommendation.type === "resource_optimization"
                    ? "📊"
                    : recommendation.type === "architectural"
                    ? "🏗️"
                    : "⚡"}
                </div>
                <div style={styles.patternContent}>
                  <div style={styles.patternTitle}>
                    {recommendation.description}
                  </div>
                  <div style={styles.patternDescription}>
                    Confidence: {(recommendation.confidence * 100).toFixed(0)}%
                    | Impact:{" "}
                    {recommendation.impact.charAt(0).toUpperCase() +
                      recommendation.impact.slice(1)}
                  </div>
                  <button
                    style={styles.recommendationButton}
                    onClick={() => handleApplyRecommendation(recommendation.id)}
                    disabled={applyingRecommendation === recommendation.id}
                  >
                    {applyingRecommendation === recommendation.id
                      ? "Applying..."
                      : "Apply Recommendation"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ padding: "20px 0", textAlign: "center" }}>
            No recommendations available at this time.
          </div>
        )}
      </div>
    </div>
  );
};

// Component for System Health Pie Chart
const SystemHealthPieChart = ({ data }) => {
  if (!data || !data.current_state || !data.current_state.services) {
    return <div>No data available</div>;
  }

  // Count services by status
  const serviceCount = Object.keys(data.current_state.services).length;
  const healthCounts = {
    healthy: 0,
    warning: 0,
    critical: 0,
    inactive: 0,
  };

  Object.entries(data.system_health.services).forEach(([_, status]) => {
    healthCounts[status] = (healthCounts[status] || 0) + 1;
  });

  const chartData = Object.entries(healthCounts)
    .filter(([_, count]) => count > 0)
    .map(([status, count]) => ({
      name: status.charAt(0).toUpperCase() + status.slice(1),
      value: count,
    }));

  return (
    <div style={{ width: "100%", height: 200 }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
            label={({ name, percent }) =>
              `${name} ${(percent * 100).toFixed(0)}%`
            }
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={STATUS_COLORS[entry.name.toLowerCase()]}
              />
            ))}
          </Pie>
          <Tooltip formatter={(value) => [`${value} services`, "Count"]} />
        </PieChart>
      </ResponsiveContainer>
      <div style={{ textAlign: "center", marginTop: "10px" }}>
        {serviceCount} Total Services
      </div>
    </div>
  );
};

// Component for Transformation Status Chart
const TransformationStatusChart = ({ data }) => {
  if (!data) {
    return <div>No transformation data available</div>;
  }

  const chartData = [
    { name: "Completed", value: data.completed },
    { name: "Active", value: data.active },
    { name: "Failed", value: data.failed },
  ];

  const colors = ["#00C49F", "#FFBB28", "#FF8042"];

  return (
    <div style={{ width: "100%", height: 200 }}>
      <ResponsiveContainer>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#8884d8">
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={colors[index % colors.length]}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

// Component for Architecture Graph Visualization
const ArchitectureGraph = ({ data }) => {
  const svgRef = React.useRef(null);

  useEffect(() => {
    if (!data || !data.current_state || !data.current_state.services) return;

    const services = Object.keys(data.current_state.services).map(
      (serviceId) => ({
        id: serviceId,
        group: 1,
      })
    );

    // Create links based on data patterns and routing
    const links = [];

    // Add some example links
    if (services.length >= 2) {
      for (let i = 1; i < services.length; i++) {
        links.push({
          source: services[0].id,
          target: services[i].id,
          value: 1,
        });
      }

      // Add some cross-links
      if (services.length >= 4) {
        links.push({
          source: services[1].id,
          target: services[2].id,
          value: 1,
        });
        links.push({
          source: services[2].id,
          target: services[3].id,
          value: 1,
        });
      }
    }

    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const simulation = d3
      .forceSimulation(services)
      .force(
        "link",
        d3
          .forceLink(links)
          .id((d) => d.id)
          .distance(100)
      )
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width / 2, height / 2));

    const link = svg
      .append("g")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke-width", (d) => Math.sqrt(d.value));

    const serviceColors = d3
      .scaleOrdinal()
      .domain([...new Set(services.map((d) => d.group))])
      .range(["#4a90e2", "#50C878", "#FF6348", "#FDCB6E"]);

    const node = svg
      .append("g")
      .selectAll("g")
      .data(services)
      .join("g")
      .call(drag(simulation));

    node
      .append("circle")
      .attr("r", 20)
      .attr("fill", (d) => serviceColors(d.group))
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5);

    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", 30)
      .text((d) => d.id)
      .style("font-size", "10px");

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    function drag(simulation) {
      function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      }

      function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      }

      function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      }

      return d3
        .drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
    }
  }, [data]);

  return <svg ref={svgRef} width="100%" height="100%"></svg>;
};

export default App;


