// Dashboard.js - Main dashboard functionality

// State variables
let trackingEnabled = false;
let breakInProgress = false;
let lastBreakTime = new Date();
let breakStartTime = null;
let workDuration = 0;
let breakDuration = 0;
let updateInterval = null;

// DOM elements
const elements = {
  toggleTrackingBtn: document.getElementById("toggle-tracking"),
  startBreakBtn: document.getElementById("start-break"),
  workTime: document.getElementById("work-time"),
  breakTime: document.getElementById("break-time"),
  timeSinceBreak: document.getElementById("time-since-break"),
  activityList: document.getElementById("activity-list"),
  activeWindow: document.getElementById("active-window"),
  dateFilter: document.getElementById("date-filter"),
  categoryFilter: document.getElementById("category-filter"),
  activeProcessesList: document.getElementById("active-processes-list"),
};

// Initialize the dashboard
async function init() {
  // Setup event listeners
  setupEventListeners();

  // Initialize charts
  initializeCharts();

  // Set default date filter to today
  const today = new Date().toISOString().split("T")[0];
  elements.dateFilter.value = today;

  // Load initial data
  await loadDashboardData();

  // Start real-time updates
  startRealTimeUpdates();
}

// Setup event listeners
function setupEventListeners() {
  elements.toggleTrackingBtn.addEventListener("click", toggleTracking);
  elements.startBreakBtn.addEventListener("click", toggleBreak);
  elements.dateFilter.addEventListener("change", loadDashboardData);
  elements.categoryFilter.addEventListener("change", loadDashboardData);
}

// Start real-time updates
function startRealTimeUpdates() {
  // Update every 2 seconds
  updateInterval = setInterval(async () => {
    if (trackingEnabled) {
      await updateRealTimeData();
    }
  }, 2000);
}

// Update real-time data
async function updateRealTimeData() {
  try {
    // Get current resources
    const resources = await api.getCurrentResources();
    updateResourceCharts(resources);

    // Get active processes
    const processes = await api.getActiveProcesses();
    updateActiveProcessesList(processes);

    // Get active window
    const window = await api.getActiveWindow();
    elements.activeWindow.textContent = window.title || "None";

    // Update timers
    updateTimers();
  } catch (error) {
    console.error("Error updating real-time data:", error);
  }
}

// Load dashboard data
async function loadDashboardData() {
  try {
    const date = new Date(elements.dateFilter.value);
    const startTime = date.getTime() / 1000;
    const endTime = startTime + 86400; // Add 24 hours

    // Get process history
    const processes = await api.getProcessHistory(startTime, endTime);
    updateActivityList(processes);

    // Get resource history
    const resources = await api.getResourceHistory(startTime, endTime);
    updateTimelineChart(resources);

    // Get idle history
    const idleTimes = await api.getIdleHistory(startTime, endTime);
    updateIdleStats(idleTimes);

    // Get summary statistics
    const summary = await api.getStatsSummary(startTime, endTime);
    updateSummaryStats(summary);
  } catch (error) {
    console.error("Error loading dashboard data:", error);
  }
}

// Update activity list
function updateActivityList(processes) {
  const container = elements.activityList;
  container.innerHTML = "";

  processes.forEach((process) => {
    const processElement = document.createElement("div");
    processElement.className = "activity-item";
    processElement.innerHTML = `
      <span class="process-name">${process.name}</span>
      <span class="process-category">${
        process.category || "Uncategorized"
      }</span>
      <span class="process-stats">
        CPU: ${process.cpu_percent.toFixed(1)}% |
        Memory: ${process.memory_percent.toFixed(1)}%
      </span>
    `;
    container.appendChild(processElement);
  });
}

// Update idle statistics
function updateIdleStats(idleTimes) {
  const totalIdleTime = idleTimes.reduce((sum, idle) => sum + idle.duration, 0);
  const totalTime = 86400; // 24 hours in seconds
  const idlePercentage = (totalIdleTime / totalTime) * 100;

  // Update UI with idle stats
  // You can add more detailed idle statistics here
}

// Update summary statistics
function updateSummaryStats(summary) {
  // Update UI with summary statistics
  // You can add more detailed summary statistics here
}

// Toggle tracking
async function toggleTracking() {
  try {
    if (!trackingEnabled) {
      await api.startMonitoring();
      trackingEnabled = true;
      elements.toggleTrackingBtn.textContent = "Stop Tracking";
      elements.toggleTrackingBtn.classList.add("active");
    } else {
      await api.stopMonitoring();
      trackingEnabled = false;
      elements.toggleTrackingBtn.textContent = "Start Tracking";
      elements.toggleTrackingBtn.classList.remove("active");
    }
  } catch (error) {
    console.error("Error toggling tracking:", error);
  }
}

// Toggle break
function toggleBreak() {
  if (!breakInProgress) {
    breakStartTime = new Date();
    breakInProgress = true;
    elements.startBreakBtn.textContent = "End Break";
    elements.startBreakBtn.classList.add("active");
  } else {
    breakInProgress = false;
    const breakDuration = (new Date() - breakStartTime) / 1000;
    breakDuration += breakDuration;
    lastBreakTime = new Date();
    elements.startBreakBtn.textContent = "Start Break";
    elements.startBreakBtn.classList.remove("active");
  }
}

// Update timers
function updateTimers() {
  const now = new Date();

  // Update work time
  if (trackingEnabled && !breakInProgress) {
    workDuration += 1;
  }
  elements.workTime.textContent = formatTime(workDuration);

  // Update break time
  elements.breakTime.textContent = formatTime(breakDuration);

  // Update time since last break
  const timeSinceBreak = (now - lastBreakTime) / 1000;
  elements.timeSinceBreak.textContent = formatTime(timeSinceBreak);
}

// Format time
function formatTime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  return `${hours.toString().padStart(2, "0")}:${minutes
    .toString()
    .padStart(2, "0")}:${remainingSeconds.toString().padStart(2, "0")}`;
}

// Cleanup on page unload
window.addEventListener("beforeunload", () => {
  if (updateInterval) {
    clearInterval(updateInterval);
  }
  if (trackingEnabled) {
    api.stopMonitoring();
  }
});

// Initialize the dashboard when the page loads
document.addEventListener("DOMContentLoaded", init);
