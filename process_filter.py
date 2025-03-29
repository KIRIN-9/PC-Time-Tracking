#!/usr/bin/env python3
"""Process filtering and prioritization for PC Time Tracking."""
import json
import os
import re
from typing import Dict, List, Optional, Set, Callable
import psutil

class ProcessFilter:
    """Filter and prioritize processes for monitoring."""

    def __init__(self, config_file: str = "process_filter.json"):
        """Initialize the process filter.

        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.excluded_processes: Set[str] = set()
        self.excluded_patterns: List[str] = []
        self.priority_processes: Dict[str, int] = {}  # process_name: priority (1-5)
        self.system_processes: bool = False  # whether to include system processes
        self.threshold_cpu: Optional[float] = None  # minimum CPU % to track
        self.threshold_memory: Optional[float] = None  # minimum Memory % to track

        # Load configuration if it exists
        if os.path.exists(config_file):
            self.load_config()
        else:
            self._create_default_config()

    def load_config(self) -> None:
        """Load filter configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            self.excluded_processes = set(config.get('excluded_processes', []))
            self.excluded_patterns = config.get('excluded_patterns', [])
            self.priority_processes = config.get('priority_processes', {})
            self.system_processes = config.get('system_processes', False)
            self.threshold_cpu = config.get('threshold_cpu')
            self.threshold_memory = config.get('threshold_memory')

        except Exception as e:
            print(f"Error loading filter configuration: {e}")
            self._create_default_config()

    def save_config(self) -> None:
        """Save filter configuration to file."""
        config = {
            'excluded_processes': list(self.excluded_processes),
            'excluded_patterns': self.excluded_patterns,
            'priority_processes': self.priority_processes,
            'system_processes': self.system_processes,
            'threshold_cpu': self.threshold_cpu,
            'threshold_memory': self.threshold_memory
        }

        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving filter configuration: {e}")

    def _create_default_config(self) -> None:
        """Create default filter configuration."""
        common_system_processes = [
            "svchost.exe", "System", "Registry", "smss.exe", "csrss.exe",
            "wininit.exe", "services.exe", "lsass.exe", "fontdrvhost.exe",
            "dwm.exe", "systemd", "kthreadd", "kworker", "rcu_sched",
            "migration", "ksoftirqd", "watchdog", "kdevtmpfs", "kauditd",
            "khugepaged", "oom_reaper", "writeback", "kcompactd", "bash"
        ]

        # Default excluded patterns
        default_patterns = [
            "^kworker.*$",
            "^rcu_.*$",
            "^migration.*$",
            "^ksoftirqd.*$",
            "^watchdog.*$",
            "^scsi_.*$"
        ]

        # Default priority processes
        default_priorities = {
            "chrome": 4,
            "firefox": 4,
            "code": 5,
            "pycharm": 5,
            "intellij": 5,
            "vscode": 5,
            "slack": 3,
            "discord": 3,
            "spotify": 2,
            "steam": 2
        }

        self.excluded_processes = set(common_system_processes)
        self.excluded_patterns = default_patterns
        self.priority_processes = default_priorities
        self.system_processes = False
        self.threshold_cpu = 0.1  # 0.1% CPU usage minimum
        self.threshold_memory = 0.1  # 0.1% Memory usage minimum

        self.save_config()

    def should_track_process(self, process_info: Dict) -> bool:
        """Check if a process should be tracked based on filters.

        Args:
            process_info: Dictionary with process information

        Returns:
            True if process should be tracked, False otherwise
        """
        process_name = process_info['name']

        # Check if explicitly excluded
        if process_name in self.excluded_processes:
            return False

        # Check excluded patterns
        for pattern in self.excluded_patterns:
            if re.match(pattern, process_name):
                return False

        # Check system process policy
        if not self.system_processes:
            try:
                # Try to determine if it's a system process
                if process_info.get('username') in ['root', 'system', 'SYSTEM', 'LOCAL SERVICE', 'NETWORK SERVICE']:
                    return False

                # Check if running as system user on Linux
                if process_info.get('uid') == 0:
                    return False
            except (KeyError, AttributeError):
                pass

        # Check thresholds
        if self.threshold_cpu is not None and process_info['cpu_percent'] < self.threshold_cpu:
            return False

        if self.threshold_memory is not None and process_info['memory_percent'] < self.threshold_memory:
            return False

        return True

    def get_process_priority(self, process_name: str) -> int:
        """Get priority level for a process (1-5, with 5 being highest).

        Args:
            process_name: Process name

        Returns:
            Priority level (1-5)
        """
        # Check exact matches
        if process_name in self.priority_processes:
            return self.priority_processes[process_name]

        # Check substring matches
        for name, priority in self.priority_processes.items():
            if name.lower() in process_name.lower():
                return priority

        return 1  # Default priority

    def apply_filter(self, processes: List[Dict]) -> List[Dict]:
        """Apply filter to a list of processes.

        Args:
            processes: List of process dictionaries

        Returns:
            Filtered list of processes
        """
        filtered = []
        for proc in processes:
            if self.should_track_process(proc):
                # Add priority information
                proc['priority'] = self.get_process_priority(proc['name'])
                filtered.append(proc)

        return filtered

    def add_excluded_process(self, process_name: str) -> None:
        """Add a process to the exclusion list.

        Args:
            process_name: Process name to exclude
        """
        self.excluded_processes.add(process_name)
        self.save_config()

    def remove_excluded_process(self, process_name: str) -> bool:
        """Remove a process from the exclusion list.

        Args:
            process_name: Process name to remove

        Returns:
            True if process was removed, False if not found
        """
        if process_name in self.excluded_processes:
            self.excluded_processes.remove(process_name)
            self.save_config()
            return True
        return False

    def add_excluded_pattern(self, pattern: str) -> None:
        """Add an exclusion pattern.

        Args:
            pattern: Regular expression pattern
        """
        if pattern not in self.excluded_patterns:
            self.excluded_patterns.append(pattern)
            self.save_config()

    def remove_excluded_pattern(self, pattern: str) -> bool:
        """Remove an exclusion pattern.

        Args:
            pattern: Pattern to remove

        Returns:
            True if pattern was removed, False if not found
        """
        if pattern in self.excluded_patterns:
            self.excluded_patterns.remove(pattern)
            self.save_config()
            return True
        return False

    def set_process_priority(self, process_name: str, priority: int) -> None:
        """Set priority for a process.

        Args:
            process_name: Process name
            priority: Priority level (1-5)
        """
        if not 1 <= priority <= 5:
            raise ValueError("Priority must be between 1 and 5")

        self.priority_processes[process_name] = priority
        self.save_config()

    def remove_process_priority(self, process_name: str) -> bool:
        """Remove priority setting for a process.

        Args:
            process_name: Process name

        Returns:
            True if setting was removed, False if not found
        """
        if process_name in self.priority_processes:
            del self.priority_processes[process_name]
            self.save_config()
            return True
        return False

    def set_threshold(self, threshold_type: str, value: Optional[float]) -> None:
        """Set resource usage threshold.

        Args:
            threshold_type: 'cpu' or 'memory'
            value: Threshold value or None to disable
        """
        if value is not None and (value < 0 or value > 100):
            raise ValueError("Threshold must be between 0 and 100")

        if threshold_type == 'cpu':
            self.threshold_cpu = value
        elif threshold_type == 'memory':
            self.threshold_memory = value
        else:
            raise ValueError("Threshold type must be 'cpu' or 'memory'")

        self.save_config()

    def set_system_processes(self, include: bool) -> None:
        """Set whether to include system processes.

        Args:
            include: True to include system processes, False to exclude
        """
        self.system_processes = include
        self.save_config()

    def get_prioritized_processes(self, processes: List[Dict]) -> List[Dict]:
        """Get processes sorted by priority (highest first).

        Args:
            processes: List of process dictionaries

        Returns:
            Sorted list of processes by priority
        """
        # Apply filter first
        filtered = self.apply_filter(processes)

        # Sort by priority (descending)
        return sorted(filtered, key=lambda p: p.get('priority', 1), reverse=True)

class ResourceLimiter:
    """Limit resource usage for specific processes."""

    def __init__(self):
        """Initialize the resource limiter."""
        self.limits = {}  # {pid: {'cpu': limit, 'memory': limit}}

    def set_cpu_limit(self, pid: int, limit_percent: int) -> bool:
        """Set CPU usage limit for a process.

        Args:
            pid: Process ID
            limit_percent: CPU usage limit (0-100)

        Returns:
            True if successful, False otherwise
        """
        if not 0 <= limit_percent <= 100:
            raise ValueError("CPU limit must be between 0 and 100")

        try:
            process = psutil.Process(pid)

            # Store limit
            if pid not in self.limits:
                self.limits[pid] = {}
            self.limits[pid]['cpu'] = limit_percent

            # On Linux, we can use cpulimit or cgroups
            # On Windows, we can use job objects
            # For now, this is just a placeholder

            return True
        except psutil.NoSuchProcess:
            return False
        except Exception as e:
            print(f"Error setting CPU limit: {e}")
            return False

    def set_memory_limit(self, pid: int, limit_mb: int) -> bool:
        """Set memory usage limit for a process.

        Args:
            pid: Process ID
            limit_mb: Memory usage limit in MB

        Returns:
            True if successful, False otherwise
        """
        try:
            process = psutil.Process(pid)

            # Store limit
            if pid not in self.limits:
                self.limits[pid] = {}
            self.limits[pid]['memory'] = limit_mb

            # Implementation would depend on platform
            # For now, this is just a placeholder

            return True
        except psutil.NoSuchProcess:
            return False
        except Exception as e:
            print(f"Error setting memory limit: {e}")
            return False

    def get_limits(self, pid: int) -> Dict:
        """Get resource limits for a process.

        Args:
            pid: Process ID

        Returns:
            Dictionary with limit information
        """
        return self.limits.get(pid, {})

    def clear_limits(self, pid: int) -> bool:
        """Clear all resource limits for a process.

        Args:
            pid: Process ID

        Returns:
            True if successful, False otherwise
        """
        if pid in self.limits:
            del self.limits[pid]

            # Would need to remove actual limits here

            return True
        return False