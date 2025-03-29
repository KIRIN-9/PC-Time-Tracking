// Config.js - Configuration for PC Time Tracker Frontend

const config = {
  // API Base URL - detects environment and sets appropriate URL
  apiBaseUrl:
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1"
      ? "http://localhost:5000" // development
      : window.location.origin, // production

  // Default workday length in hours
  defaultWorkdayHours: 8,

  // Refresh interval in milliseconds
  refreshInterval: 300000, // 5 minutes

  // Break reminder settings
  breakReminders: {
    enabled: true,
    interval: 3600000, // 1 hour
    duration: 300000, // 5 minutes
  },

  // UI Settings
  ui: {
    theme: "light", // 'light' or 'dark'
    timeFormat: "24h", // '12h' or '24h'
    dateFormat: "YYYY-MM-DD",
  },

  // Get API endpoint
  getEndpoint: function (path) {
    return `${this.apiBaseUrl}${path.startsWith("/") ? path : "/" + path}`;
  },
};
