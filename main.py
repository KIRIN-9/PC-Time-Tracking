#!/usr/bin/env python3

"""
PC Time Tracker
A simple CLI-based process and productivity tracker
"""

import os
import time
import signal
import sys
from dotenv import load_dotenv
from src.core import ProcessMonitor, IdleDetector, SessionTracker

# Global variables for cleanup
process_monitor = None
running = True

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\nShutting down...")
    running = False

def main():
    global process_monitor, running

    # Load environment variables
    load_dotenv()

    # Get settings from environment
    idle_threshold = int(os.getenv('IDLE_THRESHOLD', '5'))
    break_threshold = int(os.getenv('BREAK_THRESHOLD', '40'))

    # Initialize components
    process_monitor = ProcessMonitor()
    idle_detector = IdleDetector(idle_threshold_minutes=idle_threshold)
    session_tracker = SessionTracker(break_threshold_minutes=break_threshold)

    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)

    print("PC Time Tracker")
    print("Starting monitoring... (Press Ctrl+C to exit)")
    print(f"Idle threshold: {idle_threshold} minutes")
    print(f"Break threshold: {break_threshold} minutes")

    # Start work session
    session_tracker.start_session()

    try:
        while running:
            # Update process information
            processes = process_monitor.scan_processes()
            system_info = process_monitor.get_system_info()

            # Check idle state
            if idle_detector.check_idle():
                if not session_tracker.current_session.is_break:
                    print("\nIdle detected, starting break...")
                    session_tracker.start_break()
            else:
                if session_tracker.current_session and session_tracker.current_session.is_break:
                    print("\nActivity detected, resuming work...")
                    session_tracker.start_session()

            # Print some basic stats
            stats = session_tracker.get_session_stats()
            os.system('clear' if os.name == 'posix' else 'cls')
            print(f"\nSystem CPU: {system_info['cpu_percent']}%")
            print(f"System Memory: {system_info['memory_percent']}%")
            print(f"\nActive Processes: {len(processes)}")
            print(f"Current Session: {stats['current_session']}")
            print(f"Session Duration: {stats['current_duration']}")
            print(f"Total Work Time: {stats['total_work_time']}")
            print(f"Total Break Time: {stats['total_break_time']}")

            if session_tracker.should_take_break():
                print("\nTime for a break!")

            time.sleep(1)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        if session_tracker.current_session:
            session_tracker.end_session()
        print("\nFinal Statistics:")
        stats = session_tracker.get_session_stats()
        print(f"Total Work Time: {stats['total_work_time']}")
        print(f"Total Break Time: {stats['total_break_time']}")
        print(f"Number of Sessions: {stats['session_count']}")

if __name__ == "__main__":
    main()