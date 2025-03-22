/**
 * API Client for the Metamorphic Architecture Dashboard
 * Handles all API communications with the backend services
 */

// Base API URL - can be overridden with environment variable
const API_BASE_URL = process.env.REACT_APP_API_URL || "/api";

/**
 * Generic fetch wrapper with error handling
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} Response data
 * @throws {Error} Network or API error
 */
const fetchWithErrorHandling = async (endpoint, options = {}) => {
  try {
    const url = `${API_BASE_URL}${endpoint}`;

    // Set default headers if not provided
    const headers = options.headers || {};
    if (!headers["Content-Type"] && options.method !== "GET" && options.body) {
      headers["Content-Type"] = "application/json";
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle non-200 responses
    if (!response.ok) {
      // Try to get error details from JSON response
      let errorDetail = "";
      try {
        const errorData = await response.json();
        errorDetail =
          errorData.detail || errorData.message || JSON.stringify(errorData);
      } catch (e) {
        // If response isn't JSON, use status text
        errorDetail = response.statusText;
      }

      throw new Error(`API Error (${response.status}): ${errorDetail}`);
    }

    // Check if response is empty
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return await response.json();
    }

    return { success: true };
  } catch (error) {
    console.error("API request failed:", error);
    throw error;
  }
};

/**
 * Get dashboard overview data
 * @returns {Promise<Object>} Dashboard data
 */
export const getDashboardData = () => {
  return fetchWithErrorHandling("/dashboard-data");
};

/**
 * Get list of all services
 * @param {string} status - Optional status filter
 * @returns {Promise<Array>} List of services
 */
export const getServices = (status) => {
  const endpoint = status ? `/services?status=${status}` : "/services";
  return fetchWithErrorHandling(endpoint);
};

/**
 * Get details of a specific service
 * @param {string} serviceId - Service ID
 * @returns {Promise<Object>} Service details
 */
export const getServiceDetails = (serviceId) => {
  return fetchWithErrorHandling(`/services/${serviceId}`);
};

/**
 * Create a new service
 * @param {Object} serviceData - Service data
 * @returns {Promise<Object>} Created service
 */
export const createService = (serviceData) => {
  return fetchWithErrorHandling("/services", {
    method: "POST",
    body: JSON.stringify(serviceData),
  });
};

/**
 * Update an existing service
 * @param {string} serviceId - Service ID
 * @param {Object} serviceData - Updated service data
 * @returns {Promise<Object>} Updated service
 */
export const updateService = (serviceId, serviceData) => {
  return fetchWithErrorHandling(`/services/${serviceId}`, {
    method: "PUT",
    body: JSON.stringify(serviceData),
  });
};

/**
 * Delete a service
 * @param {string} serviceId - Service ID
 * @returns {Promise<Object>} Response
 */
export const deleteService = (serviceId) => {
  return fetchWithErrorHandling(`/services/${serviceId}`, {
    method: "DELETE",
  });
};

/**
 * Get metrics for a service
 * @param {string} serviceId - Service ID
 * @param {number} timeWindow - Time window in seconds
 * @returns {Promise<Array>} Service metrics
 */
export const getServiceMetrics = (serviceId, timeWindow = 3600) => {
  return fetchWithErrorHandling(
    `/metrics/${serviceId}?time_window=${timeWindow}`
  );
};

/**
 * Get all transformation plans
 * @returns {Promise<Array>} List of transformation plans
 */
export const getTransformations = () => {
  return fetchWithErrorHandling("/transformations");
};

/**
 * Get details of a specific transformation plan
 * @param {string} planId - Plan ID
 * @returns {Promise<Object>} Transformation plan details
 */
export const getTransformationDetails = (planId) => {
  return fetchWithErrorHandling(`/transformations/${planId}`);
};

/**
 * Create a new transformation plan
 * @param {Object} transformationData - Transformation data
 * @returns {Promise<Object>} Created transformation plan
 */
export const createTransformation = (transformationData) => {
  return fetchWithErrorHandling("/transformations", {
    method: "POST",
    body: JSON.stringify(transformationData),
  });
};

/**
 * Execute a transformation plan
 * @param {string} planId - Plan ID
 * @returns {Promise<Object>} Response
 */
export const executeTransformation = (planId) => {
  return fetchWithErrorHandling(`/transformations/${planId}/execute`, {
    method: "POST",
  });
};

/**
 * Generate a transformation plan
 * @param {string} planId - Plan ID
 * @returns {Promise<Object>} Response
 */
export const generateTransformationPlan = (planId) => {
  return fetchWithErrorHandling(`/transformations/${planId}/generate`, {
    method: "POST",
  });
};

/**
 * Get architectural recommendations
 * @returns {Promise<Array>} List of recommendations
 */
export const getRecommendations = () => {
  return fetchWithErrorHandling("/recommendations");
};

/**
 * Apply a specific recommendation
 * @param {string} recommendationId - Recommendation ID
 * @returns {Promise<Object>} Response with created plan
 */
export const applyRecommendation = (recommendationId) => {
  return fetchWithErrorHandling(`/apply-recommendation/${recommendationId}`, {
    method: "POST",
  });
};

/**
 * Trigger system analysis
 * @returns {Promise<Object>} Analysis results
 */
export const analyzeSystem = () => {
  return fetchWithErrorHandling("/analyze", {
    method: "POST",
  });
};

/**
 * Get transaction traces
 * @param {number} limit - Max number of traces to return
 * @returns {Promise<Array>} Transaction traces
 */
export const getTransactionTraces = (limit = 20) => {
  return fetchWithErrorHandling(`/data/transactions/recent?limit=${limit}`);
};

/**
 * Get current architecture state
 * @returns {Promise<Object>} Current architecture
 */
export const getCurrentArchitecture = () => {
  return fetchWithErrorHandling("/architecture/current");
};

/**
 * Get architecture history
 * @param {number} limit - Max number of items to return
 * @returns {Promise<Array>} Architecture history
 */
export const getArchitectureHistory = (limit = 10) => {
  return fetchWithErrorHandling(`/architecture/history?limit=${limit}`);
};

/**
 * Identify architecture hotspots
 * @returns {Promise<Object>} Hotspots analysis
 */
export const identifyHotspots = () => {
  return fetchWithErrorHandling("/hotspots", {
    method: "POST",
  });
};

/**
 * Compare two architecture states
 * @param {Object} currentState - Current architecture state
 * @param {Object} proposedState - Proposed architecture state
 * @returns {Promise<Object>} Comparison results
 */
export const compareArchitectures = (currentState, proposedState) => {
  return fetchWithErrorHandling("/compare", {
    method: "POST",
    body: JSON.stringify({
      current: currentState,
      proposed: proposedState,
    }),
  });
};

// Export default API client with all methods
export default {
  getDashboardData,
  getServices,
  getServiceDetails,
  createService,
  updateService,
  deleteService,
  getServiceMetrics,
  getTransformations,
  getTransformationDetails,
  createTransformation,
  executeTransformation,
  generateTransformationPlan,
  getRecommendations,
  applyRecommendation,
  analyzeSystem,
  getTransactionTraces,
  getCurrentArchitecture,
  getArchitectureHistory,
  identifyHotspots,
  compareArchitectures,
};
