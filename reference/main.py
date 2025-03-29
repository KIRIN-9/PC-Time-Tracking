#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PC Time Tracker - Main CLI Interface
A bpytop-like interface for tracking process and productivity metrics
"""

import os
import sys
import time
import argparse
import threading
import webbrowser
import signal
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Dict, List, Any, Optional
import importlib
from dotenv import load_dotenv
from src.core.monitor import ProcessMonitor
from src.ui.dashboard import Dashboard
from src.database.connection import create_db_connection

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import backend modules
# Fix imports - import directly from the file instead of assuming symbols are exported
import backend.api as api_module
from backend.core.filter import ProcessFilter
from backend.core.categorizer import ProcessCategorizer
from backend.core.database import Database
from backend.core.idle import IdleDetector
from backend.core.monitor import ProcessMonitor

# Constants
DEFAULT_API_PORT = 5000
DEFAULT_WEB_PORT = 8080
FRONTEND_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')

# Global variables
api_server_thread = None
web_server_thread = None
monitor_thread = None
should_exit = False
components = {}

def signal_handler(sig, frame):
    """Handle signals to gracefully shut down the application"""
    global should_exit
    print("\nShutting down PC Time Tracker...")
    should_exit = True
    if 'monitor' in components:
        components['monitor'].stop_monitoring()
    sys.exit(0)

def run_web_server(port: int = DEFAULT_WEB_PORT):
    """Run a simple HTTP server for the frontend"""
    # Create a backup of the current directory
    original_dir = os.getcwd()

    try:
        # Change to the frontend directory
        os.chdir(FRONTEND_PATH)

        # Create a custom HTTP request handler that sets CORS headers
        class CORSRequestHandler(SimpleHTTPRequestHandler):
            def end_headers(self):
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                SimpleHTTPRequestHandler.end_headers(self)

        # Create and start the server
        server = HTTPServer(('0.0.0.0', port), CORSRequestHandler)
        print(f"Web server running at http://localhost:{port}/")

        try:
            server.serve_forever()
        except Exception as e:
            print(f"Web server error: {e}")
        finally:
            server.server_close()

    finally:
        # Change back to the original directory
        os.chdir(original_dir)

def setup_components():
    """Initialize all components for direct usage"""
    global components

    # Initialize database
    db = Database()
    db.init_schema()
    components['db'] = db

    # Initialize process filter
    process_filter = ProcessFilter()
    components['filter'] = process_filter

    # Initialize idle detector
    idle_detector = IdleDetector()
    components['idle'] = idle_detector

    # Initialize categorizer
    categorizer = ProcessCategorizer()
    components['categorizer'] = categorizer

    # Initialize process monitor
    monitor = ProcessMonitor(db, process_filter, idle_detector, categorizer)
    components['monitor'] = monitor

    return components

def start_api_server(port=5000, debug=False):
    """Start the API server in a separate thread"""
    api_module = importlib.import_module('backend.api')
    api_thread = threading.Thread(
        target=api_module.app.run,
        kwargs={'host': '0.0.0.0', 'port': port, 'debug': debug}
    )
    api_thread.daemon = True
    api_thread.start()
    print(f"API server running at http://localhost:{port}/")

def start_servers(api_port: int = DEFAULT_API_PORT, web_port: int = DEFAULT_WEB_PORT, open_browser: bool = True):
    """Start the API and web servers"""
    global api_server_thread, web_server_thread

    # Start the API server in a separate thread
    api_server_thread = threading.Thread(
        target=start_api_server,
        args=(api_port, False),
        daemon=True
    )
    api_server_thread.start()

    # Start the web server in a separate thread
    web_server_thread = threading.Thread(
        target=run_web_server,
        args=(web_port,),
        daemon=True
    )
    web_server_thread.start()

    # Wait a moment for servers to start
    time.sleep(2)

    # Open browser if requested
    if open_browser:
        webbrowser.open(f'http://localhost:{web_port}')

    print(f"API server running at http://localhost:{api_port}/")
    print(f"Web interface available at http://localhost:{web_port}/")
    print("\nPress Ctrl+C to stop the servers")

def test_monitoring():
    """Test the process monitoring functionality"""
    # Setup components
    components = setup_components()

    print("Starting monitoring for 30 seconds...")
    # Start monitoring in the main thread (not daemon)
    monitor_thread = threading.Thread(
        target=components['monitor'].start_monitoring,
        args=(5.0,),  # 5 second interval
        daemon=True
    )
    monitor_thread.start()

    # Wait for 30 seconds
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        # Stop monitoring
        components['monitor'].stop_monitoring()
        print("Monitoring stopped")

        # Print some statistics
        print("\nProcess Monitoring Statistics:")
        print(f"Uptime: {components['monitor'].get_uptime():.2f} seconds")

        # List processes from the database
        processes = components['db'].get_processes_in_range(
            time.time() - 3600,  # Last hour
            time.time()
        )
        print(f"Processes recorded: {len(processes)}")

        # List resources from the database
        resources = components['db'].get_resources_in_range(
            time.time() - 3600,  # Last hour
            time.time()
        )
        print(f"Resource records: {len(resources)}")

        # List idle times from the database
        idle_times = components['db'].get_idle_times_in_range(
            time.time() - 3600,  # Last hour
            time.time()
        )
        print(f"Idle time records: {len(idle_times)}")

def test_filters():
    """Test the process filter functionality"""
    # Setup components
    components = setup_components()

    print("\nTesting Process Filters:")

    # Get a process filter instance
    process_filter = components['filter']

    # Print current filter settings
    print("\nCurrent filter settings:")
    print(f"CPU threshold: {process_filter.cpu_threshold}%")
    print(f"Memory threshold: {process_filter.memory_threshold}%")
    print(f"Include system processes: {process_filter.include_system_processes}")

    # Print excluded processes (limit to 10 for brevity)
    excluded_processes = list(process_filter.excluded_processes)[:10]
    if excluded_processes:
        print("\nSome excluded processes:")
        for proc in excluded_processes:
            print(f"  - {proc}")
    else:
        print("\nNo excluded processes")

    # Test filtering a specific process
    import psutil
    current_process = psutil.Process()
    should_include = process_filter.should_include_process(current_process)
    print(f"\nShould include current process ({current_process.name()}): {should_include}")

    # Test setting a process priority
    print("\nSetting process priority for 'firefox' to 3")
    process_filter.set_process_priority("firefox", 3)

    # Verify the priority was set
    priority = process_filter.get_process_priority(current_process)
    print(f"Priority of current process: {priority}")

def test_categories():
    """Test the process categorizer functionality"""
    # Setup components
    components = setup_components()

    print("\nTesting Process Categories:")

    # Get a categorizer instance
    categorizer = components['categorizer']

    # Print available categories
    print("\nAvailable categories:")
    for category in categorizer.categories.keys():
        print(f"  - {category}")

    # Test categorizing some common processes
    test_processes = ["chrome", "firefox", "code", "terminal", "slack", "zoom"]
    print("\nCategorizing test processes:")
    for proc in test_processes:
        category = categorizer.categorize_process(proc)
        print(f"  - {proc}: {category}")

    # Test adding a process to a category
    test_category = "Testing"
    test_process = "myapp"

    print(f"\nAdding '{test_process}' to category '{test_category}'")
    if test_category not in categorizer.categories:
        categorizer.create_category(test_category)
    categorizer.add_process_to_category(test_process, test_category)

    # Verify the process was added
    category = categorizer.categorize_process(test_process)
    print(f"Category of '{test_process}': {category}")

def test_idle_detection():
    """Test the idle detection functionality"""
    # Setup components
    components = setup_components()

    print("\nTesting Idle Detection:")

    # Get an idle detector instance
    idle_detector = components['idle']

    # Test idle detection
    idle_time = idle_detector.get_idle_time()
    is_idle = idle_detector.is_idle()

    print(f"Current idle time: {idle_time} seconds")
    print(f"System is idle: {is_idle}")

    # Test with different threshold
    print("\nChanging idle threshold to 10 seconds...")
    idle_detector.set_idle_threshold(10)

    # Check again
    is_idle_new_threshold = idle_detector.is_idle()
    print(f"System is idle with new threshold: {is_idle_new_threshold}")

def test_database():
    """Test the database functionality"""
    # Setup components
    components = setup_components()

    print("\nTesting Database Connection:")

    # Get a database instance
    db = components['db']

    # Test saving a process
    process_data = {
        'pid': 12345,
        'name': 'test-process',
        'cpu_percent': 1.5,
        'memory_percent': 2.0,
        'category': 'Testing',
        'active_window': 'Test Window',
        'create_time': time.time(),
        'timestamp': time.time()
    }

    print("Saving test process data...")
    db.save_process(process_data)

    # Test saving a resource
    resource_data = {
        'cpu_percent': 10.0,
        'memory_percent': 50.0,
        'disk_percent': 60.0,
        'memory_total': 16000000000,
        'memory_available': 8000000000,
        'timestamp': time.time()
    }

    print("Saving test resource data...")
    db.save_resource(resource_data)

    # Test saving idle time
    print("Saving test idle time data...")
    db.save_idle_time(True, 300, time.time())

    # Retrieve data
    print("\nRetrieving data from the last hour...")

    start_time = time.time() - 3600  # Last hour
    end_time = time.time()

    processes = db.get_processes_in_range(start_time, end_time)
    resources = db.get_resources_in_range(start_time, end_time)
    idle_times = db.get_idle_times_in_range(start_time, end_time)

    print(f"Processes: {len(processes)}")
    print(f"Resources: {len(resources)}")
    print(f"Idle times: {len(idle_times)}")

def main():
    # Load environment variables
    load_dotenv()

    try:
        # Initialize database connection
        db = create_db_connection()

        # Initialize process monitor
        monitor = ProcessMonitor(db)

        # Initialize dashboard UI
        dashboard = Dashboard(monitor)

        # Start the application
        dashboard.run()

    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()