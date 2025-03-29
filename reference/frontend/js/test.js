// Test script for dashboard functionality

// Mock API for testing
const mockApi = {
  async fetchProcesses(date) {
    // Generate mock process data
    const processes = [];
    const now = new Date();
    const hour = now.getHours();

    // Generate 5 processes for the current hour
    for (let i = 0; i < 5; i++) {
      processes.push({
        name: `Test Process ${i + 1}`,
        timestamp: new Date(now.getTime() - (4 - i) * 60000).toISOString(),
        category: "Development",
      });
    }

    return processes;
  },

  async fetchIdleTime(date) {
    // Generate mock idle data
    const idle = [];
    const now = new Date();
    const hour = now.getHours();

    // Generate 2 idle entries for the current hour
    for (let i = 0; i < 2; i++) {
      idle.push({
        is_idle: true,
        timestamp: new Date(now.getTime() - (1 - i) * 300000).toISOString(),
      });
    }

    return idle;
  },

  async toggleTracking(enabled) {
    console.log("Tracking toggled:", enabled);
    return { success: true };
  },

  async logBreak(startTime, endTime) {
    console.log("Break logged:", { startTime, endTime });
    return { success: true };
  },
};

// Override the real API with mock API for testing
window.api = mockApi;

// Test functions
function testTimelineChart() {
  console.log("Testing timeline chart...");
  const chart = window.timelineChart;
  if (!chart) {
    console.error("Timeline chart not initialized");
    return false;
  }

  if (!chart.data.labels || chart.data.labels.length !== 24) {
    console.error("Timeline chart labels not properly initialized");
    return false;
  }

  console.log("Timeline chart test passed");
  return true;
}

function testActivityList() {
  console.log("Testing activity list...");
  const activityList = document.getElementById("activity-list");
  if (!activityList) {
    console.error("Activity list element not found");
    return false;
  }

  const items = activityList.getElementsByClassName("activity-item");
  if (items.length === 0) {
    console.error("No activity items found");
    return false;
  }

  console.log("Activity list test passed");
  return true;
}

function testStats() {
  console.log("Testing stats display...");
  const workTime = document.getElementById("work-time");
  const breakTime = document.getElementById("break-time");
  const timeSinceBreak = document.getElementById("time-since-break");

  if (!workTime || !breakTime || !timeSinceBreak) {
    console.error("Stats elements not found");
    return false;
  }

  // Check if time format is correct (HH:MM:SS)
  const timeFormat = /^\d+:\d{2}:\d{2}$/;
  if (
    !timeFormat.test(workTime.textContent) ||
    !timeFormat.test(breakTime.textContent) ||
    !timeFormat.test(timeSinceBreak.textContent)
  ) {
    console.error("Time format is incorrect");
    return false;
  }

  console.log("Stats test passed");
  return true;
}

function testControls() {
  console.log("Testing controls...");
  const toggleBtn = document.getElementById("toggle-tracking");
  const breakBtn = document.getElementById("start-break");

  if (!toggleBtn || !breakBtn) {
    console.error("Control buttons not found");
    return false;
  }

  // Test button click handlers
  toggleBtn.click();
  if (toggleBtn.textContent !== "Stop Tracking") {
    console.error("Toggle button text not updated");
    return false;
  }

  breakBtn.click();
  if (breakBtn.textContent !== "End Break") {
    console.error("Break button text not updated");
    return false;
  }

  console.log("Controls test passed");
  return true;
}

// Run all tests
function runTests() {
  console.log("Starting dashboard tests...");

  const tests = [
    { name: "Timeline Chart", fn: testTimelineChart },
    { name: "Activity List", fn: testActivityList },
    { name: "Stats Display", fn: testStats },
    { name: "Controls", fn: testControls },
  ];

  let allPassed = true;

  tests.forEach((test) => {
    console.log(`\nRunning ${test.name} test...`);
    if (!test.fn()) {
      allPassed = false;
      console.error(`${test.name} test failed`);
    }
  });

  console.log("\nTest Summary:");
  console.log(allPassed ? "All tests passed!" : "Some tests failed");
}

// Run tests when the page loads
document.addEventListener("DOMContentLoaded", () => {
  // Wait for dashboard to initialize
  setTimeout(runTests, 1000);
});
