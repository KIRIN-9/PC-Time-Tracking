import psutil


import time
import platform
from typing import Dict, List, Optional
from datetime import datetime
import subprocess
from database import Database
from idle_detector import IdleDetector
from process_categorizer import ProcessCategorizer
from process_filter import ProcessFilter

class ProcessMonitor:
    def __init__(self):
        self.system = platform.system()
        self._active_window = None
        self._process_history = {}
        self.db = Database()
        self.idle_detector = IdleDetector()
        self.categorizer = ProcessCategorizer()
        self.process_filter = ProcessFilter()

    def get_running_processes(self) -> List[Dict]:
        """Get list of all running processes with their details."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
            try:
                process_info = proc.info  # info is a dict, not a method
                processes.append({
                    'pid': process_info['pid'],
                    'name': process_info['name'],
                    'cpu_percent': process_info['cpu_percent'],
                    'memory_percent': process_info['memory_percent'],
                    'create_time': datetime.fromtimestamp(process_info['create_time']).isoformat()
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Apply process filtering
        return self.process_filter.apply_filter(processes)

    def get_active_window(self) -> Optional[str]:
        """Get the currently active window title."""
        previous_window = self._active_window

        if self.system == 'Linux':
            try:
                # Try using xdotool first (more reliable)
                result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'],
                                     capture_output=True, text=True)
                if result.returncode == 0:
                    self._active_window = result.stdout.strip()
                    return self._active_window
            except FileNotFoundError:
                pass

            try:
                # Fallback to wmctrl if xdotool is not available
                import wmctrl
                window = wmctrl.Window.get_active()
                self._active_window = window.wm_name if window else None
                return self._active_window
            except (ImportError, Exception):
                return None
        elif self.system == 'Windows':
            try:
                import win32gui
                window = win32gui.GetForegroundWindow()
                self._active_window = win32gui.GetWindowText(window)
                return self._active_window
            except ImportError:
                return None
        return None

    def get_system_resources(self) -> Dict:
        """Get current system resource usage."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'percent': psutil.disk_usage('/').percent
            }
        }

    def monitor_processes(self, interval: float = 1.0):
        """Continuously monitor processes and system resources."""
        while True:
            try:
                processes = self.get_running_processes()
                active_window = self.get_active_window()
                system_resources = self.get_system_resources()

                # Categorize processes
                for proc in processes:
                    proc['category'] = self.categorizer.categorize_process(proc['name'])

                # Log the current state
                timestamp = datetime.now().isoformat()

                # Save to database
                self.db.save_process_data(timestamp, processes, active_window, system_resources)

                # Check for idle state
                idle_time = self.idle_detector.get_idle_time()
                is_idle = self.idle_detector.is_idle()

                # Add idle information to system resources
                system_resources['idle_time'] = idle_time
                system_resources['is_idle'] = is_idle

                # Keep in memory for quick access
                self._process_history[timestamp] = {
                    'processes': processes,
                    'active_window': active_window,
                    'system_resources': system_resources
                }

                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in process monitoring: {e}")
                time.sleep(interval)

    def get_process_history(self, start_time: Optional[str] = None,
                          end_time: Optional[str] = None) -> Dict:
        """Get process history from database."""
        return self.db.get_process_history(start_time, end_time)

    def get_process_summary(self, start_time: Optional[str] = None,
                          end_time: Optional[str] = None) -> Dict:
        """Get process summary statistics from database."""
        return self.db.get_process_summary(start_time, end_time)

    def get_prioritized_processes(self, limit: Optional[int] = None) -> List[Dict]:
        """Get list of processes sorted by priority."""
        processes = self.get_running_processes()
        prioritized = self.process_filter.get_prioritized_processes(processes)

        if limit:
            return prioritized[:limit]
        return prioritized