import React, { useState } from "react";
import { Routes, Route, NavLink, useLocation } from "react-router-dom";
import { useMetamorphic } from "./context/MetamorphicContext";
import "./App.css";

// Import dashboard components
import SystemOverview from "./components/SystemOverview";
import ServicesView from "./components/ServicesView";
import TransformationsView from "./components/TransformationsView";
import ArchitectureView from "./components/ArchitectureView";
import RecommendationsView from "./components/RecommendationsView";
import TelemetryView from "./components/TelemetryView";
import LoadingSpinner from "./components/common/LoadingSpinner";

function App() {
  const location = useLocation();
  const { loading, systemState } = useMetamorphic();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <button className="sidebar-toggle" onClick={toggleSidebar}>
            ☰
          </button>
          <h1>Metamorphic Architecture</h1>
        </div>
        <div className="header-right">
          {systemState && (
            <div className="system-status">
              <span
                className={`status-indicator ${
                  systemState.health?.overall || "healthy"
                }`}
              ></span>
              <span>
                System Status:{" "}
                {(systemState.health?.overall || "healthy").toUpperCase()}
              </span>
            </div>
          )}
        </div>
      </header>

      <div className="app-content">
        {/* Sidebar Navigation */}
        <aside className={`app-sidebar ${sidebarOpen ? "open" : "closed"}`}>
          <nav>
            <ul>
              <li>
                <NavLink
                  to="/"
                  className={({ isActive }) => (isActive ? "active" : "")}
                >
                  Dashboard
                </NavLink>
              </li>
              <li>
                <NavLink
                  to="/services"
                  className={({ isActive }) => (isActive ? "active" : "")}
                >
                  Services
                </NavLink>
              </li>
              <li>
                <NavLink
                  to="/transformations"
                  className={({ isActive }) => (isActive ? "active" : "")}
                >
                  Transformations
                </NavLink>
              </li>
              <li>
                <NavLink
                  to="/architecture"
                  className={({ isActive }) => (isActive ? "active" : "")}
                >
                  Architecture
                </NavLink>
              </li>
              <li>
                <NavLink
                  to="/recommendations"
                  className={({ isActive }) => (isActive ? "active" : "")}
                >
                  Recommendations
                </NavLink>
              </li>
              <li>
                <NavLink
                  to="/telemetry"
                  className={({ isActive }) => (isActive ? "active" : "")}
                >
                  Telemetry
                </NavLink>
              </li>
            </ul>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="main-content">
          {loading ? (
            <LoadingSpinner message="Loading system data..." />
          ) : (
            <Routes>
              <Route path="/" element={<SystemOverview />} />
              <Route path="/services" element={<ServicesView />} />
              <Route path="/services/:serviceId" element={<ServicesView />} />
              <Route
                path="/transformations"
                element={<TransformationsView />}
              />
              <Route
                path="/transformations/:transformationId"
                element={<TransformationsView />}
              />
              <Route path="/architecture" element={<ArchitectureView />} />
              <Route
                path="/recommendations"
                element={<RecommendationsView />}
              />
              <Route path="/telemetry" element={<TelemetryView />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          )}
        </main>
      </div>

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-content">
          <span>Metamorphic Architecture Dashboard</span>
          {systemState && <span>Version {systemState.version || "1.0.0"}</span>}
        </div>
      </footer>
    </div>
  );
}

// 404 Page
function NotFound() {
  return (
    <div className="not-found">
      <h2>404 - Page Not Found</h2>
      <p>The page you're looking for doesn't exist or has been moved.</p>
      <NavLink to="/" className="button">
        Return to Dashboard
      </NavLink>
    </div>
  );
}

export default App;
