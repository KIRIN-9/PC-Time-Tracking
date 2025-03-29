// API.js - API utilities for the PC Time Tracker

const API_BASE_URL = "http://localhost:5000/api";

// Helper function for making API requests
async function makeRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.statusText}`);
  }

  return response.json();
}

// API client object
const api = {
  // Status and monitoring
  getStatus: () => makeRequest("/status"),
  startMonitoring: () => makeRequest("/monitor/start", { method: "POST" }),
  stopMonitoring: () => makeRequest("/monitor/stop", { method: "POST" }),

  // Real-time data
  getCurrentResources: () => makeRequest("/resources/current"),
  getActiveProcesses: () => makeRequest("/processes/active"),
  getActiveWindow: () => makeRequest("/active-window"),

  // Historical data
  getProcessHistory: (startTime, endTime, category = "all") =>
    makeRequest(
      `/processes/history?start_time=${startTime}&end_time=${endTime}&category=${category}`
    ),

  getResourceHistory: (startTime, endTime) =>
    makeRequest(
      `/resources/history?start_time=${startTime}&end_time=${endTime}`
    ),

  getIdleHistory: (startTime, endTime) =>
    makeRequest(`/idle/history?start_time=${startTime}&end_time=${endTime}`),

  // Process details
  getProcessDetails: (pid) => makeRequest(`/processes/${pid}`),

  // Categories
  getCategories: () => makeRequest("/categories"),
  getProcessesByCategory: (category, startTime, endTime) =>
    makeRequest(
      `/categories/${category}/processes?start_time=${startTime}&end_time=${endTime}`
    ),
  updateCategories: (categories) =>
    makeRequest("/categories/update", {
      method: "POST",
      body: JSON.stringify({ categories }),
    }),

  // Statistics
  getStatsSummary: (startTime, endTime) =>
    makeRequest(`/stats/summary?start_time=${startTime}&end_time=${endTime}`),

  // Filter settings
  updateFilter: (settings) =>
    makeRequest("/filter/update", {
      method: "POST",
      body: JSON.stringify(settings),
    }),

  /**
   * Fetch processes for a specific date
   * @param {string} date - Date in YYYY-MM-DD format
   * @returns {Promise<Array>} - Array of process objects
   */
  async fetchProcesses(date) {
    try {
      const url = `${API_BASE_URL}/api/processes?date=${date}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.processes || [];
    } catch (error) {
      console.error("Error fetching processes:", error);
      return [];
    }
  },

  /**
   * Fetch system resources for a specific date
   * @param {string} date - Date in YYYY-MM-DD format
   * @returns {Promise<Array>} - Array of resource usage objects
   */
  async fetchResources(date) {
    try {
      const url = `${API_BASE_URL}/api/resources?date=${date}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.resources || [];
    } catch (error) {
      console.error("Error fetching resources:", error);
      return [];
    }
  },

  /**
   * Fetch idle time data for a specific date
   * @param {string} date - Date in YYYY-MM-DD format
   * @returns {Promise<Array>} - Array of idle time objects
   */
  async fetchIdleTime(date) {
    try {
      const url = `${API_BASE_URL}/api/idle?date=${date}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.idle_times || [];
    } catch (error) {
      console.error("Error fetching idle time:", error);
      return [];
    }
  },

  /**
   * Toggle tracking on/off
   * @param {boolean} enabled - Whether tracking should be enabled
   * @returns {Promise<Object>} - Response object
   */
  async toggleTracking(enabled) {
    try {
      const url = `${API_BASE_URL}/api/tracking`;
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ enabled }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error toggling tracking:", error);
      return { success: false, error: error.message };
    }
  },

  /**
   * Log a break
   * @param {Date} startTime - Break start time
   * @param {Date} endTime - Break end time
   * @returns {Promise<Object>} - Response object
   */
  async logBreak(startTime, endTime) {
    try {
      const url = `${API_BASE_URL}/api/breaks`;
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          start_time: startTime.toISOString(),
          end_time: endTime.toISOString(),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error logging break:", error);
      return { success: false, error: error.message };
    }
  },

  /**
   * Export data for a specific date range
   * @param {string} startDate - Start date in YYYY-MM-DD format
   * @param {string} endDate - End date in YYYY-MM-DD format
   * @param {string} format - Export format (csv, json)
   * @returns {Promise<Blob>} - Data blob for download
   */
  async exportData(startDate, endDate, format = "csv") {
    try {
      const url = `${API_BASE_URL}/api/export?start_date=${startDate}&end_date=${endDate}&format=${format}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Return blob for download
      return await response.blob();
    } catch (error) {
      console.error("Error exporting data:", error);
      throw error;
    }
  },

  /**
   * Get tracking status
   * @returns {Promise<Object>} - Tracking status object
   */
  async getTrackingStatus() {
    try {
      const url = `${API_BASE_URL}/api/status`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error getting tracking status:", error);
      return { tracking: false, error: error.message };
    }
  },

  /**
   * Update filter settings
   * @param {Object} filterSettings - Filter settings to update
   * @returns {Promise<Object>} - Response object
   */
  async updateFilters(filterSettings) {
    try {
      const url = `${API_BASE_URL}/api/filters`;
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(filterSettings),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error updating filters:", error);
      return { success: false, error: error.message };
    }
  },

  /**
   * Get filter settings
   * @returns {Promise<Object>} - Filter settings object
   */
  async getFilters() {
    try {
      const url = `${API_BASE_URL}/api/filters`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error getting filters:", error);
      return { filters: {}, error: error.message };
    }
  },
};

// Export the API client
window.api = api;
