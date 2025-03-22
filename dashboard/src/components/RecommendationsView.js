import React, { useState, useEffect } from "react";
import { useMetamorphic } from "../context/MetamorphicContext";

function RecommendationsView() {
  const { systemState, loading, refresh } = useMetamorphic();
  const [recommendations, setRecommendations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [applyingRecommendation, setApplyingRecommendation] = useState(null);
  const [filterType, setFilterType] = useState("all");
  const [sortBy, setSortBy] = useState("confidence");
  const [appliedRecommendations, setAppliedRecommendations] = useState([]);

  // Load recommendations
  useEffect(() => {
    fetchRecommendations();
  }, []);

  // Fetch recommendations from API
  const fetchRecommendations = async () => {
    try {
      setIsLoading(true);
      const response = await fetch("/api/recommendations");
      const data = await response.json();
      setRecommendations(data);
    } catch (error) {
      console.error("Error fetching recommendations:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle applying a recommendation
  const handleApplyRecommendation = async (recommendation) => {
    try {
      setApplyingRecommendation(recommendation.id);
      const response = await fetch(
        `/api/apply-recommendation/${recommendation.id}`,
        {
          method: "POST",
        }
      );

      if (response.ok) {
        const result = await response.json();

        // Add to applied recommendations
        setAppliedRecommendations([
          ...appliedRecommendations,
          {
            id: recommendation.id,
            appliedAt: new Date().toISOString(),
            planId: result.plan_id,
            recommendation,
          },
        ]);

        // Refresh data and recommendations
        refresh();
        fetchRecommendations();

        // Show success
        alert(
          `Recommendation applied successfully. Transformation plan created: ${result.plan_id}`
        );
      } else {
        const error = await response.json();
        alert(
          `Failed to apply recommendation: ${error.detail || "Unknown error"}`
        );
      }
    } catch (error) {
      console.error("Error applying recommendation:", error);
      alert(
        "Failed to apply recommendation due to a system error. Please try again."
      );
    } finally {
      setApplyingRecommendation(null);
    }
  };

  // Get filtered and sorted recommendations
  const getFilteredRecommendations = () => {
    let filtered = [...recommendations];

    // Apply type filter
    if (filterType !== "all") {
      filtered = filtered.filter((rec) => rec.type === filterType);
    }

    // Check if already applied
    filtered = filtered.filter(
      (rec) => !appliedRecommendations.some((applied) => applied.id === rec.id)
    );

    // Apply sorting
    filtered.sort((a, b) => {
      if (sortBy === "confidence") {
        return b.confidence - a.confidence;
      } else if (sortBy === "impact") {
        const impactOrder = { high: 3, medium: 2, low: 1 };
        return impactOrder[b.impact || "low"] - impactOrder[a.impact || "low"];
      } else {
        return 0;
      }
    });

    return filtered;
  };

  // Get recommendation type icon
  const getRecommendationIcon = (type) => {
    switch (type) {
      case "service_coupling":
        return "🔄";
      case "resource_optimization":
        return "📊";
      case "architectural":
        return "🏗️";
      case "performance":
        return "⚡";
      default:
        return "💡";
    }
  };

  // Get impact class for styling
  const getImpactClass = (impact) => {
    switch (impact) {
      case "high":
        return "impact-high";
      case "medium":
        return "impact-medium";
      case "low":
        return "impact-low";
      default:
        return "impact-low";
    }
  };

  if (loading && !recommendations.length) {
    return <div className="loading-message">Loading recommendations...</div>;
  }

  const filteredRecommendations = getFilteredRecommendations();

  return (
    <div className="recommendations-view">
      <h1>Architectural Recommendations</h1>

      <div className="controls-container">
        <div className="filters">
          <div className="filter-group">
            <label>Filter by Type:</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="all">All Types</option>
              <option value="service_coupling">Service Coupling</option>
              <option value="resource_optimization">
                Resource Optimization
              </option>
              <option value="architectural">Architectural</option>
              <option value="performance">Performance</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Sort by:</label>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="confidence">Confidence</option>
              <option value="impact">Impact</option>
            </select>
          </div>
        </div>

        <button
          className="refresh-button"
          onClick={fetchRecommendations}
          disabled={isLoading}
        >
          {isLoading ? "Refreshing..." : "Refresh Recommendations"}
        </button>
      </div>

      <div className="recommendations-container">
        <div className="active-recommendations">
          <h2>Recommended Actions</h2>

          {isLoading ? (
            <div className="loading-overlay">Loading recommendations...</div>
          ) : filteredRecommendations.length > 0 ? (
            <div className="recommendations-list">
              {filteredRecommendations.map((recommendation) => (
                <div key={recommendation.id} className="recommendation-card">
                  <div className="recommendation-icon">
                    {getRecommendationIcon(recommendation.type)}
                  </div>
                  <div className="recommendation-content">
                    <div className="recommendation-header">
                      <h3>{recommendation.description}</h3>
                      <div
                        className={`impact-badge ${getImpactClass(
                          recommendation.impact
                        )}`}
                      >
                        {recommendation.impact}
                      </div>
                    </div>

                    <div className="recommendation-meta">
                      <div className="meta-item">
                        <span className="meta-label">Type:</span>
                        <span className="meta-value">
                          {recommendation.type.replace("_", " ")}
                        </span>
                      </div>
                      <div className="meta-item">
                        <span className="meta-label">Confidence:</span>
                        <span className="meta-value">
                          {(recommendation.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    <div className="recommendation-actions">
                      <button
                        className="apply-button"
                        onClick={() =>
                          handleApplyRecommendation(recommendation)
                        }
                        disabled={applyingRecommendation === recommendation.id}
                      >
                        {applyingRecommendation === recommendation.id
                          ? "Applying..."
                          : "Apply Recommendation"}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">✓</div>
              <h3>No recommendations to display</h3>
              <p>There are no active recommendations matching your filters.</p>
            </div>
          )}
        </div>

        <div className="applied-recommendations">
          <h2>Applied Recommendations</h2>

          {appliedRecommendations.length > 0 ? (
            <div className="applied-list">
              {appliedRecommendations.map((applied, index) => (
                <div key={index} className="applied-item">
                  <div className="applied-icon">
                    {getRecommendationIcon(applied.recommendation.type)}
                  </div>
                  <div className="applied-content">
                    <h3>{applied.recommendation.description}</h3>
                    <div className="applied-meta">
                      <span>
                        Applied: {new Date(applied.appliedAt).toLocaleString()}
                      </span>
                      <span>Plan ID: {applied.planId}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-applied">
              <p>No recommendations have been applied yet.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Additional styles
const styles = `
  .recommendations-view h1 {
    margin-bottom: 20px;
    color: var(--dark-color);
  }
  
  .controls-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    background: white;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  .filters {
    display: flex;
    gap: 20px;
  }
  
  .filter-group {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .filter-group label {
    font-weight: 500;
  }
  
  .filter-group select {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: white;
  }
  
  .refresh-button {
    padding: 8px 16px;
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .refresh-button:hover {
    background-color: var(--secondary-color);
  }
  
  .refresh-button:disabled {
    background-color: #aaa;
    cursor: not-allowed;
  }
  
  .recommendations-container {
    display: flex;
    gap: 20px;
  }
  
  .active-recommendations {
    flex: 2;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    padding: 20px;
    position: relative;
  }
  
  .applied-recommendations {
    flex: 1;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    padding: 20px;
  }
  
  .recommendations-container h2 {
    margin-top: 0;
    margin-bottom: 20px;
    font-size: 1.3rem;
    color: var(--dark-color);
  }
  
  .recommendations-list {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }
  
  .recommendation-card {
    display: flex;
    align-items: stretch;
    background: #f9f9f9;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }
  
  .recommendation-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 60px;
    background: var(--primary-color);
    color: white;
    font-size: 24px;
  }
  
  .recommendation-content {
    flex: 1;
    padding: 15px;
    display: flex;
    flex-direction: column;
  }
  
  .recommendation-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 10px;
  }
  
  .recommendation-header h3 {
    margin: 0;
    font-size: 1.1rem;
    color: var(--dark-color);
  }
  
  .impact-badge {
    padding: 4px 8px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
  }
  
  .impact-high {
    background-color: #ffecec;
    color: var(--danger-color);
  }
  
  .impact-medium {
    background-color: #fff8e6;
    color: #e6a817;
  }
  
  .impact-low {
    background-color: #e6f7f2;
    color: var(--success-color);
  }
  
  .recommendation-meta {
    display: flex;
    gap: 15px;
    margin-bottom: 15px;
  }
  
  .meta-item {
    display: flex;
    align-items: center;
    gap: 5px;
  }
  
  .meta-label {
    font-size: 0.85rem;
    color: #666;
  }
  
  .meta-value {
    font-weight: 500;
  }
  
  .recommendation-actions {
    display: flex;
    justify-content: flex-end;
  }
  
  .apply-button {
    padding: 6px 12px;
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .apply-button:hover {
    background-color: var(--secondary-color);
  }
  
  .apply-button:disabled {
    background-color: #aaa;
    cursor: not-allowed;
  }
  
  .loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.8);
    z-index: 10;
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    text-align: center;
  }
  
  .empty-icon {
    font-size: 3rem;
    margin-bottom: 15px;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: var(--success-color);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .empty-state h3 {
    margin-bottom: 10px;
    color: var(--dark-color);
  }
  
  .empty-state p {
    color: #666;
  }
  
  .applied-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  
  .applied-item {
    display: flex;
    gap: 10px;
    padding: 12px;
    background: #f9f9f9;
    border-radius: 6px;
  }
  
  .applied-icon {
    font-size: 18px;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: #eee;
  }
  
  .applied-content {
    flex: 1;
  }
  
  .applied-content h3 {
    font-size: 0.95rem;
    margin: 0 0 5px 0;
    color: var(--dark-color);
  }
  
  .applied-meta {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: 0.8rem;
    color: #666;
  }
  
  .empty-applied {
    padding: 20px;
    text-align: center;
    color: #666;
    font-style: italic;
  }
  
  @media (max-width: 768px) {
    .recommendations-container {
      flex-direction: column;
    }
    
    .controls-container {
      flex-direction: column;
      gap: 15px;
      align-items: flex-start;
    }
    
    .filters {
      flex-direction: column;
      gap: 10px;
      width: 100%;
    }
    
    .refresh-button {
      width: 100%;
    }
  }
`;

// Inject the component styles
const styleSheet = document.createElement("style");
styleSheet.type = "text/css";
styleSheet.innerText = styles;
document.head.appendChild(styleSheet);

export default RecommendationsView;
