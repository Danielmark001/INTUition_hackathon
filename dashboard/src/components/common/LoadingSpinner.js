import React from "react";

/**
 * A reusable loading spinner component
 * @param {Object} props
 * @param {string} props.message - Message to display below the spinner
 * @param {string} props.size - Size of the spinner (small, medium, large)
 * @param {string} props.color - Color of the spinner (defaults to primary color)
 */
function LoadingSpinner({ message = "Loading...", size = "medium", color }) {
  // Determine spinner size
  const spinnerSizes = {
    small: { width: "20px", height: "20px", border: "3px" },
    medium: { width: "40px", height: "40px", border: "4px" },
    large: { width: "60px", height: "60px", border: "5px" },
  };

  const spinnerSize = spinnerSizes[size] || spinnerSizes.medium;

  // Set default spinner color from CSS variables
  const spinnerColor = color || "var(--primary-color, #4a90e2)";

  return (
    <div className="loading-container">
      <div
        className="spinner"
        style={{
          width: spinnerSize.width,
          height: spinnerSize.height,
          borderWidth: spinnerSize.border,
          borderTopColor: spinnerColor,
        }}
      ></div>
      {message && <div className="loading-message">{message}</div>}
    </div>
  );
}

// Component styles
const styles = `
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20px;
    min-height: 120px;
  }
  
  .spinner {
    border-style: solid;
    border-color: rgba(0, 0, 0, 0.1);
    border-radius: 50%;
    animation: spinner-rotate 1s linear infinite;
  }
  
  .loading-message {
    margin-top: 15px;
    color: #666;
    font-size: 14px;
  }
  
  @keyframes spinner-rotate {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

// Inject the component styles
const styleSheet = document.createElement("style");
styleSheet.type = "text/css";
styleSheet.innerText = styles;
document.head.appendChild(styleSheet);

export default LoadingSpinner;
