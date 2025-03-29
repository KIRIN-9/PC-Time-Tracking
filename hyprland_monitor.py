import json
import socket
import os
import threading
from datetime import datetime

class HyprlandMonitor:
    def __init__(self):
        self.socket_path = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
        if not self.socket_path:
            raise EnvironmentError("HYPRLAND_INSTANCE_SIGNATURE not found")
        self.socket_path = f"/tmp/hypr/{self.socket_path}/.socket2.sock"
        self.running = True
        self.callbacks = {
            'workspace': [],
            'activewindow': [],
            'focusedmon': []
        }
        self.current_window = None
        self._start_monitor()

    def _start_monitor(self):
        """Start the Hyprland event monitor in a separate thread."""
        self.monitor_thread = threading.Thread(target=self._monitor_events)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def _monitor_events(self):
        """Monitor Hyprland events through the socket."""
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.socket_path)

            while self.running:
                try:
                    data = sock.recv(1024).decode()
                    if not data:
                        continue

                    for line in data.strip().split('\n'):
                        event_type, *event_data = line.split('>>')
                        if not event_data:
                            continue

                        event_data = event_data[0]
                        if event_type == 'activewindow':
                            self._handle_window_change(event_data)
                        elif event_type == 'workspace':
                            self._handle_workspace_change(event_data)
                        elif event_type == 'focusedmon':
                            self._handle_monitor_change(event_data)

                except (socket.error, UnicodeDecodeError) as e:
                    print(f"Socket error: {e}")
                    break

        except Exception as e:
            print(f"Error in Hyprland monitor: {e}")
        finally:
            sock.close()

    def _handle_window_change(self, window_data):
        """Handle window focus change events."""
        self.current_window = window_data
        for callback in self.callbacks['activewindow']:
            callback(window_data)

    def _handle_workspace_change(self, workspace_data):
        """Handle workspace change events."""
        for callback in self.callbacks['workspace']:
            callback(workspace_data)

    def _handle_monitor_change(self, monitor_data):
        """Handle monitor focus change events."""
        for callback in self.callbacks['focusedmon']:
            callback(monitor_data)

    def on_window_change(self, callback):
        """Register a callback for window focus changes."""
        self.callbacks['activewindow'].append(callback)

    def on_workspace_change(self, callback):
        """Register a callback for workspace changes."""
        self.callbacks['workspace'].append(callback)

    def on_monitor_change(self, callback):
        """Register a callback for monitor focus changes."""
        self.callbacks['focusedmon'].append(callback)

    def get_current_window(self):
        """Get the currently focused window."""
        return self.current_window

    def stop(self):
        """Stop the Hyprland monitor."""
        self.running = False
