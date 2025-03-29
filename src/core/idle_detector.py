import psutil
import time
from datetime import datetime, timedelta
import os
from typing import Optional

class IdleDetector:
    def __init__(self, idle_threshold_minutes: int = 5):
        self.idle_threshold = timedelta(minutes=idle_threshold_minutes)
        self.last_active_time = datetime.now()
        self.is_idle = False

    def get_idle_time(self) -> timedelta:
        """Get the current idle time"""
        try:
            # Get the last input time from psutil
            cpu_times = psutil.cpu_times()
            # Some systems might not have idle time
            if hasattr(cpu_times, 'idle'):
                current_time = datetime.now()
                return current_time - self.last_active_time
        except Exception:
            pass

        return timedelta()

    def check_idle(self) -> bool:
        """Check if system is idle based on CPU activity and user input"""
        idle_time = self.get_idle_time()

        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        if cpu_percent > 20:  # If CPU usage is high, system is not idle
            self.last_active_time = datetime.now()
            self.is_idle = False
            return False

        # Check if idle threshold is exceeded
        if idle_time >= self.idle_threshold:
            self.is_idle = True
            return True

        self.is_idle = False
        return False

    def get_idle_duration(self) -> Optional[timedelta]:
        """Get how long the system has been idle"""
        if self.is_idle:
            return datetime.now() - self.last_active_time
        return None

    def reset(self):
        """Reset the idle detector"""
        self.last_active_time = datetime.now()
        self.is_idle = False