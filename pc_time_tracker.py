#!/usr/bin/env python3
"""
PC Time Tracking - Main application integrating all components.
"""
import argparse
import os
import signal
import sys
import threading
import time
from datetime import datetime

from process_monitor import ProcessMonitor
from process_categorizer import ProcessCategorizer
from data_analyzer import DataAnalyzer
from alerts import AlertManager
from cli import CLI

def signal_handler(sig, frame):
    """Handle interrupt signals."""
    print("\nGracefully shutting down...")
    sys.exit(0)

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='PC Time Tracking Application')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Run the process monitor')
    monitor_parser.add_argument('--interval', '-i', type=float, default=1.0,
                             help='Monitoring interval in seconds')
    monitor_parser.add_argument('--output', '-o', type=str, help='Output file for process history')
    monitor_parser.add_argument('--summary', '-s', action='store_true',
                              help='Show process summary statistics')
    monitor_parser.add_argument('--categories', '-c', action='store_true',
                              help='Show process categories summary')
    monitor_parser.add_argument('--hours', type=int, default=24,
                              help='Hours of history for summary (default: 24)')

    # CLI command
    cli_parser = subparsers.add_parser('cli', help='Run the CLI interface')
    cli_parser.add_argument('--interactive', '-i', action='store_true',
                         help='Run in interactive mode with UI')
    cli_parser.add_argument('--view', '-v', choices=['processes', 'categories', 'resources'],
                          default='processes', help='Initial view mode')
    cli_parser.add_argument('--refresh', '-r', type=float, default=2.0,
                          help='Refresh rate in seconds')
    cli_parser.add_argument('--sort', '-s', choices=['cpu', 'memory', 'name'],
                          default='cpu', help='Sort processes by')
    cli_parser.add_argument('--hours', type=int, default=24,
                          help='Hours of history for summaries')
    cli_parser.add_argument('--all', '-a', action='store_true',
                          help='Show all processes, not just top ones')

    # Alerts command
    alerts_parser = subparsers.add_parser('alerts', help='Manage alerts')
    alerts_subparsers = alerts_parser.add_subparsers(dest='alerts_command', help='Alerts command')

    # List alerts
    list_parser = alerts_subparsers.add_parser('list', help='List configured alerts')

    # Add alert
    add_parser = alerts_subparsers.add_parser('add', help='Add a new alert')
    add_parser.add_argument('--type', '-t', choices=['resource', 'process', 'category', 'idle'],
                         required=True, help='Alert type')
    add_parser.add_argument('--name', '-n', required=True, help='Alert name')
    add_parser.add_argument('--description', '-d', required=True, help='Alert description')
    add_parser.add_argument('--resource', choices=['cpu', 'memory', 'disk'],
                         help='Resource type for resource alerts')
    add_parser.add_argument('--threshold', type=float, help='Threshold value')
    add_parser.add_argument('--process', help='Process name for process alerts')
    add_parser.add_argument('--category', help='Category for category alerts')
    add_parser.add_argument('--duration', type=int, help='Duration in seconds/minutes')

    # Remove alert
    remove_parser = alerts_subparsers.add_parser('remove', help='Remove an alert')
    remove_parser.add_argument('name', help='Alert name to remove')

    # Monitor alerts
    monitor_alerts_parser = alerts_subparsers.add_parser('monitor', help='Monitor alerts')
    monitor_alerts_parser.add_argument('--interval', '-i', type=float, default=60.0,
                                    help='Check interval in seconds')

    # History alerts
    history_parser = alerts_subparsers.add_parser('history', help='Show alert history')
    history_parser.add_argument('--limit', '-l', type=int, default=10,
                             help='Maximum number of history entries to show')

    # Report command
    report_parser = subparsers.add_parser('report', help='Generate reports')
    report_parser.add_argument('--hours', type=int, default=24,
                            help='Number of hours to analyze (default: 24)')
    report_parser.add_argument('--no-plots', action='store_true',
                             help='Skip generating plots')
    report_parser.add_argument('--categories-only', action='store_true',
                             help='Only show category-based reports')
    report_parser.add_argument('--output', '-o', help='Output directory for reports')

    # Parse arguments
    args = parser.parse_args()

    # Set up signal handler for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Default to monitor if no command is provided
    if not args.command:
        parser.print_help()
        return

    # Handle commands
    if args.command == 'monitor':
        run_monitor(args)
    elif args.command == 'cli':
        run_cli(args)
    elif args.command == 'alerts':
        run_alerts(args)
    elif args.command == 'report':
        run_report(args)

def run_monitor(args):
    """Run the process monitor."""
    print(f"Starting PC Time Tracking Monitor...")

    from main import main as monitor_main
    sys.argv = [sys.argv[0]]  # Reset args for the monitor

    if args.interval:
        sys.argv.extend(['--interval', str(args.interval)])
    if args.output:
        sys.argv.extend(['--output', args.output])
    if args.summary:
        sys.argv.append('--summary')
    if args.categories:
        sys.argv.append('--categories')
    if args.hours:
        sys.argv.extend(['--hours', str(args.hours)])

    monitor_main()

def run_cli(args):
    """Run the CLI interface."""
    print(f"Starting PC Time Tracking CLI...")

    cli = CLI()
    cli.refresh_rate = args.refresh
    cli.view_mode = args.view
    cli.sort_by = args.sort
    cli.hours = args.hours
    cli.show_all = args.all

    if args.interactive:
        try:
            import curses
            curses.wrapper(cli.interactive_mode)
        except KeyboardInterrupt:
            print("\nStopping process monitoring...")
    else:
        cli.standard_mode()

def run_alerts(args):
    """Run the alerts system."""
    print(f"PC Time Tracking Alerts...")

    alert_manager = AlertManager()

    if not args.alerts_command:
        print("Available commands:")
        print("  list    - List configured alerts")
        print("  add     - Add a new alert")
        print("  remove  - Remove an alert")
        print("  monitor - Monitor alerts")
        print("  history - Show alert history")
        return

    if args.alerts_command == 'list':
        print("\nConfigured Alerts:")
        print("=" * 60)
        for i, alert in enumerate(alert_manager.alerts):
            status = "ENABLED" if alert.enabled else "DISABLED"
            last_triggered = alert.last_triggered.strftime("%Y-%m-%d %H:%M:%S") if alert.last_triggered else "Never"
            print(f"{i+1}. {alert.name} [{status}]")
            print(f"   Description: {alert.description}")
            print(f"   Last Triggered: {last_triggered}")
            print(f"   Cooldown: {alert.cooldown} seconds")
            print("-" * 60)

    elif args.alerts_command == 'add':
        from alerts import ResourceAlert, ProcessAlert, CategoryAlert, IdleAlert

        if args.type == 'resource':
            if not args.resource or not args.threshold:
                print("Error: Resource alerts require --resource and --threshold")
                return
            alert = ResourceAlert(args.name, args.description, args.resource, args.threshold)
            alert_manager.add_alert(alert)
            print(f"Added resource alert: {args.name}")

        elif args.type == 'process':
            if not args.process:
                print("Error: Process alerts require --process")
                return
            alert = ProcessAlert(args.name, args.description, args.process,
                                args.duration, args.threshold)
            alert_manager.add_alert(alert)
            print(f"Added process alert: {args.name}")

        elif args.type == 'category':
            if not args.category or not args.threshold:
                print("Error: Category alerts require --category and --threshold")
                return
            alert = CategoryAlert(args.name, args.description, args.category,
                                args.threshold, args.hours or 24)
            alert_manager.add_alert(alert)
            print(f"Added category alert: {args.name}")

        elif args.type == 'idle':
            if not args.duration:
                print("Error: Idle alerts require --duration (minutes)")
                return
            alert = IdleAlert(args.name, args.description, args.duration)
            alert_manager.add_alert(alert)
            print(f"Added idle alert: {args.name}")

    elif args.alerts_command == 'remove':
        success = alert_manager.remove_alert(args.name)
        if success:
            print(f"Removed alert: {args.name}")
        else:
            print(f"Error: Alert not found: {args.name}")

    elif args.alerts_command == 'monitor':
        print(f"Monitoring alerts (interval: {args.interval}s)...")
        print("Press Ctrl+C to stop")

        monitor = ProcessMonitor()

        # Start monitoring thread
        monitor_thread = threading.Thread(
            target=monitor.monitor_processes,
            args=(1.0,),
            daemon=True
        )
        monitor_thread.start()

        # Start alerts monitoring
        alert_manager.start_monitoring(monitor, args.interval)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping alert monitoring...")
            alert_manager.stop_monitoring()

    elif args.alerts_command == 'history':
        history = alert_manager.get_history(args.limit)
        print("\nAlert History:")
        print("=" * 60)

        if not history:
            print("No alerts have been triggered.")
            return

        for i, entry in enumerate(history):
            time_str = datetime.fromisoformat(entry['time']).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{i+1}. {entry['name']} - {time_str}")
            print(f"   {entry['description']}")
            print("-" * 60)

def run_report(args):
    """Generate reports."""
    print(f"Generating PC Time Tracking Reports...")

    from generate_report import main as report_main
    sys.argv = [sys.argv[0]]  # Reset args for the report

    if args.hours:
        sys.argv.extend(['--hours', str(args.hours)])
    if args.no_plots:
        sys.argv.append('--no-plots')
    if args.categories_only:
        sys.argv.append('--categories-only')

    # Create output directory if specified
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        os.chdir(args.output)

    report_main()

if __name__ == "__main__":
    main()