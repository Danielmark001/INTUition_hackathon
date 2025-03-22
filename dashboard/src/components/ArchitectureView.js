import React, { useEffect, useRef, useState } from "react";
import { useMetamorphic } from "../context/MetamorphicContext";
import * as d3 from "d3";

function ArchitectureView() {
  const { systemState, services, loading } = useMetamorphic();
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [graphData, setGraphData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [viewMode, setViewMode] = useState("dependency"); // 'dependency', 'resources', 'status'

  // Calculate graph data when system state changes
  useEffect(() => {
    if (!loading && systemState && services.length > 0) {
      const nodes = services.map((service) => ({
        id: service.service_id,
        group: determineGroup(service),
        status: service.status,
        capabilities: service.capabilities || [],
        dependencies: service.dependencies || [],
        resources: service.resource_allocation || {},
      }));

      // Create links based on dependencies
      const links = [];
      nodes.forEach((node) => {
        if (node.dependencies && node.dependencies.length > 0) {
          node.dependencies.forEach((depId) => {
            if (nodes.some((n) => n.id === depId)) {
              links.push({
                source: node.id,
                target: depId,
                value: 1,
              });
            }
          });
        }
      });

      setGraphData({ nodes, links });
    }
  }, [systemState, services, loading]);

  // Draw graph when data changes or view mode changes
  useEffect(() => {
    if (graphData && svgRef.current) {
      drawGraph();
    }
  }, [graphData, viewMode]);

  // Function to determine the group (for coloring)
  function determineGroup(service) {
    // Group by primary capability
    if (service.capabilities && service.capabilities.length > 0) {
      const capability = service.capabilities[0];
      if (capability.includes("user")) return 1;
      if (capability.includes("order")) return 2;
      if (capability.includes("payment")) return 3;
      if (capability.includes("notif")) return 4;
      return 5;
    }
    return 0;
  }

  // Draw the architecture graph
  function drawGraph() {
    if (!graphData || !svgRef.current) return;

    // Clear previous graph
    d3.select(svgRef.current).selectAll("*").remove();

    const containerWidth = containerRef.current.clientWidth;
    const containerHeight = containerRef.current.clientHeight;

    const svg = d3
      .select(svgRef.current)
      .attr("width", containerWidth)
      .attr("height", containerHeight);

    // Colors based on view mode
    let nodeColorScale;
    if (viewMode === "dependency") {
      // Group-based coloring
      nodeColorScale = d3
        .scaleOrdinal()
        .domain([0, 1, 2, 3, 4, 5])
        .range(["#aaa", "#4a90e2", "#ff6b6b", "#50c878", "#ffa500", "#8a2be2"]);
    } else if (viewMode === "resources") {
      // Resource utilization coloring
      nodeColorScale = d3
        .scaleLinear()
        .domain([0, 0.5, 1, 1.5, 2])
        .range(["#d1e5f0", "#92c5de", "#4393c3", "#2166ac", "#053061"]);
    } else if (viewMode === "status") {
      // Status-based coloring
      nodeColorScale = d3
        .scaleOrdinal()
        .domain(["active", "degraded", "offline"])
        .range(["#4ecca3", "#ffbb28", "#ff6b6b"]);
    }

    // Create a simulation with forces
    const simulation = d3
      .forceSimulation(graphData.nodes)
      .force(
        "link",
        d3
          .forceLink(graphData.links)
          .id((d) => d.id)
          .distance(100)
      )
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(containerWidth / 2, containerHeight / 2))
      .force("x", d3.forceX(containerWidth / 2).strength(0.1))
      .force("y", d3.forceY(containerHeight / 2).strength(0.1));

    // Create a container for links with a lower z-index
    const linkGroup = svg.append("g").attr("class", "links");

    // Create a container for nodes with a higher z-index
    const nodeGroup = svg.append("g").attr("class", "nodes");

    // Draw links
    const link = linkGroup
      .selectAll("line")
      .data(graphData.links)
      .enter()
      .append("line")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", (d) => Math.sqrt(d.value));

    // Create node groups
    const node = nodeGroup
      .selectAll("g")
      .data(graphData.nodes)
      .enter()
      .append("g")
      .attr("class", "node")
      .call(
        d3
          .drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended)
      )
      .on("click", (event, d) => {
        event.stopPropagation();
        setSelectedNode(d);
      });

    // Add circles to nodes
    node
      .append("circle")
      .attr("r", (d) => getNodeRadius(d))
      .attr("fill", (d) => getNodeColor(d))
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5);

    // Add labels to nodes
    node
      .append("text")
      .attr("dy", 30)
      .attr("text-anchor", "middle")
      .text((d) => d.id)
      .attr("fill", "#333")
      .style("font-size", "10px")
      .style("pointer-events", "none");

    // Add title for hover
    node
      .append("title")
      .text(
        (d) =>
          `${d.id}\nStatus: ${d.status}\nCapabilities: ${d.capabilities.join(
            ", "
          )}`
      );

    // Update positions on each simulation tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    // Drag handlers
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // Helper functions for node appearance
    function getNodeRadius(d) {
      if (viewMode === "resources") {
        // Size based on total resources
        const cpu = d.resources.cpu || 0;
        const memory = d.resources.memory || 0;
        return 10 + Math.sqrt(cpu + memory) * 5;
      }
      // Default size with bonus for more capabilities
      return 12 + d.capabilities.length * 2;
    }

    function getNodeColor(d) {
      if (viewMode === "dependency") {
        return nodeColorScale(d.group);
      } else if (viewMode === "resources") {
        const cpu = d.resources.cpu || 0;
        const memory = d.resources.memory || 0;
        return nodeColorScale((cpu + memory) / 2);
      } else if (viewMode === "status") {
        return nodeColorScale(d.status);
      }
      return nodeColorScale(d.group);
    }

    // Clear selection when clicking on the background
    svg.on("click", () => {
      setSelectedNode(null);
    });
  }

  if (loading) {
    return <div className="loading-message">Loading architecture data...</div>;
  }

  return (
    <div className="architecture-view">
      <h1>Architecture Visualization</h1>

      <div className="view-controls">
        <div className="view-modes">
          <button
            className={`view-mode-button ${
              viewMode === "dependency" ? "active" : ""
            }`}
            onClick={() => setViewMode("dependency")}
          >
            Dependency View
          </button>
          <button
            className={`view-mode-button ${
              viewMode === "resources" ? "active" : ""
            }`}
            onClick={() => setViewMode("resources")}
          >
            Resource View
          </button>
          <button
            className={`view-mode-button ${
              viewMode === "status" ? "active" : ""
            }`}
            onClick={() => setViewMode("status")}
          >
            Status View
          </button>
        </div>

        <div className="legend">
          {viewMode === "dependency" && (
            <div className="legend-items">
              <div className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: "#4a90e2" }}
                ></div>
                <div className="legend-label">User Services</div>
              </div>
              <div className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: "#ff6b6b" }}
                ></div>
                <div className="legend-label">Order Services</div>
              </div>
              <div className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: "#50c878" }}
                ></div>
                <div className="legend-label">Payment Services</div>
              </div>
              <div className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: "#ffa500" }}
                ></div>
                <div className="legend-label">Notification Services</div>
              </div>
              <div className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: "#8a2be2" }}
                ></div>
                <div className="legend-label">Other Services</div>
              </div>
            </div>
          )}

          {viewMode === "resources" && (
            <div className="legend-items">
              <div className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: "#d1e5f0" }}
                ></div>
                <div className="legend-label">Low Resource Usage</div>
              </div>
              <div className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: "#4393c3" }}
                ></div>
                <div className="legend-label">Medium Resource Usage</div>
              </div>
              <div className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: "#053061" }}
                ></div>
                <div className="legend-label">High Resource Usage</div>
              </div>
            </div>
          )}

          {viewMode === "status" && (
            <div className="legend-items">
              <div className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: "#4ecca3" }}
                ></div>
                <div className="legend-label">Active</div>
              </div>
              <div className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: "#ffbb28" }}
                ></div>
                <div className="legend-label">Degraded</div>
              </div>
              <div className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: "#ff6b6b" }}
                ></div>
                <div className="legend-label">Offline</div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="architecture-container">
        <div className="graph-container" ref={containerRef}>
          <svg ref={svgRef} className="architecture-graph"></svg>
        </div>

        {selectedNode && (
          <div className="node-details">
            <h2>{selectedNode.id}</h2>

            <div className="detail-section">
              <h3>Status</h3>
              <div className={`status-badge status-${selectedNode.status}`}>
                {selectedNode.status}
              </div>
            </div>

            <div className="detail-section">
              <h3>Capabilities</h3>
              <div className="capabilities-list">
                {selectedNode.capabilities.map((cap, index) => (
                  <div key={index} className="capability-tag">
                    {cap}
                  </div>
                ))}
              </div>
            </div>

            <div className="detail-section">
              <h3>Dependencies</h3>
              {selectedNode.dependencies.length > 0 ? (
                <ul className="dependencies-list">
                  {selectedNode.dependencies.map((dep, index) => (
                    <li key={index}>{dep}</li>
                  ))}
                </ul>
              ) : (
                <div className="empty-message">No dependencies</div>
              )}
            </div>

            <div className="detail-section">
              <h3>Resources</h3>
              <div className="resources-list">
                <div className="resource-item">
                  <span>CPU:</span>
                  <span>{selectedNode.resources.cpu || 0}</span>
                </div>
                <div className="resource-item">
                  <span>Memory:</span>
                  <span>{selectedNode.resources.memory || 0}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Additional styles
const styles = `
  .architecture-view h1 {
    margin-bottom: 20px;
    color: var(--dark-color);
  }
  
  .view-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    background: white;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  .view-modes {
    display: flex;
    gap: 10px;
  }
  
  .view-mode-button {
    padding: 8px 16px;
    border: 1px solid var(--primary-color);
    background: white;
    color: var(--primary-color);
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .view-mode-button:hover {
    background: #f0f7ff;
  }
  
  .view-mode-button.active {
    background: var(--primary-color);
    color: white;
  }
  
  .legend {
    display: flex;
    align-items: center;
  }
  
  .legend-items {
    display: flex;
    gap: 15px;
  }
  
  .legend-item {
    display: flex;
    align-items: center;
    gap: 5px;
  }
  
  .legend-color {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }
  
  .legend-label {
    font-size: 0.85rem;
  }
  
  .architecture-container {
    display: flex;
    gap: 20px;
    height: calc(100vh - 280px);
  }
  
  .graph-container {
    flex: 1;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    overflow: hidden;
  }
  
  .architecture-graph {
    width: 100%;
    height: 100%;
  }
  
  .node-details {
    width: 300px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    padding: 20px;
    overflow-y: auto;
  }
  
  .node-details h2 {
    margin-top: 0;
    margin-bottom: 20px;
    color: var(--dark-color);
    font-size: 1.5rem;
  }
  
  .detail-section {
    margin-bottom: 20px;
  }
  
  .detail-section h3 {
    font-size: 1.1rem;
    margin-bottom: 10px;
    color: var(--dark-color);
  }
  
  .status-badge {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 15px;
    font-size: 0.9rem;
    font-weight: 500;
    text-transform: uppercase;
  }
  
  .status-active {
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
  
  .dependencies-list {
    list-style-type: none;
    padding: 0;
    margin: 0;
  }
  
  .dependencies-list li {
    padding: 5px 0;
    border-bottom: 1px solid #eee;
  }
  
  .dependencies-list li:last-child {
    border-bottom: none;
  }
  
  .resources-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  
  .resource-item {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
    border-bottom: 1px solid #eee;
  }
  
  .resource-item:last-child {
    border-bottom: none;
  }
  
  .empty-message {
    color: #777;
    font-style: italic;
  }
  
  @media (max-width: 768px) {
    .architecture-container {
      flex-direction: column;
      height: auto;
    }
    
    .graph-container {
      height: 400px;
    }
    
    .node-details {
      width: 100%;
    }
    
    .view-controls {
      flex-direction: column;
      gap: 15px;
      align-items: flex-start;
    }
    
    .legend-items {
      flex-wrap: wrap;
    }
  }
`;

// Inject the component styles
const styleSheet = document.createElement("style");
styleSheet.type = "text/css";
styleSheet.innerText = styles;
document.head.appendChild(styleSheet);

export default ArchitectureView;
