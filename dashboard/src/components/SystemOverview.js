import React from "react";
import { useNavigate } from "react-router-dom";
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
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from "recharts";

// Component for the System Overview dashboard page
function SystemOverview() {
  const navigate = useNavigate();
  const { systemState, services, transformations, loading } = useMetamorphic();

  if (loading) {
    return <div>Loading system data...</div>;
  }

  // Data for service status chart
  const statusData = [
    {
      name: "Healthy",
      value: services.filter((s) => s.status === "active").length,
    },
    {
      name: "Degraded",
      value: services.filter((s) => s.status === "degraded").length,
    },
    {
      name: "Offline",
      value: services.filter((s) => s.status === "offline").length,
    },
  ].filter((item) => item.value > 0);

  // Data for transformation status chart
  const transformationData = [
    {
      name: "Completed",
      value: transformations.filter((t) => t.status === "completed").length,
    },
    {
      name: "Executing",
      value: transformations.filter((t) => t.status === "executing").length,
    },
    {
      name: "Failed",
      value: transformations.filter((t) => t.status === "failed").length,
    },
  ].filter((item) => item.value > 0);

  // Colors for the charts
  const COLORS = ["#00C49F", "#FFBB28", "#FF8042", "#0088FE"];

  return (
    <div className="system-overview">
      <h1>System Overview</h1>

      {/* Key Metrics Section */}
      <div className="card-grid">
        <div className="card">
          <div className="card-header">Services</div>
          <div className="metric-value">{services.length}</div>
          <button onClick={() => navigate("/services")} className="view-more">
            View All Services
          </button>
        </div>

        <div className="card">
          <div className="card-header">Active Transformations</div>
          <div className="metric-value">
            {transformations.filter((t) => t.status === "executing").length}
          </div>
          <button
            onClick={() => navigate("/transformations")}
            className="view-more"
          >
            View All Transformations
          </button>
        </div>

        <div className="card">
          <div className="card-header">System Health</div>
          <div className="metric-value">
            <span
              className={`status-pill ${
                systemState?.health?.overall || "healthy"
              }`}
            >
              {(systemState?.health?.overall || "healthy").toUpperCase()}
            </span>
          </div>
        </div>

        <div className="card">
          <div className="card-header">Recommendations</div>
          <div className="metric-value">
            {systemState?.recommendation_count || 0}
          </div>
          <button
            onClick={() => navigate("/recommendations")}
            className="view-more"
          >
            View Recommendations
          </button>
        </div>
      </div>

      {/* Charts Section */}
      <div className="card-grid">
        {/* Service Status Chart */}
        <div className="card">
          <div className="card-header">Service Status</div>
          <div style={{ width: "100%", height: 300 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  labelLine={true}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                >
                  {statusData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => [`${value} services`, "Count"]}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Transformation Status Chart */}
        <div className="card">
          <div className="card-header">Transformation Status</div>
          <div style={{ width: "100%", height: 300 }}>
            <ResponsiveContainer>
              <BarChart data={transformationData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" name="Transformations">
                  {transformationData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Activity Timeline */}
        <div className="card full-width-card">
          <div className="card-header">Recent Activity</div>
          <div className="timeline">
            {transformations.slice(0, 5).map((transformation, index) => (
              <div key={index} className="timeline-item">
                <div
                  className={`timeline-status ${transformation.status}`}
                ></div>
                <div className="timeline-content">
                  <h3>{transformation.name}</h3>
                  <p>{transformation.description}</p>
                  <div className="timeline-meta">
                    <span>Status: {transformation.status}</span>
                    <span>
                      {new Date(
                        transformation.updated_at * 1000
                      ).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Additional CSS for this component
const styles = `
  .system-overview h1 {
    margin-bottom: 20px;
    color: var(--dark-color);
  }
  
  .metric-value {
    font-size: 2.5rem;
    font-weight: 600;
    margin: 15px 0;
    color: var(--primary-color);
  }
  
  .view-more {
    display: inline-block;
    padding: 6px 12px;
    background-color: var(--light-color);
    border: none;
    border-radius: 4px;
    color: var(--primary-color);
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .view-more:hover {
    background-color: var(--gray-color);
  }
  
  .status-pill {
    display: inline-block;
    padding: 5px 15px;
    border-radius: 20px;
    font-size: 1rem;
    font-weight: 600;
  }
  
  .status-pill.healthy {
    background-color: var(--success-color);
    color: white;
  }
  
  .status-pill.degraded {
    background-color: var(--warning-color);
    color: var(--text-color);
  }
  
  .status-pill.critical {
    background-color: var(--danger-color);
    color: white;
  }
  
  .timeline {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }
  
  .timeline-item {
    display: flex;
    padding: 10px 0;
    border-bottom: 1px solid var(--gray-color);
  }
  
  .timeline-status {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 15px;
    margin-top: 5px;
  }
  
  .timeline-status.completed {
    background-color: var(--success-color);
  }
  
  .timeline-status.executing {
    background-color: var(--warning-color);
  }
  
  .timeline-status.failed {
    background-color: var(--danger-color);
  }
  
  .timeline-content h3 {
    font-size: 1rem;
    margin-bottom: 5px;
  }
  
  .timeline-content p {
    color: var(--text-color);
    margin-bottom: 5px;
  }
  
  .timeline-meta {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    color: #777;
  }
`;

// Inject the component styles
const styleSheet = document.createElement("style");
styleSheet.type = "text/css";
styleSheet.innerText = styles;
document.head.appendChild(styleSheet);

export default SystemOverview;
