#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Process monitor module for PC Time Tracker
Monitors system processes and resources
"""

import os
import time
import datetime
import platform
import psutil
from typing import Dict, List, Any, Optional, Tuple

from .database import Database
from .filter import ProcessFilter
from .idle import IdleDetector
from .categorizer import ProcessCategorizer

class ProcessMonitor:
    """
    Monitor system processes and resources
    """

    def __init__(self, db: Database, process_filter: ProcessFilter, idle_detector: IdleDetector, categorizer: ProcessCategorizer):
        self.db = db
        self.process_filter = process_filter
        self.idle_detector = idle_detector
        self.categorizer = categorizer
        self.running = False
        self.start_time = None
        self.active_window_provider = self._get_active_window_provider()

    def _get_active_window_provider(self) -> Optional[callable]:
        """Get the appropriate active window provider based on the OS"""
        system = platform.system()

        if system == 'Windows':
            try:
                import win32gui
                def get_active_window_win():
                    try:
                        window = win32gui.GetForegroundWindow()
                        return win32gui.GetWindowText(window)
                    except Exception:
                        return None
                return get_active_window_win
            except ImportError:
                print("Warning: win32gui not available. Active window tracking disabled.")
                return lambda: None

        elif system == 'Darwin':  # macOS
            try:
                from AppKit import NSWorkspace
                def get_active_window_mac():
                    try:
                        return NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
                    except Exception:
                        return None
                return get_active_window_mac
            except ImportError:
                print("Warning: AppKit not available. Active window tracking disabled.")
                return lambda: None

        elif system == 'Linux':
            try:
                import subprocess
                def get_active_window_linux():
                    """Get the active window title in Wayland"""
                    try:
                        # Try swaymsg for Sway
                        try:
                            result = subprocess.run(
                                ["swaymsg", "-t", "get_tree"],
                                capture_output=True, text=True, check=False
                            )
                            if result.returncode == 0:
                                import json
                                tree = json.loads(result.stdout)
                                # Find the focused window
                                def find_focused(node):
                                    if node.get('focused'):
                                        return node.get('name')
                                    for child in node.get('nodes', []):
                                        result = find_focused(child)
                                        if result:
                                            return result
                                    return None
                                return find_focused(tree)
                        except Exception:
                            pass

                        # Try wl-paste for Wayland
                        try:
                            result = subprocess.run(
                                ["wl-paste", "-t", "text/plain"],
                                capture_output=True, text=True, check=False
                            )
                            if result.returncode == 0:
                                return result.stdout.strip()
                        except Exception:
                            pass

                        # Try wl-clipboard as fallback
                        try:
                            result = subprocess.run(
                                ["wl-clipboard", "-t", "text/plain"],
                                capture_output=True, text=True, check=False
                            )
                            if result.returncode == 0:
                                return result.stdout.strip()
                        except Exception:
                            pass

                    except Exception as e:
                        print(f"Warning: Error getting active window: {e}")

                    return None
                return get_active_window_linux
            except ImportError:
                print("Warning: Required tools not available. Active window tracking disabled.")
                return lambda: None

        else:
            print(f"Warning: Unsupported platform {system}. Active window tracking disabled.")
            return lambda: None

    def start_monitoring(self, interval: float = 5.0) -> None:
        """
        Start monitoring processes and resources

        Args:
            interval: Monitoring interval in seconds
        """
        if self.running:
            return

        self.running = True
        self.start_time = time.time()
        print(f"Starting process monitoring with interval {interval} seconds")

        try:
            while self.running:
                # Check if system is idle
                idle_time = self.idle_detector.get_idle_time()
                is_idle = self.idle_detector.is_idle()

                # Save idle time to database
                self.db.save_idle_time(is_idle, idle_time)

                # Skip process monitoring if system is idle
                if not is_idle:
                    self._monitor_processes()

                # Always monitor system resources
                self._monitor_system_resources()

                # Sleep for the specified interval
                time.sleep(interval)

        except KeyboardInterrupt:
            print("Process monitoring stopped by user")
        except Exception as e:
            print(f"Error in process monitoring: {e}")
        finally:
            self.running = False

    def stop_monitoring(self) -> None:
        """Stop monitoring processes and resources"""
        self.running = False

    def get_uptime(self) -> float:
        """Get monitoring uptime in seconds"""
        if self.start_time is None:
            return 0
        return time.time() - self.start_time

    def _monitor_processes(self) -> None:
        """Monitor system processes"""
        try:
            active_window = self.active_window_provider()
            timestamp = datetime.datetime.now()

            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
                try:
                    proc_info = proc.info

                    # Apply process filtering
                    if not self.process_filter.should_include_process(proc):
                        continue

                    # Determine process priority
                    priority = self.process_filter.get_process_priority(proc)

                    # Categorize the process
                    category = self.categorizer.categorize_process(proc_info['name'])

                    # Save process to database
                    process_data = {
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'cpu_percent': proc_info['cpu_percent'],
                        'memory_percent': proc_info['memory_percent'],
                        'category': category,
                        'active_window': active_window,
                        'create_time': datetime.datetime.fromtimestamp(proc_info['create_time']).isoformat() if proc_info['create_time'] else None,
                        'timestamp': timestamp.isoformat()
                    }

                    self.db.save_process(process_data)

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    print(f"Error processing {proc.info['name'] if 'name' in proc.info else 'unknown'}: {e}")

        except Exception as e:
            print(f"Error monitoring processes: {e}")

    def _monitor_system_resources(self) -> None:
        """Monitor system resources"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            resource_data = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'memory_total': memory.total,
                'memory_available': memory.available,
                'timestamp': datetime.datetime.now().isoformat()
            }

            self.db.save_resource(resource_data)

        except Exception as e:
            print(f"Error monitoring system resources: {e}")