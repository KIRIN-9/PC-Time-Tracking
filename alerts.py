#!/usr/bin/env python3
"""Alert and notification system for PC Time Tracking."""
import json
import os
import time
import threading
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
import subprocess
from process_monitor import ProcessMonitor

class Alert:
    """Base alert class."""

    def __init__(self, name: str, description: str):
        """Initialize the alert.

        Args:
            name: Alert name
            description: Alert description
        """
        self.name = name
        self.description = description
        self.enabled = True
        self.triggered = False
        self.last_triggered = None
        self.cooldown = 300  # seconds (5 min default)
        self.conditions = {}
        self.actions = []

    def check(self, monitor: ProcessMonitor) -> bool:
        """Check if alert should be triggered.

        Args:
            monitor: ProcessMonitor instance

        Returns:
            True if alert should be triggered, False otherwise
        """
        raise NotImplementedError("Subclasses must implement check()")

    def trigger(self):
        """Trigger the alert and execute actions."""
        if not self.enabled:
            return

        # Check if in cooldown period
        if self.last_triggered and (datetime.now() - self.last_triggered).total_seconds() < self.cooldown:
            return

        self.triggered = True
        self.last_triggered = datetime.now()

        # Execute actions
        for action in self.actions:
            try:
                action(self)
            except Exception as e:
                logging.error(f"Error executing action for alert {self.name}: {e}")

    def add_action(self, action: Callable):
        """Add an action to execute when alert is triggered."""
        self.actions.append(action)

    def to_dict(self) -> Dict:
        """Convert alert to dictionary for serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'cooldown': self.cooldown,
            'conditions': self.conditions,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Alert':
        """Create alert from dictionary."""
        raise NotImplementedError("Subclasses must implement from_dict()")

class ResourceAlert(Alert):
    """Alert for system resource thresholds."""

    def __init__(self, name: str, description: str, resource_type: str, threshold: float):
        """Initialize the resource alert.

        Args:
            name: Alert name
            description: Alert description
            resource_type: Resource type (cpu, memory, disk)
            threshold: Threshold value (percentage)
        """
        super().__init__(name, description)
        self.resource_type = resource_type
        self.threshold = threshold
        self.conditions = {
            'resource_type': resource_type,
            'threshold': threshold
        }

    def check(self, monitor: ProcessMonitor) -> bool:
        """Check if resource usage exceeds threshold."""
        resources = monitor.get_system_resources()

        if self.resource_type == 'cpu':
            usage = resources['cpu_percent']
        elif self.resource_type == 'memory':
            usage = resources['memory']['percent']
        elif self.resource_type == 'disk':
            usage = resources['disk']['percent']
        else:
            return False

        if usage >= self.threshold:
            self.trigger()
            return True

        return False

    @classmethod
    def from_dict(cls, data: Dict) -> 'ResourceAlert':
        """Create resource alert from dictionary."""
        alert = cls(
            data['name'],
            data['description'],
            data['conditions']['resource_type'],
            data['conditions']['threshold']
        )
        alert.enabled = data['enabled']
        alert.cooldown = data['cooldown']
        if data['last_triggered']:
            alert.last_triggered = datetime.fromisoformat(data['last_triggered'])
        return alert

class ProcessAlert(Alert):
    """Alert when specific processes are detected."""

    def __init__(self, name: str, description: str, process_name: str,
                duration: Optional[int] = None, cpu_threshold: Optional[float] = None):
        """Initialize the process alert.

        Args:
            name: Alert name
            description: Alert description
            process_name: Name of process to monitor
            duration: Optional duration threshold in seconds
            cpu_threshold: Optional CPU usage threshold
        """
        super().__init__(name, description)
        self.process_name = process_name
        self.duration = duration
        self.cpu_threshold = cpu_threshold
        self.process_start_time = {}  # track when processes started
        self.conditions = {
            'process_name': process_name,
            'duration': duration,
            'cpu_threshold': cpu_threshold
        }

    def check(self, monitor: ProcessMonitor) -> bool:
        """Check if process alert should be triggered."""
        processes = monitor.get_running_processes()
        now = datetime.now()

        # Find matching processes
        matching = [p for p in processes if self.process_name.lower() in p['name'].lower()]

        if not matching:
            # Process not running, clear tracking
            self.process_start_time = {}
            return False

        for proc in matching:
            pid = proc['pid']

            # Track start time if not already tracking
            if pid not in self.process_start_time:
                self.process_start_time[pid] = now

            # Check CPU threshold if specified
            if self.cpu_threshold and proc['cpu_percent'] >= self.cpu_threshold:
                self.trigger()
                return True

            # Check duration threshold if specified
            if self.duration:
                duration = (now - self.process_start_time[pid]).total_seconds()
                if duration >= self.duration:
                    self.trigger()
                    return True

        # If no specific thresholds, trigger on process presence
        if not self.duration and not self.cpu_threshold:
            self.trigger()
            return True

        return False

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProcessAlert':
        """Create process alert from dictionary."""
        alert = cls(
            data['name'],
            data['description'],
            data['conditions']['process_name'],
            data['conditions'].get('duration'),
            data['conditions'].get('cpu_threshold')
        )
        alert.enabled = data['enabled']
        alert.cooldown = data['cooldown']
        if data['last_triggered']:
            alert.last_triggered = datetime.fromisoformat(data['last_triggered'])
        return alert

class CategoryAlert(Alert):
    """Alert when time spent in a category exceeds threshold."""

    def __init__(self, name: str, description: str, category: str,
                hours_threshold: float, period_hours: int = 24):
        """Initialize the category alert.

        Args:
            name: Alert name
            description: Alert description
            category: Category name to monitor
            hours_threshold: Hours threshold
            period_hours: Time period to check (default: 24h)
        """
        super().__init__(name, description)
        self.category = category
        self.hours_threshold = hours_threshold
        self.period_hours = period_hours
        self.conditions = {
            'category': category,
            'hours_threshold': hours_threshold,
            'period_hours': period_hours
        }

    def check(self, monitor: ProcessMonitor) -> bool:
        """Check if category time exceeds threshold."""
        from process_categorizer import ProcessCategorizer
        categorizer = ProcessCategorizer()

        category_data = categorizer.get_category_summary(self.period_hours)
        if self.category not in category_data:
            return False

        hours_spent = category_data[self.category] / 3600  # convert seconds to hours

        if hours_spent >= self.hours_threshold:
            self.trigger()
            return True

        return False

    @classmethod
    def from_dict(cls, data: Dict) -> 'CategoryAlert':
        """Create category alert from dictionary."""
        alert = cls(
            data['name'],
            data['description'],
            data['conditions']['category'],
            data['conditions']['hours_threshold'],
            data['conditions'].get('period_hours', 24)
        )
        alert.enabled = data['enabled']
        alert.cooldown = data['cooldown']
        if data['last_triggered']:
            alert.last_triggered = datetime.fromisoformat(data['last_triggered'])
        return alert

class IdleAlert(Alert):
    """Alert when system has been idle for specified time."""

    def __init__(self, name: str, description: str, idle_minutes: int):
        """Initialize the idle alert.

        Args:
            name: Alert name
            description: Alert description
            idle_minutes: Idle time threshold in minutes
        """
        super().__init__(name, description)
        self.idle_minutes = idle_minutes
        self.conditions = {
            'idle_minutes': idle_minutes
        }

    def check(self, monitor: ProcessMonitor) -> bool:
        """Check if idle time exceeds threshold."""
        idle_time = monitor.idle_detector.get_idle_time()
        idle_minutes = idle_time / 60

        if idle_minutes >= self.idle_minutes:
            self.trigger()
            return True

        return False

    @classmethod
    def from_dict(cls, data: Dict) -> 'IdleAlert':
        """Create idle alert from dictionary."""
        alert = cls(
            data['name'],
            data['description'],
            data['conditions']['idle_minutes']
        )
        alert.enabled = data['enabled']
        alert.cooldown = data['cooldown']
        if data['last_triggered']:
            alert.last_triggered = datetime.fromisoformat(data['last_triggered'])
        return alert

# Alert actions
def desktop_notification(alert: Alert):
    """Show desktop notification."""
    title = f"PC Time Tracking - {alert.name}"
    message = alert.description

    try:
        if os.name == 'posix':  # Linux/Mac
            subprocess.run(['notify-send', title, message])
        elif os.name == 'nt':  # Windows
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, message, duration=5)
    except Exception as e:
        logging.error(f"Failed to show notification: {e}")

def log_alert(alert: Alert):
    """Log alert to file."""
    logging.info(f"Alert triggered: {alert.name} - {alert.description}")

def play_sound(alert: Alert):
    """Play alert sound."""
    try:
        if os.name == 'posix':  # Linux
            subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/bell.oga'])
        elif os.name == 'nt':  # Windows
            import winsound
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
    except Exception as e:
        logging.error(f"Failed to play sound: {e}")

class AlertManager:
    """Manage alerts and notifications."""

    def __init__(self, config_file: str = "alerts_config.json"):
        """Initialize the alert manager.

        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.alerts = []
        self.history = []
        self.running = False
        self.monitor = None
        self.monitor_thread = None

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename='alerts.log'
        )

        # Load configuration if exists
        self.load_config()

    def load_config(self):
        """Load alert configuration from file."""
        if not os.path.exists(self.config_file):
            self.create_default_config()
            return

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            self.alerts = []
            for alert_data in config['alerts']:
                alert_type = alert_data.pop('type', None)
                if alert_type == 'resource':
                    alert = ResourceAlert.from_dict(alert_data)
                elif alert_type == 'process':
                    alert = ProcessAlert.from_dict(alert_data)
                elif alert_type == 'category':
                    alert = CategoryAlert.from_dict(alert_data)
                elif alert_type == 'idle':
                    alert = IdleAlert.from_dict(alert_data)
                else:
                    continue

                # Add default actions
                alert.add_action(log_alert)
                alert.add_action(desktop_notification)

                self.alerts.append(alert)

            logging.info(f"Loaded {len(self.alerts)} alerts from config")

        except Exception as e:
            logging.error(f"Error loading config: {e}")
            self.create_default_config()

    def create_default_config(self):
        """Create default alert configuration."""
        self.alerts = [
            ResourceAlert("High CPU Usage", "CPU usage exceeds 90%", "cpu", 90.0),
            ResourceAlert("High Memory Usage", "Memory usage exceeds 85%", "memory", 85.0),
            ResourceAlert("High Disk Usage", "Disk usage exceeds 90%", "disk", 90.0),
            IdleAlert("Long Idle", "System has been idle for 30 minutes", 30),
            CategoryAlert("Entertainment Limit", "Entertainment time exceeds 2 hours", "entertainment", 2.0)
        ]

        # Add default actions
        for alert in self.alerts:
            alert.add_action(log_alert)
            alert.add_action(desktop_notification)

        self.save_config()
        logging.info("Created default alert configuration")

    def save_config(self):
        """Save alert configuration to file."""
        config = {
            'alerts': []
        }

        for alert in self.alerts:
            alert_data = alert.to_dict()

            # Add type information
            if isinstance(alert, ResourceAlert):
                alert_data['type'] = 'resource'
            elif isinstance(alert, ProcessAlert):
                alert_data['type'] = 'process'
            elif isinstance(alert, CategoryAlert):
                alert_data['type'] = 'category'
            elif isinstance(alert, IdleAlert):
                alert_data['type'] = 'idle'

            config['alerts'].append(alert_data)

        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logging.info(f"Saved configuration with {len(self.alerts)} alerts")
        except Exception as e:
            logging.error(f"Error saving config: {e}")

    def add_alert(self, alert: Alert):
        """Add a new alert."""
        self.alerts.append(alert)
        self.save_config()

    def remove_alert(self, alert_name: str) -> bool:
        """Remove an alert by name."""
        for i, alert in enumerate(self.alerts):
            if alert.name == alert_name:
                del self.alerts[i]
                self.save_config()
                return True
        return False

    def get_alert(self, alert_name: str) -> Optional[Alert]:
        """Get an alert by name."""
        for alert in self.alerts:
            if alert.name == alert_name:
                return alert
        return None

    def check_alerts(self):
        """Check all alerts."""
        if not self.monitor:
            return

        triggered = []
        for alert in self.alerts:
            if alert.enabled and alert.check(self.monitor):
                triggered.append(alert)
                self.history.append({
                    'name': alert.name,
                    'time': datetime.now().isoformat(),
                    'description': alert.description
                })

        # Keep history limited to last 100 entries
        if len(self.history) > 100:
            self.history = self.history[-100:]

        return triggered

    def start_monitoring(self, monitor: ProcessMonitor, interval: float = 60.0):
        """Start monitoring thread to check alerts periodically.

        Args:
            monitor: ProcessMonitor instance to use
            interval: Check interval in seconds
        """
        if self.running:
            return

        self.monitor = monitor
        self.running = True

        def _monitor_thread():
            while self.running:
                try:
                    self.check_alerts()
                except Exception as e:
                    logging.error(f"Error checking alerts: {e}")
                time.sleep(interval)

        self.monitor_thread = threading.Thread(target=_monitor_thread, daemon=True)
        self.monitor_thread.start()
        logging.info(f"Started alert monitoring with interval {interval}s")

    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logging.info("Stopped alert monitoring")

    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get alert history.

        Args:
            limit: Maximum number of history entries to return

        Returns:
            List of alert history entries
        """
        return self.history[-limit:]