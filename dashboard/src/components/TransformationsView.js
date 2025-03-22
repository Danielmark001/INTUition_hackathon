import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useMetamorphic } from "../context/MetamorphicContext";

function TransformationsView() {
  const { transformationId } = useParams();
  const navigate = useNavigate();
  const { transformations, systemState, loading, refresh } = useMetamorphic();

  const [selectedTransformation, setSelectedTransformation] = useState(null);
  const [detailedTransformation, setDetailedTransformation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Load the selected transformation when ID changes
  useEffect(() => {
    if (transformationId && transformations.length > 0) {
      const transformation = transformations.find(
        (t) => t.id === transformationId
      );
      setSelectedTransformation(transformation || null);

      if (transformation) {
        fetchTransformationDetails(transformation.id);
      }
    } else if (!transformationId) {
      setSelectedTransformation(null);
      setDetailedTransformation(null);
    }
  }, [transformationId, transformations]);

  // Fetch detailed transformation data
  const fetchTransformationDetails = async (id) => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/transformations/${id}`);
      const data = await response.json();
      setDetailedTransformation(data);
    } catch (error) {
      console.error("Error fetching transformation details:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle transformation selection
  const handleTransformationSelect = (transformation) => {
    navigate(`/transformations/${transformation.id}`);
  };

  // Execute a transformation
  const handleExecuteTransformation = async (id) => {
    try {
      const response = await fetch(`/api/transformations/${id}/execute`, {
        method: "POST",
      });

      if (response.ok) {
        // Refresh transformation data
        refresh();
        // Update the details
        fetchTransformationDetails(id);
      } else {
        console.error("Failed to execute transformation");
      }
    } catch (error) {
      console.error("Error executing transformation:", error);
    }
  };

  // Format date from timestamp
  const formatDate = (timestamp) => {
    if (!timestamp) return "N/A";
    return new Date(timestamp * 1000).toLocaleString();
  };

  // Get status class for styling
  const getStatusClass = (status) => {
    switch (status) {
      case "completed":
        return "status-success";
      case "executing":
        return "status-warning";
      case "failed":
        return "status-danger";
      case "ready":
        return "status-info";
      default:
        return "status-default";
    }
  };

  // Transformation progress percentage
  const calculateProgress = (transformation) => {
    if (!detailedTransformation || !detailedTransformation.transformation_steps)
      return 0;

    const totalSteps = detailedTransformation.transformation_steps.length;
    if (totalSteps === 0) return 0;

    const completedSteps = detailedTransformation.transformation_steps.filter(
      (step) => step.status === "completed"
    ).length;

    return Math.round((completedSteps / totalSteps) * 100);
  };

  if (loading) {
    return <div className="loading-message">Loading transformations...</div>;
  }

  return (
    <div className="transformations-view">
      <h1>Architectural Transformations</h1>

      <div className="transformations-container">
        <div className="transformations-list">
          <div className="list-header">
            <h2>Transformation Plans</h2>
            <div className="transformation-count">
              {transformations.length} plans
            </div>
          </div>

          <div className="transformation-items">
            {transformations.map((transformation) => (
              <div
                key={transformation.id}
                className={`transformation-item ${
                  selectedTransformation &&
                  selectedTransformation.id === transformation.id
                    ? "selected"
                    : ""
                }`}
                onClick={() => handleTransformationSelect(transformation)}
              >
                <div
                  className={`transformation-status ${getStatusClass(
                    transformation.status
                  )}`}
                ></div>
                <div className="transformation-info">
                  <div className="transformation-name">
                    {transformation.name}
                  </div>
                  <div className="transformation-metadata">
                    <span>{transformation.status}</span>
                    <span>{formatDate(transformation.updated_at)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="transformation-details">
          {selectedTransformation ? (
            isLoading ? (
              <div className="loading-details">
                Loading transformation details...
              </div>
            ) : (
              <>
                <div className="detail-header">
                  <h2>{selectedTransformation.name}</h2>
                  <div
                    className={`status-badge ${getStatusClass(
                      selectedTransformation.status
                    )}`}
                  >
                    {selectedTransformation.status}
                  </div>
                </div>

                <div className="description-card">
                  <p>
                    {selectedTransformation.description ||
                      "No description available."}
                  </p>
                </div>

                <div className="meta-info">
                  <div className="meta-item">
                    <span className="meta-label">Created:</span>
                    <span className="meta-value">
                      {formatDate(selectedTransformation.created_at)}
                    </span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Last Updated:</span>
                    <span className="meta-value">
                      {formatDate(selectedTransformation.updated_at)}
                    </span>
                  </div>
                  {detailedTransformation && detailedTransformation.metrics && (
                    <div className="meta-item">
                      <span className="meta-label">Duration:</span>
                      <span className="meta-value">
                        {detailedTransformation.metrics.duration
                          ? `${detailedTransformation.metrics.duration.toFixed(
                              2
                            )} seconds`
                          : "N/A"}
                      </span>
                    </div>
                  )}
                </div>

                {selectedTransformation.status === "ready" && (
                  <div className="action-buttons">
                    <button
                      className="execute-button"
                      onClick={() =>
                        handleExecuteTransformation(selectedTransformation.id)
                      }
                    >
                      Execute Transformation
                    </button>
                  </div>
                )}

                {selectedTransformation.status === "executing" &&
                  detailedTransformation && (
                    <div className="progress-container">
                      <div className="progress-label">
                        <span>Progress</span>
                        <span>
                          {calculateProgress(detailedTransformation)}%
                        </span>
                      </div>
                      <div className="progress-bar">
                        <div
                          className="progress-value"
                          style={{
                            width: `${calculateProgress(
                              detailedTransformation
                            )}%`,
                          }}
                        ></div>
                      </div>
                    </div>
                  )}

                {detailedTransformation &&
                  detailedTransformation.transformation_steps && (
                    <div className="steps-container">
                      <h3>Transformation Steps</h3>
                      <div className="steps-list">
                        {detailedTransformation.transformation_steps.map(
                          (step, index) => (
                            <div key={step.id || index} className="step-item">
                              <div
                                className={`step-status ${getStatusClass(
                                  step.status
                                )}`}
                              ></div>
                              <div className="step-content">
                                <div className="step-header">
                                  <span className="step-name">
                                    {step.description}
                                  </span>
                                  <span className="step-badge">
                                    {step.status}
                                  </span>
                                </div>
                                <div className="step-details">
                                  <span className="step-type">{step.type}</span>
                                  {step.completed_at && (
                                    <span className="step-time">
                                      {formatDate(step.completed_at)}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}

                {detailedTransformation &&
                  detailedTransformation.metrics &&
                  detailedTransformation.metrics.step_results && (
                    <div className="metrics-container">
                      <h3>Execution Metrics</h3>
                      <div className="metrics-grid">
                        <div className="metric-box">
                          <div className="metric-value">
                            {detailedTransformation.metrics.total_steps || 0}
                          </div>
                          <div className="metric-label">Total Steps</div>
                        </div>
                        <div className="metric-box">
                          <div className="metric-value">
                            {detailedTransformation.metrics.completed_steps ||
                              0}
                          </div>
                          <div className="metric-label">Completed</div>
                        </div>
                        <div className="metric-box">
                          <div className="metric-value">
                            {detailedTransformation.metrics.failed_steps || 0}
                          </div>
                          <div className="metric-label">Failed</div>
                        </div>
                        <div className="metric-box">
                          <div className="metric-value">
                            {detailedTransformation.metrics.duration
                              ? `${detailedTransformation.metrics.duration.toFixed(
                                  1
                                )}s`
                              : "N/A"}
                          </div>
                          <div className="metric-label">Duration</div>
                        </div>
                      </div>
                    </div>
                  )}
              </>
            )
          ) : (
            <div className="no-selection">
              <div className="empty-state">
                <i className="empty-icon">🔄</i>
                <h3>Select a transformation to view details</h3>
                <p>
                  Choose a transformation plan from the list to view its steps
                  and progress.
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
  .transformations-view h1 {
    margin-bottom: 20px;
    color: var(--dark-color);
  }
  
  .transformations-container {
    display: flex;
    gap: 20px;
    height: calc(100vh - 200px);
  }
  
  .transformations-list {
    width: 350px;
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
  
  .transformation-count {
    font-size: 0.9rem;
    color: #777;
  }
  
  .transformation-items {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
  }
  
  .transformation-item {
    display: flex;
    align-items: center;
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .transformation-item:hover {
    background-color: var(--gray-color);
  }
  
  .transformation-item.selected {
    background-color: var(--primary-color);
    color: white;
  }
  
  .transformation-item.selected .transformation-metadata {
    color: rgba(255, 255, 255, 0.8);
  }
  
  .transformation-status {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 12px;
  }
  
  .status-success {
    background-color: var(--success-color);
  }
  
  .status-warning {
    background-color: var(--warning-color);
  }
  
  .status-danger {
    background-color: var(--danger-color);
  }
  
  .status-info {
    background-color: var(--primary-color);
  }
  
  .status-default {
    background-color: #999;
  }
  
  .transformation-info {
    flex: 1;
  }
  
  .transformation-name {
    font-weight: 500;
    margin-bottom: 4px;
  }
  
  .transformation-metadata {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    color: #666;
  }
  
  .transformation-details {
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
  
  .status-badge {
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 500;
    text-transform: uppercase;
  }
  
  .description-card {
    background: #f9f9f9;
    border-radius: 6px;
    padding: 15px;
    margin-bottom: 20px;
  }
  
  .meta-info {
    display: flex;
    gap: 20px;
    margin-bottom: 20px;
  }
  
  .meta-item {
    display: flex;
    flex-direction: column;
  }
  
  .meta-label {
    font-size: 0.85rem;
    color: #666;
  }
  
  .meta-value {
    font-weight: 500;
  }
  
  .action-buttons {
    margin-bottom: 20px;
  }
  
  .execute-button {
    background-color: var(--primary-color);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .execute-button:hover {
    background-color: var(--secondary-color);
  }
  
  .progress-container {
    margin-bottom: 20px;
  }
  
  .progress-label {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
    font-size: 0.9rem;
  }
  
  .progress-bar {
    height: 10px;
    background-color: #eee;
    border-radius: 5px;
    overflow: hidden;
  }
  
  .progress-value {
    height: 100%;
    background-color: var(--primary-color);
    transition: width 0.3s;
  }
  
  .steps-container {
    margin-bottom: 20px;
  }
  
  .steps-container h3 {
    margin-bottom: 15px;
    font-size: 1.2rem;
  }
  
  .steps-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  
  .step-item {
    display: flex;
    align-items: flex-start;
    background: #f9f9f9;
    border-radius: 6px;
    padding: 12px;
  }
  
  .step-status {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 12px;
    margin-top: 4px;
  }
  
  .step-content {
    flex: 1;
  }
  
  .step-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 5px;
  }
  
  .step-name {
    font-weight: 500;
  }
  
  .step-badge {
    font-size: 0.8rem;
    padding: 2px 8px;
    border-radius: 10px;
    background: #eee;
  }
  
  .step-details {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    color: #666;
  }
  
  .metrics-container {
    margin-top: 20px;
  }
  
  .metrics-container h3 {
    margin-bottom: 15px;
    font-size: 1.2rem;
  }
  
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
  }
  
  .metric-box {
    background: #f9f9f9;
    border-radius: 6px;
    padding: 15px;
    text-align: center;
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
  
  .loading-details {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #666;
    font-style: italic;
  }
  
  @media (max-width: 768px) {
    .transformations-container {
      flex-direction: column;
      height: auto;
    }
    
    .transformations-list {
      width: 100%;
    }
    
    .meta-info {
      flex-direction: column;
      gap: 10px;
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

export default TransformationsView;
