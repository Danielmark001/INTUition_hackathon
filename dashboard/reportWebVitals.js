/**
 * Simplified Web Vitals reporting function
 *
 * This is a placeholder for performance metric reporting.
 * The actual web-vitals package is not required for the application to function.
 */

const reportWebVitals = (onPerfEntry) => {
  // No-op implementation that doesn't require the web-vitals package
  if (onPerfEntry && typeof onPerfEntry === "function") {
    // We could add basic performance metrics here if needed
    const timestamp = Date.now();

    // Report a basic timestamp as a simple metric
    onPerfEntry({
      name: "app-load",
      value: timestamp,
      delta: 0,
      id: "app-load-" + timestamp,
    });
  }
};

export default reportWebVitals;
