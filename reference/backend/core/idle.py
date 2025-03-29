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
            # Check if we're running under Wayland
            is_wayland = os.environ.get('XDG_SESSION_TYPE') == 'wayland'

            if is_wayland:
                try:
                    # Try swayidle for Wayland
                    result = subprocess.run(
                        ["swayidle", "timeout", "1", "echo", "idle"],
                        capture_output=True, text=True, check=False
                    )
                    if result.returncode == 0:
                        return int(time.time() - self._last_active_time)
                except Exception:
                    pass

                try:
                    # Try wl-paste for Wayland
                    result = subprocess.run(
                        ["wl-paste", "-t", "text/plain"],
                        capture_output=True, text=True, check=False
                    )
                    if result.returncode == 0:
                        self._last_active_time = time.time()
                        return 0
                except Exception:
                    pass
            else:
                # Try several methods for X11, fall back to simpler ones
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

            # If all methods fail, use a simple time-based approach
            if not self._reported_error:
                print("Warning: Could not detect system idle time. Using basic time-based tracking.")
                self._reported_error = True
            return int(time.time() - self._last_active_time)

        elif self.system == "Windows":
            try:
                import ctypes
                from ctypes import wintypes

                class LASTINPUTINFO(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", wintypes.UINT),
                        ("dwTime", wintypes.DWORD),
                    ]

                lastInputInfo = LASTINPUTINFO()
                lastInputInfo.cbSize = ctypes.sizeof(lastInputInfo)
                ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo))
                millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
                return millis // 1000  # Convert to seconds
            except Exception:
                if not self._reported_error:
                    print("Warning: Could not detect system idle time. Using basic time-based tracking.")
                    self._reported_error = True
                return int(time.time() - self._last_active_time)

        elif self.system == "Darwin":  # macOS
            try:
                from AppKit import NSEvent
                last_event = NSEvent.lastEvent()
                if last_event:
                    return int(time.time() - last_event.timestamp())
                return 0
            except Exception:
                if not self._reported_error:
                    print("Warning: Could not detect system idle time. Using basic time-based tracking.")
                    self._reported_error = True
                return int(time.time() - self._last_active_time)

        else:
            if not self._reported_error:
                print(f"Warning: Unsupported platform {self.system}. Using basic time-based tracking.")
                self._reported_error = True
            return int(time.time() - self._last_active_time)

    def is_idle(self) -> bool:
        """Check if the system is idle"""
        idle_time = self.get_idle_time()
        return idle_time >= self.idle_threshold

    def update(self) -> bool:
        """Update idle state and return True if state changed"""
        was_idle = self._is_idle
        self._is_idle = self.is_idle()
        return was_idle != self._is_idle

    def set_idle_threshold(self, seconds: int):
        """Set the idle threshold in seconds"""
        self.idle_threshold = seconds