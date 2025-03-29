// Dashboard.js - Main dashboard functionality

// State variables
let currentDate = new Date();
let viewMode = "day"; // 'day' or 'week'
let trackingEnabled = true;
let breakInProgress = false;
let lastBreakTime = new Date();
let breakStartTime = null;
let breakEndTime = null;
let breakDuration = 0;
let workDuration = 0;

// Cache of processed data
let cachedData = {
  processes: [],
  resources: [],
  idle: [],
  workblocks: [],
  categories: {},
  breakdown: [],
};

// Chart objects
let timelineChart = null;
let focusChart = null;
let meetingsChart = null;
let breaksChart = null;

// DOM elements
const elements = {
  currentDateEl: document.getElementById("current-date"),
  prevDayBtn: document.getElementById("prev-day"),
  nextDayBtn: document.getElementById("next-day"),
  viewDayBtn: document.getElementById("view-day"),
  viewWeekBtn: document.getElementById("view-week"),

  totalTimeValue: document.getElementById("total-time-value"),
  percentValue: document.getElementById("percent-value"),
  workdayHours: document.getElementById("workday-hours"),
  trackingStatus: document.getElementById("tracking-status"),
  trackingHours: document.getElementById("tracking-hours"),
  toggleTrackingBtn: document.getElementById("toggle-tracking"),

  timeSinceBreak: document.getElementById("time-since-break"),
  breakRatio: document.getElementById("break-ratio"),
  startBreakBtn: document.getElementById("start-break"),

  activityList: document.getElementById("activity-list"),
  workblocksList: document.getElementById("workblocks-list"),
  projectsList: document.getElementById("projects-list"),

  focusScore: document.getElementById("focus-score"),
  focusTime: document.getElementById("focus-time"),
  meetingsScore: document.getElementById("meetings-score"),
  meetingsTime: document.getElementById("meetings-time"),
  breaksScore: document.getElementById("breaks-score"),
  breaksTime: document.getElementById("breaks-time"),

  breakdownList: document.getElementById("breakdown-list"),
};

// Initialize the dashboard
function init() {
  // Update date display
  updateDateDisplay();

  // Setup event listeners
  setupEventListeners();

  // Initialize charts
  initializeCharts();

  // Load data
  loadDashboardData();

  // Start timers
  startTimers();
}

// Update the current date display
function updateDateDisplay() {
  const options = {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  };
  elements.currentDateEl.textContent = currentDate.toLocaleDateString(
    "en-US",
    options
  );
}

// Setup event listeners
function setupEventListeners() {
  elements.prevDayBtn.addEventListener("click", () => {
    currentDate.setDate(currentDate.getDate() - 1);
    updateDateDisplay();
    loadDashboardData();
  });

  elements.nextDayBtn.addEventListener("click", () => {
    currentDate.setDate(currentDate.getDate() + 1);
    updateDateDisplay();
    loadDashboardData();
  });

  elements.viewDayBtn.addEventListener("click", () => {
    viewMode = "day";
    elements.viewDayBtn.classList.add("active");
    elements.viewWeekBtn.classList.remove("active");
    loadDashboardData();
  });

  elements.viewWeekBtn.addEventListener("click", () => {
    viewMode = "week";
    elements.viewWeekBtn.classList.add("active");
    elements.viewDayBtn.classList.remove("active");
    loadDashboardData();
  });

  elements.toggleTrackingBtn.addEventListener("click", () => {
    toggleTracking();
  });

  elements.startBreakBtn.addEventListener("click", () => {
    toggleBreak();
  });
}

// Initialize chart objects
function initializeCharts() {
  // Timeline chart
  const timelineCtx = document
    .getElementById("timeline-canvas")
    .getContext("2d");
  timelineChart = new Chart(timelineCtx, {
    type: "bar",
    data: {
      labels: [],
      datasets: [],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          stacked: true,
          grid: {
            display: false,
          },
          ticks: {
            display: false,
          },
        },
        y: {
          stacked: true,
          display: false,
        },
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          enabled: true,
        },
      },
    },
  });

  // Focus chart (donut)
  const focusCtx = document.getElementById("focus-chart").getContext("2d");
  focusChart = new Chart(focusCtx, {
    type: "doughnut",
    data: {
      labels: ["Focus", "Other"],
      datasets: [
        {
          data: [60, 40],
          backgroundColor: ["#4caf50", "#333"],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "70%",
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          enabled: false,
        },
      },
    },
  });

  // Meetings chart (donut)
  const meetingsCtx = document
    .getElementById("meetings-chart")
    .getContext("2d");
  meetingsChart = new Chart(meetingsCtx, {
    type: "doughnut",
    data: {
      labels: ["Meetings", "Other"],
      datasets: [
        {
          data: [12, 88],
          backgroundColor: ["#673ab7", "#333"],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "70%",
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          enabled: false,
        },
      },
    },
  });

  // Breaks chart (donut)
  const breaksCtx = document.getElementById("breaks-chart").getContext("2d");
  breaksChart = new Chart(breaksCtx, {
    type: "doughnut",
    data: {
      labels: ["Breaks", "Other"],
      datasets: [
        {
          data: [18, 82],
          backgroundColor: ["#2196f3", "#333"],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "70%",
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          enabled: false,
        },
      },
    },
  });
}

// Load dashboard data from API
async function loadDashboardData() {
  try {
    // Get processes for the current date
    const dateStr = formatDateForAPI(currentDate);
    const processesResponse = await api.fetchProcesses(dateStr);

    // Get resources for the current date
    const resourcesResponse = await api.fetchResources(dateStr);

    // Get idle time for the current date
    const idleResponse = await api.fetchIdleTime(dateStr);

    // Process the data
    processData(processesResponse, resourcesResponse, idleResponse);

    // Update the UI
    updateDashboard();
  } catch (error) {
    console.error("Error loading dashboard data:", error);
  }
}

// Process raw data into usable format
function processData(processes, resources, idle) {
  // Save raw data
  cachedData.processes = processes;
  cachedData.resources = resources;
  cachedData.idle = idle;

  // Generate workblocks
  cachedData.workblocks = generateWorkblocks(processes, idle);

  // Calculate category breakdown
  cachedData.breakdown = calculateBreakdown(processes);

  // Calculate scores
  calculateScores();
}

// Generate work blocks from process data
function generateWorkblocks(processes, idle) {
  // Group processes by time blocks
  const timeBlocks = {};

  // Create 5-minute blocks
  processes.forEach((process) => {
    const timestamp = new Date(process.timestamp);
    const blockKey = Math.floor(
      timestamp.getHours() * 12 + timestamp.getMinutes() / 5
    );

    if (!timeBlocks[blockKey]) {
      timeBlocks[blockKey] = {
        startTime: new Date(timestamp),
        processes: [],
        category: null,
        duration: 5 * 60, // 5 minutes in seconds
        isIdle: false,
      };
    }

    timeBlocks[blockKey].processes.push(process);
  });

  // Mark idle blocks
  idle.forEach((idleEntry) => {
    const timestamp = new Date(idleEntry.timestamp);
    const blockKey = Math.floor(
      timestamp.getHours() * 12 + timestamp.getMinutes() / 5
    );

    if (timeBlocks[blockKey] && idleEntry.is_idle) {
      timeBlocks[blockKey].isIdle = true;
    }
  });

  // Determine category for each block
  Object.values(timeBlocks).forEach((block) => {
    const categoryCounts = {};

    block.processes.forEach((process) => {
      if (process.category) {
        categoryCounts[process.category] =
          (categoryCounts[process.category] || 0) + 1;
      }
    });

    // Find most common category
    let maxCount = 0;
    let maxCategory = null;

    for (const [category, count] of Object.entries(categoryCounts)) {
      if (count > maxCount) {
        maxCount = count;
        maxCategory = category;
      }
    }

    block.category = maxCategory || "Other";
  });

  // Merge adjacent blocks with the same category
  const merged = [];
  let currentBlock = null;

  Object.values(timeBlocks)
    .sort((a, b) => a.startTime - b.startTime)
    .forEach((block) => {
      if (!currentBlock) {
        currentBlock = { ...block };
        return;
      }

      // If same category and not idle, merge
      if (
        currentBlock.category === block.category &&
        !block.isIdle &&
        !currentBlock.isIdle
      ) {
        currentBlock.duration += block.duration;
        currentBlock.processes = [
          ...currentBlock.processes,
          ...block.processes,
        ];
      } else {
        merged.push(currentBlock);
        currentBlock = { ...block };
      }
    });

  if (currentBlock) {
    merged.push(currentBlock);
  }

  return merged;
}

// Calculate time breakdown by category
function calculateBreakdown(processes) {
  const categories = {};
  let totalTime = 0;

  processes.forEach((process) => {
    const category = process.category || "Other";

    if (!categories[category]) {
      categories[category] = 0;
    }

    // Each process entry represents about 5 seconds of time
    categories[category] += 5;
    totalTime += 5;
  });

  // Convert to array and sort by time spent
  const breakdown = Object.entries(categories).map(([name, seconds]) => ({
    name,
    seconds,
    percent: Math.round((seconds / totalTime) * 100),
  }));

  return breakdown.sort((a, b) => b.seconds - a.seconds);
}

// Calculate focus, meetings, and breaks scores
function calculateScores() {
  // Calculate work and break durations
  workDuration = 0;
  breakDuration = 0;

  cachedData.workblocks.forEach((block) => {
    if (block.isIdle) {
      breakDuration += block.duration;
    } else {
      workDuration += block.duration;
    }
  });

  // Calculate focus time (coding, documentation)
  const focusCategories = ["Code", "Documentation", "Development", "Design"];
  let focusTime = 0;

  cachedData.workblocks.forEach((block) => {
    if (focusCategories.includes(block.category) && !block.isIdle) {
      focusTime += block.duration;
    }
  });

  // Calculate meeting time
  const meetingCategories = ["Meeting", "Call", "Communication"];
  let meetingTime = 0;

  cachedData.workblocks.forEach((block) => {
    if (meetingCategories.includes(block.category) && !block.isIdle) {
      meetingTime += block.duration;
    }
  });

  // Set scores
  const totalTime = workDuration + breakDuration;
  const focusScore =
    totalTime > 0 ? Math.round((focusTime / totalTime) * 100) : 0;
  const meetingsScore =
    totalTime > 0 ? Math.round((meetingTime / totalTime) * 100) : 0;
  const breaksScore =
    totalTime > 0 ? Math.round((breakDuration / totalTime) * 100) : 0;

  // Update chart data
  focusChart.data.datasets[0].data = [focusScore, 100 - focusScore];
  meetingsChart.data.datasets[0].data = [meetingsScore, 100 - meetingsScore];
  breaksChart.data.datasets[0].data = [breaksScore, 100 - breaksScore];

  // Update charts
  focusChart.update();
  meetingsChart.update();
  breaksChart.update();

  // Update score displays
  elements.focusScore.textContent = `${focusScore}%`;
  elements.meetingsScore.textContent = `${meetingsScore}%`;
  elements.breaksScore.textContent = `${breaksScore}%`;

  // Update time displays
  elements.focusTime.textContent = formatDuration(focusTime);
  elements.meetingsTime.textContent = formatDuration(meetingTime);
  elements.breaksTime.textContent = formatDuration(breakDuration);
}

// Update the dashboard UI
function updateDashboard() {
  // Update timeline
  updateTimeline();

  // Update work hours
  updateWorkHours();

  // Update workblocks list
  updateWorkblocks();

  // Update breakdown
  updateBreakdown();

  // Update activity list
  updateActivity();

  // Update projects
  updateProjects();
}

// Update timeline visualization
function updateTimeline() {
  const workBlocks = cachedData.workblocks;
  const hours = [];
  const focusData = [];
  const meetingsData = [];
  const otherData = [];
  const breakData = [];

  // Generate labels for each 15-minute interval
  for (let hour = 6; hour <= 22; hour++) {
    for (let minute = 0; minute < 60; minute += 15) {
      hours.push(`${hour}:${minute.toString().padStart(2, "0")}`);
      focusData.push(0);
      meetingsData.push(0);
      otherData.push(0);
      breakData.push(0);
    }
  }

  // Fill in the data
  workBlocks.forEach((block) => {
    const startHour = block.startTime.getHours();
    const startMinute = block.startTime.getMinutes();

    // Find the closest index
    const index = (startHour - 6) * 4 + Math.floor(startMinute / 15);

    if (index >= 0 && index < hours.length) {
      const blockDuration = block.duration / 60; // Convert to minutes

      if (block.isIdle) {
        breakData[index] += blockDuration;
      } else if (
        ["Code", "Documentation", "Development", "Design"].includes(
          block.category
        )
      ) {
        focusData[index] += blockDuration;
      } else if (
        ["Meeting", "Call", "Communication"].includes(block.category)
      ) {
        meetingsData[index] += blockDuration;
      } else {
        otherData[index] += blockDuration;
      }
    }
  });

  // Update the chart
  timelineChart.data.labels = hours;
  timelineChart.data.datasets = [
    {
      label: "Focus",
      data: focusData,
      backgroundColor: "#4caf50",
    },
    {
      label: "Meetings",
      data: meetingsData,
      backgroundColor: "#673ab7",
    },
    {
      label: "Other",
      data: otherData,
      backgroundColor: "#ff9800",
    },
    {
      label: "Breaks",
      data: breakData,
      backgroundColor: "#2196f3",
    },
  ];

  timelineChart.update();
}

// Update work hours section
function updateWorkHours() {
  const totalSeconds = workDuration;
  const workdaySeconds = 8 * 60 * 60; // 8 hours
  const percentWorked = Math.min(
    Math.round((totalSeconds / workdaySeconds) * 100),
    100
  );

  elements.totalTimeValue.textContent = formatDuration(totalSeconds);
  elements.percentValue.textContent = `${percentWorked}%`;
  elements.workdayHours.textContent = `of 8 hr 0 min`;
}

// Update workblocks list
function updateWorkblocks() {
  const workblocksList = elements.workblocksList;
  workblocksList.innerHTML = "";

  cachedData.workblocks.forEach((block) => {
    if (!block.isIdle) {
      const startTime = block.startTime;
      const timeStr = startTime.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      });
      const durationMinutes = Math.round(block.duration / 60);

      const blockEl = document.createElement("div");
      blockEl.className = "workblock-item";

      const timeEl = document.createElement("div");
      timeEl.className = "workblock-time";
      timeEl.textContent = timeStr;

      const categoryEl = document.createElement("div");
      categoryEl.className = `workblock-category ${block.category.toLowerCase()}`;
      categoryEl.textContent = block.category;

      const durationEl = document.createElement("div");
      durationEl.className = "workblock-duration";
      durationEl.textContent = `${durationMinutes} min`;

      const scoreEl = document.createElement("div");
      scoreEl.className = "workblock-score";

      // Calculate productivity score (random for now)
      const score = Math.floor(Math.random() * 20) + 80;
      scoreEl.textContent = score.toFixed(1);

      blockEl.appendChild(timeEl);
      blockEl.appendChild(categoryEl);
      blockEl.appendChild(durationEl);
      blockEl.appendChild(scoreEl);

      workblocksList.appendChild(blockEl);
    }
  });
}

// Update time breakdown
function updateBreakdown() {
  const breakdownList = elements.breakdownList;
  breakdownList.innerHTML = "";

  cachedData.breakdown.slice(0, 10).forEach((category) => {
    const categoryEl = document.createElement("div");
    categoryEl.className = "breakdown-item";

    const percentEl = document.createElement("div");
    percentEl.className = "breakdown-percent";
    percentEl.textContent = `${category.percent}%`;

    const nameContainer = document.createElement("div");

    const nameEl = document.createElement("div");
    nameEl.className = "breakdown-name";
    nameEl.textContent = category.name;

    const barEl = document.createElement("div");
    barEl.className = "breakdown-bar";

    const progressEl = document.createElement("div");
    progressEl.className = `breakdown-progress ${category.name.toLowerCase()}`;
    progressEl.style.width = `${category.percent}%`;

    barEl.appendChild(progressEl);
    nameContainer.appendChild(nameEl);
    nameContainer.appendChild(barEl);

    const timeEl = document.createElement("div");
    timeEl.className = "breakdown-time";
    timeEl.textContent = formatDuration(category.seconds);

    categoryEl.appendChild(percentEl);
    categoryEl.appendChild(nameContainer);
    categoryEl.appendChild(timeEl);

    breakdownList.appendChild(categoryEl);
  });
}

// Update activity list
function updateActivity() {
  const activityList = elements.activityList;
  activityList.innerHTML = "";

  // Sort processes by timestamp (newest first)
  const recentProcesses = [...cachedData.processes]
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    .slice(0, 20);

  // Group by active_window
  const groupedProcesses = {};

  recentProcesses.forEach((process) => {
    if (!groupedProcesses[process.name]) {
      groupedProcesses[process.name] = {
        name: process.name,
        window: process.active_window || "Unknown",
        timestamp: process.timestamp,
      };
    }
  });

  // Display the unique processes
  Object.values(groupedProcesses).forEach((process) => {
    const activityEl = document.createElement("div");
    activityEl.className = "activity-item";

    const timeEl = document.createElement("div");
    timeEl.className = "activity-time";
    const time = new Date(process.timestamp);
    timeEl.textContent = time.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });

    const infoContainer = document.createElement("div");

    const appEl = document.createElement("div");
    appEl.className = "activity-app";
    appEl.textContent = process.name;

    const detailsEl = document.createElement("div");
    detailsEl.className = "activity-details";
    detailsEl.textContent = process.window;

    infoContainer.appendChild(appEl);
    infoContainer.appendChild(detailsEl);

    activityEl.appendChild(infoContainer);
    activityEl.appendChild(timeEl);

    activityList.appendChild(activityEl);
  });
}

// Update projects section
function updateProjects() {
  const projectsList = elements.projectsList;
  projectsList.innerHTML = "";

  // Group processes by category
  const categories = {};

  cachedData.processes.forEach((process) => {
    const category = process.category || "Other";

    if (!categories[category]) {
      categories[category] = 0;
    }

    categories[category] += 5; // Each entry is about 5 seconds
  });

  // Convert to array and sort
  const projectsArray = Object.entries(categories)
    .map(([name, seconds]) => ({ name, seconds }))
    .sort((a, b) => b.seconds - a.seconds)
    .slice(0, 5);

  const totalSeconds = projectsArray.reduce((sum, p) => sum + p.seconds, 0);

  // Create project items
  projectsArray.forEach((project) => {
    const projectEl = document.createElement("div");
    projectEl.className = "project-item";

    const nameContainer = document.createElement("div");

    const nameEl = document.createElement("div");
    nameEl.className = "project-name";
    nameEl.textContent = project.name;

    const barEl = document.createElement("div");
    barEl.className = "project-bar";

    const progressEl = document.createElement("div");
    progressEl.className = "project-progress";
    progressEl.style.width = `${(project.seconds / totalSeconds) * 100}%`;

    barEl.appendChild(progressEl);
    nameContainer.appendChild(nameEl);
    nameContainer.appendChild(barEl);

    const timeEl = document.createElement("div");
    timeEl.className = "project-time";
    timeEl.textContent = formatDuration(project.seconds);

    projectEl.appendChild(nameContainer);
    projectEl.appendChild(timeEl);

    projectsList.appendChild(projectEl);
  });
}

// Start interval timers
function startTimers() {
  // Update break timer every second
  setInterval(updateBreakTimer, 1000);

  // Refresh dashboard data every 5 minutes
  setInterval(loadDashboardData, 5 * 60 * 1000);
}

// Update break timer
function updateBreakTimer() {
  // Calculate time since last break
  const now = new Date();
  const timeSinceBreak = (now - lastBreakTime) / 1000;

  // Update display
  elements.timeSinceBreak.textContent = formatTime(timeSinceBreak);

  // Calculate break ratio
  const ratio =
    breakDuration > 0 && workDuration > 0
      ? (breakDuration / workDuration).toFixed(1)
      : "0.0";

  elements.breakRatio.textContent = `1 / ${ratio}`;
}

// Toggle tracking on/off
function toggleTracking() {
  trackingEnabled = !trackingEnabled;

  if (trackingEnabled) {
    elements.trackingStatus.textContent = "On";
    elements.toggleTrackingBtn.textContent = "Disable Tracking";
  } else {
    elements.trackingStatus.textContent = "Off";
    elements.toggleTrackingBtn.textContent = "Enable Tracking";
  }

  // Call API to toggle tracking
  api.toggleTracking(trackingEnabled);
}

// Toggle break state
function toggleBreak() {
  breakInProgress = !breakInProgress;

  if (breakInProgress) {
    elements.startBreakBtn.textContent = "End Break";
    breakStartTime = new Date();
  } else {
    elements.startBreakBtn.textContent = "Start Break";
    breakEndTime = new Date();
    lastBreakTime = new Date();

    // Calculate duration of the break
    if (breakStartTime) {
      const breakDurationSeconds = (breakEndTime - breakStartTime) / 1000;
      breakDuration += breakDurationSeconds;

      // Log the break
      api.logBreak(breakStartTime, breakEndTime);
    }
  }
}

// Helper Functions

// Format a date for API requests
function formatDateForAPI(date) {
  return date.toISOString().split("T")[0];
}

// Format seconds into a human-readable duration
function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours > 0) {
    return `${hours} hr ${minutes} min`;
  } else {
    return `${minutes} min`;
  }
}

// Format seconds into a time string (HH:MM:SS)
function formatTime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  return `${hours}:${minutes.toString().padStart(2, "0")}:${secs
    .toString()
    .padStart(2, "0")}`;
}

// Initialize when the DOM is ready
document.addEventListener("DOMContentLoaded", init);
