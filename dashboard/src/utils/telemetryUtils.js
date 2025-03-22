/**
 * Utility functions for processing and visualizing telemetry data
 */

/**
 * Process raw telemetry data for chart visualization
 * @param {Array} data - Raw telemetry data from API
 * @param {string} timeFormat - Time format ('hour', 'minute', 'second')
 * @returns {Array} Processed data ready for charts
 */
export const processTelemetryData = (data, timeFormat = "minute") => {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return [];
  }

  return data.map((point) => {
    const timestamp = new Date(point.timestamp * 1000);

    let formattedTime;
    switch (timeFormat) {
      case "hour":
        formattedTime = `${timestamp.getHours()}:00`;
        break;
      case "second":
        formattedTime = timestamp.toLocaleTimeString();
        break;
      case "minute":
      default:
        formattedTime = `${timestamp.getHours()}:${String(
          timestamp.getMinutes()
        ).padStart(2, "0")}`;
    }

    return {
      timestamp: formattedTime,
      rawTimestamp: point.timestamp,
      cpuUsage: (point.cpu_usage * 100).toFixed(1),
      memoryUsage: (point.memory_usage * 100).toFixed(1),
      latency: point.latency?.toFixed(1) || 0,
      requestCount: point.request_count || 0,
      errorRate: (point.error_rate * 100).toFixed(2) || 0,
      // Additional metrics if available
      ...(point.additional_metrics && {
        additionalMetrics: point.additional_metrics,
      }),
    };
  });
};

/**
 * Aggregate telemetry data by time window
 * @param {Array} data - Raw telemetry data
 * @param {string} interval - Aggregation interval ('minute', 'hour', 'day')
 * @returns {Array} Aggregated data
 */
export const aggregateTelemetryData = (data, interval = "minute") => {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return [];
  }

  const aggregated = {};

  data.forEach((point) => {
    const timestamp = new Date(point.timestamp * 1000);

    // Create time bucket key based on interval
    let bucketKey;
    switch (interval) {
      case "hour":
        bucketKey = `${timestamp.getFullYear()}-${timestamp.getMonth()}-${timestamp.getDate()}-${timestamp.getHours()}`;
        break;
      case "day":
        bucketKey = `${timestamp.getFullYear()}-${timestamp.getMonth()}-${timestamp.getDate()}`;
        break;
      case "minute":
      default:
        bucketKey = `${timestamp.getFullYear()}-${timestamp.getMonth()}-${timestamp.getDate()}-${timestamp.getHours()}-${timestamp.getMinutes()}`;
    }

    // Initialize bucket if it doesn't exist
    if (!aggregated[bucketKey]) {
      aggregated[bucketKey] = {
        timestamp: timestamp.getTime() / 1000,
        formattedTime: formatTimestamp(timestamp, interval),
        cpuPoints: [],
        memoryPoints: [],
        latencyPoints: [],
        requestCount: 0,
        errorCount: 0,
      };
    }

    // Add data to bucket
    const bucket = aggregated[bucketKey];
    bucket.cpuPoints.push(point.cpu_usage || 0);
    bucket.memoryPoints.push(point.memory_usage || 0);
    bucket.latencyPoints.push(point.latency || 0);
    bucket.requestCount += point.request_count || 0;
    bucket.errorCount += point.error_count || 0;
  });

  // Calculate averages and format the result
  return Object.values(aggregated)
    .map((bucket) => ({
      timestamp: bucket.formattedTime,
      rawTimestamp: bucket.timestamp,
      cpuUsage: (averageArray(bucket.cpuPoints) * 100).toFixed(1),
      memoryUsage: (averageArray(bucket.memoryPoints) * 100).toFixed(1),
      latency: averageArray(bucket.latencyPoints).toFixed(1),
      requestCount: bucket.requestCount,
      errorRate:
        bucket.requestCount > 0
          ? ((bucket.errorCount / bucket.requestCount) * 100).toFixed(2)
          : "0.00",
    }))
    .sort((a, b) => a.rawTimestamp - b.rawTimestamp);
};

/**
 * Calculate moving average for a metric to smooth chart data
 * @param {Array} data - Telemetry data
 * @param {string} metric - Metric to average
 * @param {number} windowSize - Size of the moving window
 * @returns {Array} Data with moving average added
 */
export const calculateMovingAverage = (data, metric, windowSize = 5) => {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return [];
  }

  const result = [...data];

  for (let i = 0; i < data.length; i++) {
    // Calculate window boundaries
    const windowStart = Math.max(0, i - Math.floor(windowSize / 2));
    const windowEnd = Math.min(data.length - 1, i + Math.floor(windowSize / 2));
    const window = data.slice(windowStart, windowEnd + 1);

    // Calculate average for the window
    const values = window.map((item) => parseFloat(item[metric] || 0));
    const average = averageArray(values);

    // Add moving average to result
    result[i] = {
      ...result[i],
      [`${metric}MA`]: average.toFixed(2),
    };
  }

  return result;
};

/**
 * Convert raw transaction traces to a format suitable for visualization
 * @param {Array} traces - Raw transaction traces
 * @returns {Array} Processed traces
 */
export const processTransactionTraces = (traces) => {
  if (!traces || !Array.isArray(traces) || traces.length === 0) {
    return [];
  }

  return (
    traces
      .map((trace) => {
        // Extract list of unique services involved
        const services = Array.from(
          new Set(trace.spans.map((span) => span.service_id))
        );

        // Calculate total duration
        const totalLatency = trace.spans.reduce(
          (sum, span) => sum + (span.latency || 0),
          0
        );

        // Get start and end times
        const startTime = Math.min(
          ...trace.spans.map((span) => span.timestamp)
        );
        const endTime = Math.max(
          ...trace.spans.map(
            (span) => span.timestamp + (span.latency / 1000 || 0)
          )
        );

        // Process spans for visualization
        const processedSpans = trace.spans
          .sort((a, b) => a.timestamp - b.timestamp)
          .map((span) => ({
            service_id: span.service_id,
            latency: span.latency?.toFixed(1) || 0,
            start_time: new Date(span.timestamp * 1000).toLocaleTimeString(),
            timestamp: span.timestamp,
          }));

        return {
          transaction_id: trace.transaction_id,
          services,
          total_latency: totalLatency,
          start_time: startTime,
          end_time: endTime,
          spans: processedSpans,
          span_count: trace.spans.length,
        };
      })
      // Sort by most recent first
      .sort((a, b) => b.start_time - a.start_time)
  );
};

// Helper function to calculate average of an array of numbers
const averageArray = (arr) => {
  if (!arr || arr.length === 0) return 0;
  return arr.reduce((sum, val) => sum + (parseFloat(val) || 0), 0) / arr.length;
};

// Helper function to format timestamp based on interval
const formatTimestamp = (timestamp, interval) => {
  switch (interval) {
    case "hour":
      return `${timestamp.getHours()}:00`;
    case "day":
      return timestamp.toLocaleDateString();
    case "minute":
    default:
      return `${timestamp.getHours()}:${String(timestamp.getMinutes()).padStart(
        2,
        "0"
      )}`;
  }
};

/**
 * Generate colors for service visualization
 * @param {Array} services - List of service names
 * @returns {Object} Map of service names to colors
 */
export const generateServiceColors = (services) => {
  const baseColors = [
    "#4a90e2", // Blue
    "#ff6b6b", // Red
    "#50c878", // Green
    "#ff8c00", // Orange
    "#9370db", // Purple
    "#20b2aa", // Teal
    "#ff6347", // Tomato
    "#3cb371", // Sea Green
    "#4169e1", // Royal Blue
    "#ff4500", // Orange Red
  ];

  const colorMap = {};

  services.forEach((service, index) => {
    colorMap[service] = baseColors[index % baseColors.length];
  });

  return colorMap;
};
