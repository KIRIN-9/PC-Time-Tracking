// charts.js - Handles all chart-related functionality

// Chart instances
let cpuChart, memoryChart, diskChart, timelineChart;

// Chart configurations
const chartConfigs = {
  cpu: {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "CPU Usage (%)",
          data: [],
          borderColor: "#2196f3",
          backgroundColor: "rgba(33, 150, 243, 0.1)",
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
        },
      },
      animation: {
        duration: 0,
      },
    },
  },
  memory: {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Memory Usage (%)",
          data: [],
          borderColor: "#4caf50",
          backgroundColor: "rgba(76, 175, 80, 0.1)",
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
        },
      },
      animation: {
        duration: 0,
      },
    },
  },
  disk: {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Disk Usage (%)",
          data: [],
          borderColor: "#ff9800",
          backgroundColor: "rgba(255, 152, 0, 0.1)",
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
        },
      },
      animation: {
        duration: 0,
      },
    },
  },
};

// Initialize all charts
function initializeCharts() {
  const cpuCtx = document.getElementById("cpu-chart").getContext("2d");
  const memoryCtx = document.getElementById("memory-chart").getContext("2d");
  const diskCtx = document.getElementById("disk-chart").getContext("2d");
  const timelineCtx = document
    .getElementById("timeline-canvas")
    .getContext("2d");

  cpuChart = new Chart(cpuCtx, chartConfigs.cpu);
  memoryChart = new Chart(memoryCtx, chartConfigs.memory);
  diskChart = new Chart(diskCtx, chartConfigs.disk);

  // Timeline chart configuration
  timelineChart = new Chart(timelineCtx, {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          label: "Activity",
          data: [],
          backgroundColor: "#2196f3",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });
}

// Update resource charts with new data
function updateResourceCharts(data) {
  const timestamp = new Date().toLocaleTimeString();
  const maxDataPoints = 30; // Keep last 30 data points

  // Update CPU chart
  updateChartData(cpuChart, timestamp, data.cpu_percent, maxDataPoints);

  // Update Memory chart
  updateChartData(memoryChart, timestamp, data.memory_percent, maxDataPoints);

  // Update Disk chart
  updateChartData(diskChart, timestamp, data.disk_percent, maxDataPoints);
}

// Helper function to update chart data
function updateChartData(chart, label, value, maxPoints) {
  chart.data.labels.push(label);
  chart.data.datasets[0].data.push(value);

  if (chart.data.labels.length > maxPoints) {
    chart.data.labels.shift();
    chart.data.datasets[0].data.shift();
  }

  chart.update();
}

// Update timeline chart with activity data
function updateTimelineChart(activities) {
  timelineChart.data.labels = activities.map((a) => a.timestamp);
  timelineChart.data.datasets[0].data = activities.map((a) => a.duration);
  timelineChart.update();
}

// Update active processes list
function updateActiveProcessesList(processes) {
  const container = document.getElementById("active-processes-list");
  container.innerHTML = "";

  processes.forEach((process) => {
    const processElement = document.createElement("div");
    processElement.className = "activity-item";
    processElement.innerHTML = `
      <span class="process-name">${process.name}</span>
      <span class="process-stats">
        CPU: ${process.cpu_percent.toFixed(1)}% |
        Memory: ${process.memory_percent.toFixed(1)}%
      </span>
    `;
    container.appendChild(processElement);
  });
}

// Export functions
window.initializeCharts = initializeCharts;
window.updateResourceCharts = updateResourceCharts;
window.updateTimelineChart = updateTimelineChart;
window.updateActiveProcessesList = updateActiveProcessesList;
