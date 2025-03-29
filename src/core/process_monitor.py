import psutil
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging

class ProcessMonitor:
    def __init__(self):
        self.running = False
        self.active_processes: Dict[int, Dict] = {}
        self.start_time = datetime.now()

    def get_process_info(self, proc: psutil.Process) -> Optional[Dict]:
        """Get information about a single process"""
        try:
            with proc.oneshot():
                cpu_percent = proc.cpu_percent()
                memory_percent = proc.memory_percent()
                create_time = datetime.fromtimestamp(proc.create_time())
                name = proc.name()
                cmdline = " ".join(proc.cmdline()) if proc.cmdline() else name
                username = proc.username()

                return {
                    "pid": proc.pid,
                    "name": name,
                    "cmdline": cmdline,
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "create_time": create_time,
                    "username": username,
                    "last_updated": datetime.now()
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None

    def scan_processes(self) -> List[Dict]:
        """Scan all running processes and update active_processes"""
        current_pids = set()
        process_list = []

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = self.get_process_info(proc)
                if info:
                    current_pids.add(info['pid'])
                    self.active_processes[info['pid']] = info
                    process_list.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Remove processes that are no longer running
        ended_pids = set(self.active_processes.keys()) - current_pids
        for pid in ended_pids:
            del self.active_processes[pid]

        return process_list

    def get_system_info(self) -> Dict:
        """Get overall system information"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "timestamp": datetime.now()
        }

    def start_monitoring(self):
        """Start the monitoring process"""
        self.running = True
        self.start_time = datetime.now()

        while self.running:
            try:
                # Update process information
                processes = self.scan_processes()
                system_info = self.get_system_info()

                # Here we'll add database updates once implemented

                time.sleep(1)  # Update every second

            except Exception as e:
                logging.error(f"Error in process monitoring: {e}")
                continue

    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.running = False

    def get_active_processes(self) -> List[Dict]:
        """Get list of currently active processes"""
        return list(self.active_processes.values())

    def get_process_by_pid(self, pid: int) -> Optional[Dict]:
        """Get information about a specific process"""
        return self.active_processes.get(pid)