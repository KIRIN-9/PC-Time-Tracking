import platform
import time
import subprocess
from typing import Optional
import os

class IdleDetector:
    def __init__(self, idle_threshold: int = 300):
        self.system = platform.system()
        self.idle_threshold = idle_threshold  # 5 minutes by default
        self._last_active_time = time.time()
        self._is_idle = False
        self._reported_error = False  # Flag to prevent repeated error messages

    def get_idle_time(self) -> int:
        if self.system == "Linux":
            # Try several methods, fall back to simpler ones
            try:
                # Method 1: Try using xprintidle
                output = subprocess.check_output(["xprintidle"], stderr=subprocess.DEVNULL).decode().strip()
                return int(output) // 1000  # Convert from milliseconds to seconds
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

            try:
                # Method 2: Try using dbus-send directly with less strict dependencies
                cmd = ["dbus-send", "--session", "--dest=org.freedesktop.ScreenSaver",
                      "--type=method_call", "--print-reply", "/org/freedesktop/ScreenSaver",
                      "org.freedesktop.ScreenSaver.GetSessionIdleTime"]
                output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode()
                for line in output.splitlines():
                    if "uint32" in line:
                        return int(line.split()[-1])
                return 0
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

            try:
                # Method 3: Try using dbus with GNOME screensaver
                cmd = ["dbus-send", "--session", "--dest=org.gnome.ScreenSaver",
                      "--type=method_call", "--print-reply", "/org/gnome/ScreenSaver",
                      "org.gnome.ScreenSaver.GetSessionIdleTime"]
                output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode()
                for line in output.splitlines():
                    if "uint32" in line:
                        return int(line.split()[-1])
                return 0
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

            # Method 4: Time-based approach
            current_time = time.time()
            if not self._is_idle:
                self._last_active_time = current_time

            # If we reached this point, none of the methods worked
            # Show error only once to avoid spamming the terminal
            if not self._reported_error:
                print("Warning: Could not detect system idle time. Using basic time-based tracking.")
                self._reported_error = True

            return int(current_time - self._last_active_time)

        elif self.system == "Windows":
            try:
                import ctypes
                class LASTINPUTINFO(ctypes.Structure):
                    _fields_ = [
                        ('cbSize', ctypes.c_uint),
                        ('dwTime', ctypes.c_uint),
                    ]

                lastInputInfo = LASTINPUTINFO()
                lastInputInfo.cbSize = ctypes.sizeof(lastInputInfo)
                ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo))
                millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
                return millis // 1000
            except (ImportError, AttributeError):
                # Fall back to time-based approach
                current_time = time.time()
                if not self._is_idle:
                    self._last_active_time = current_time
                return int(current_time - self._last_active_time)

        elif self.system == "Darwin":  # macOS
            try:
                cmd = "ioreg -c IOHIDSystem | grep HIDIdleTime"
                output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
                idle_time_ns = int(output.split("=")[-1].strip().replace('"', ''))
                return idle_time_ns // 1000000000  # Convert from nanoseconds to seconds
            except (subprocess.SubprocessError, ValueError):
                # Fall back to time-based approach
                current_time = time.time()
                if not self._is_idle:
                    self._last_active_time = current_time
                return int(current_time - self._last_active_time)

        # Default fallback
        current_time = time.time()
        if not self._is_idle:
            self._last_active_time = current_time
        return int(current_time - self._last_active_time)

    def is_idle(self) -> bool:
        try:
            idle_time = self.get_idle_time()
            self._is_idle = idle_time >= self.idle_threshold
            return self._is_idle
        except Exception as e:
            # Any unexpected error should result in a non-idle state
            print(f"Error in idle detection: {e}")
            self._is_idle = False
            return False

    def update(self) -> bool:
        return self.is_idle()

    def set_idle_threshold(self, seconds: int):
        self.idle_threshold = max(1, seconds)  # Ensure positive value