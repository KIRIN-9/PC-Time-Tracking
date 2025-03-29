/**
 * Frontend configuration
 */

// API configuration
const config = {
  // Development config (when running locally)
  development: {
    apiBaseUrl: "http://localhost:8000/api/v1",
    wsBaseUrl: "ws://localhost:8000",
  },

  // Production config (when deployed to Vercel)
  production: {
    // Update this with your actual backend server when deployed
    apiBaseUrl: "http://your-backend-server.com/api/v1",
    wsBaseUrl: "ws://your-backend-server.com",
  },

  // Test config
  test: {
    apiBaseUrl: "http://localhost:8000/api/v1",
    wsBaseUrl: "ws://localhost:8000",
  },
};

// Determine environment
const environment =
  window.location.hostname === "localhost" ? "development" : "production";

// Export the appropriate config
export const apiConfig = config[environment];

// Helper for API calls
export const apiUrl = (endpoint) => {
  // Remove leading slash if it exists
  const cleanEndpoint = endpoint.startsWith("/")
    ? endpoint.substring(1)
    : endpoint;
  return `${apiConfig.apiBaseUrl}/${cleanEndpoint}`;
};

// Export constants
export const REFRESH_INTERVAL = 5000; // 5 seconds default refresh interval
export const DEFAULT_HOURS = 24; // Default time period for stats
