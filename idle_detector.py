"""Idle time detection module for PC Time Tracking."""
import time
import platform
from typing import Optional, Tuple, List
from datetime import datetime, timedelta
import subprocess

class IdleDetector:
    def __init__(self, idle_threshold: int = 300):  # Default 5 minutes
        """Initialize the idle detector.

        Args:
            idle_threshold: Time in seconds before considering system as idle
        """
        self.system = platform.system()
        self.idle_threshold = idle_threshold
        self.last_activity_time = datetime.now()
        self._last_input_check = datetime.now()
        self._idle_periods = []
        self._currently_idle = False
        self._idle_start_time = None

    def get_idle_time(self) -> int:
        """Get the current idle time in seconds."""
        if self.system == 'Linux':
            return self._get_linux_idle_time()
        elif self.system == 'Windows':
            return self._get_windows_idle_time()
        return 0

    def _get_linux_idle_time(self) -> int:
        """Get idle time on Linux using xprintidle."""
        try:
            result = subprocess.run(['xprintidle'],
                                 capture_output=True,
                                 text=True)
            if result.returncode == 0:
                # xprintidle returns milliseconds
                return int(result.stdout.strip()) // 1000
        except FileNotFoundError:
            # Fallback to basic detection
            return self._basic_idle_detection()
        return 0

    def _get_windows_idle_time(self) -> int:
        """Get idle time on Windows using GetLastInputInfo."""
        try:
            import win32api
            return (win32api.GetTickCount() - win32api.GetLastInputInfo()) // 1000
        except ImportError:
            # Fallback to basic detection
            return self._basic_idle_detection()

    def _basic_idle_detection(self) -> int:
        """Basic idle detection based on active window changes."""
        current_time = datetime.now()
        return int((current_time - self._last_input_check).total_seconds())

    def is_idle(self) -> bool:
        """Check if the system is considered idle."""
        idle_time = self.get_idle_time()
        is_idle = idle_time >= self.idle_threshold

        # Track idle periods
        if is_idle and not self._currently_idle:
            self._currently_idle = True
            self._idle_start_time = datetime.now() - timedelta(seconds=idle_time)
        elif not is_idle and self._currently_idle:
            self._currently_idle = False
            if self._idle_start_time:
                # Record the idle period
                end_time = datetime.now()
                self._idle_periods.append((self._idle_start_time, end_time))
                self._idle_start_time = None

        return is_idle

    def update_activity(self) -> None:
        """Update the last activity time."""
        self._last_input_check = datetime.now()
        if self._currently_idle:
            self._currently_idle = False
            if self._idle_start_time:
                # Record the idle period that just ended
                end_time = datetime.now()
                self._idle_periods.append((self._idle_start_time, end_time))
                self._idle_start_time = None

    def get_idle_periods(self, start_time: datetime, end_time: datetime) -> List[Tuple[datetime, datetime]]:
        """Get list of idle periods between start and end time."""
        return [
            period for period in self._idle_periods
            if period[0] >= start_time and period[1] <= end_time
        ]