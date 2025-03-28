import argparse
import threading
from process_monitor import ProcessMonitor
import time
import json
from datetime import datetime, timedelta
from tabulate import tabulate

def format_time(seconds):
    """Format time in seconds to a human-readable string."""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

def print_process_stats(monitor: ProcessMonitor):
    """Print current process statistics in a formatted table."""
    processes = monitor.get_running_processes()
    resources = monitor.get_system_resources()
    active_window = monitor.get_active_window()

    print("\n" + "="*50)
    print(f"Active Window: {active_window}")
    print(f"CPU Usage: {resources['cpu_percent']}%")
    print(f"Memory Usage: {resources['memory']['percent']}%")
    print(f"Disk Usage: {resources['disk']['percent']}%")
    print("\nTop Processes by CPU Usage:")
    print("-"*50)

    # Sort processes by CPU usage and prepare table data
    sorted_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)
    table_data = []
    for proc in sorted_processes[:10]:  # Show top 10
        running_time = time.time() - datetime.fromisoformat(proc['create_time']).timestamp()
        table_data.append([
            proc['pid'],
            proc['name'],
            f"{proc['cpu_percent']:.1f}%",
            f"{proc['memory_percent']:.1f}%",
            format_time(running_time)
        ])

    headers = ["PID", "Process Name", "CPU %", "Memory %", "Running Time"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def print_process_summary(monitor: ProcessMonitor, hours: int = 24):
    """Print process summary statistics for the specified time range."""
    end_time = datetime.now().isoformat()
    start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

    summary = monitor.get_process_summary(start_time, end_time)

    print(f"\nProcess Summary (Last {hours} hours):")
    print("="*50)

    table_data = []
    for proc in summary['processes'][:10]:  # Show top 10
        table_data.append([
            proc['name'],
            proc['count'],
            f"{proc['avg_cpu']:.1f}%",
            f"{proc['avg_memory']:.1f}%",
            datetime.fromisoformat(proc['first_seen']).strftime('%H:%M:%S'),
            datetime.fromisoformat(proc['last_seen']).strftime('%H:%M:%S')
        ])

    headers = ["Process Name", "Count", "Avg CPU %", "Avg Memory %", "First Seen", "Last Seen"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def main():
    parser = argparse.ArgumentParser(description='Process Monitoring Dashboard')
    parser.add_argument('--interval', type=float, default=1.0,
                      help='Monitoring interval in seconds')
    parser.add_argument('--output', type=str, help='Output file for process history')
    parser.add_argument('--db', type=str, default="process_data.db",
                      help='Database file path')
    parser.add_argument('--summary', action='store_true',
                      help='Show process summary statistics')
    parser.add_argument('--hours', type=int, default=24,
                      help='Hours of history for summary (default: 24)')
    args = parser.parse_args()

    monitor = ProcessMonitor(args.db)

    # Start monitoring in a separate thread
    monitor_thread = threading.Thread(
        target=monitor.monitor_processes,
        args=(args.interval,),
        daemon=True
    )
    monitor_thread.start()

    try:
        while True:
            print_process_stats(monitor)
            if args.summary:
                print_process_summary(monitor, args.hours)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopping process monitoring...")
        if args.output:
            # Save process history to file
            with open(args.output, 'w') as f:
                json.dump(monitor.get_process_history(), f, indent=2)
            print(f"Process history saved to {args.output}")

if __name__ == "__main__":
    main()