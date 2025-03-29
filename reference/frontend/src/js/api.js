import { apiUrl } from "./config.js";

export async function fetchProcesses(sortBy = "cpu", limit = 10) {
  const response = await fetch(
    apiUrl(`processes?sort_by=${sortBy}&limit=${limit}`)
  );
  return response.json();
}

export async function fetchResources() {
  const response = await fetch(apiUrl("resources"));
  return response.json();
}

export async function fetchCategories(hours = 24) {
  const response = await fetch(apiUrl(`categories?hours=${hours}`));
  return response.json();
}

export async function fetchStats(hours = 24) {
  const response = await fetch(apiUrl(`stats?hours=${hours}`));
  return response.json();
}

export async function fetchFilters() {
  const response = await fetch(apiUrl("filter"));
  return response.json();
}

export async function excludeProcess(processName) {
  const response = await fetch(
    apiUrl(`filter/exclude?process_name=${encodeURIComponent(processName)}`),
    {
      method: "POST",
    }
  );
  return response.json();
}

export async function includeProcess(processName) {
  const response = await fetch(
    apiUrl(`filter/include?process_name=${encodeURIComponent(processName)}`),
    {
      method: "POST",
    }
  );
  return response.json();
}

export async function addPattern(pattern) {
  const response = await fetch(apiUrl("filter/pattern"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pattern }),
  });
  return response.json();
}

export async function removePattern(pattern) {
  const response = await fetch(apiUrl("filter/remove-pattern"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pattern }),
  });
  return response.json();
}

export async function setPriority(processName, priority) {
  const response = await fetch(apiUrl("filter/priority"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ process_name: processName, priority }),
  });
  return response.json();
}

export async function removePriority(processName) {
  const response = await fetch(
    apiUrl(
      `filter/remove-priority?process_name=${encodeURIComponent(processName)}`
    ),
    {
      method: "POST",
    }
  );
  return response.json();
}

export async function setCpuThreshold(threshold) {
  const response = await fetch(apiUrl("filter/cpu-threshold"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ threshold }),
  });
  return response.json();
}

export async function setMemoryThreshold(threshold) {
  const response = await fetch(apiUrl("filter/memory-threshold"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ threshold }),
  });
  return response.json();
}

export async function setSystemProcesses(include) {
  const response = await fetch(apiUrl("filter/system"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ include }),
  });
  return response.json();
}

export async function resetFilters() {
  const response = await fetch(apiUrl("filter/reset"), { method: "POST" });
  return response.json();
}

export async function exportData(dataType = "all", hours = 24, format = "csv") {
  const response = await fetch(
    apiUrl(`export?data_type=${dataType}&hours=${hours}&format=${format}`)
  );
  return response.json();
}
