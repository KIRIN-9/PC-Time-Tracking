#!/usr/bin/env python3
import os
import sys
import time
import threading
import signal
import argparse
from typing import Dict, Optional

# Core components
from backend.core.monitor import ProcessMonitor
from backend.core.filter import ProcessFilter
from backend.core.database import Database
from backend.core.idle import IdleDetector
from backend.core.categorizer import ProcessCategorizer

# Import API if available
try:
    from backend.api.api_server import start_api_server
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False

class PCTimeTracker:
    def __init__(self, config_dir: Optional[str] = None):
        # Set up configuration directory
        self.config_dir = config_dir or os.path.expanduser("~/.pc_time_tracker")
        os.makedirs(self.config_dir, exist_ok=True)

        # Change working directory to config dir
        os.chdir(self.config_dir)

        # Initialize components
        self.db = Database()
        self.idle_detector = IdleDetector(idle_threshold=300)  # 5 minutes
        self.categorizer = ProcessCategorizer()
        self.process_filter = ProcessFilter()

        # Initialize monitor with all components
        self.monitor = ProcessMonitor(
            db_manager=self.db,
            idle_detector=self.idle_detector,
            categorizer=self.categorizer,
            process_filter=self.process_filter
        )

        # State
        self.running = False
        self.api_thread = None

    def start(self, interval: float = 2.0, with_api: bool = False, api_port: int = 8000):
        self.running = True

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Start the monitor
        print(f"Starting PC Time Tracker with {interval}s update interval")
        self.monitor.start(interval=interval)

        # Start API server if requested
        if with_api and API_AVAILABLE:
            self.api_thread = threading.Thread(
                target=start_api_server,
                kwargs={"host": "0.0.0.0", "port": api_port},
                daemon=True
            )
            self.api_thread.start()
            print(f"API server running at http://localhost:{api_port}")

        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        print("Stopping PC Time Tracker...")
        self.running = False

        # Stop the monitor
        if hasattr(self, 'monitor'):
            self.monitor.stop()

        print("PC Time Tracker stopped")

    def signal_handler(self, sig, frame):
        self.stop()
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="PC Time Tracking")

    parser.add_argument("--interval", "-i", type=float, default=2.0,
                      help="Update interval in seconds")
    parser.add_argument("--config-dir", "-c", type=str,
                      help="Configuration directory path")
    parser.add_argument("--api", action="store_true",
                      help="Start the API server")
    parser.add_argument("--api-port", type=int, default=8000,
                      help="API server port")

    args = parser.parse_args()

    app = PCTimeTracker(config_dir=args.config_dir)
    app.start(interval=args.interval, with_api=args.api, api_port=args.api_port)

if __name__ == "__main__":
    main()