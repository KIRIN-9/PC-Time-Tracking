// API.js - API utilities for the PC Time Tracker

const api = {
  // Base URL for API endpoints
  baseUrl: config.apiBaseUrl,

  /**
   * Fetch processes for a specific date
   * @param {string} date - Date in YYYY-MM-DD format
   * @returns {Promise<Array>} - Array of process objects
   */
  async fetchProcesses(date) {
    try {
      const url = `${this.baseUrl}/api/processes?date=${date}`;
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
      const url = `${this.baseUrl}/api/resources?date=${date}`;
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
      const url = `${this.baseUrl}/api/idle?date=${date}`;
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
      const url = `${this.baseUrl}/api/tracking`;
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
      const url = `${this.baseUrl}/api/breaks`;
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
      const url = `${this.baseUrl}/api/export?start_date=${startDate}&end_date=${endDate}&format=${format}`;
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
      const url = `${this.baseUrl}/api/status`;
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
      const url = `${this.baseUrl}/api/filters`;
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
      const url = `${this.baseUrl}/api/filters`;
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
