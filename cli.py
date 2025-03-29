#!/usr/bin/env python3
"""Enhanced CLI interface for PC Time Tracking."""
import argparse
import curses
import threading
import time
import os
import sys
from datetime import datetime, timedelta
from tabulate import tabulate
from process_monitor import ProcessMonitor
from process_categorizer import ProcessCategorizer
from data_analyzer import DataAnalyzer

class CLI:
    """Enhanced CLI interface with interactive mode."""

    def __init__(self):
        """Initialize the CLI interface."""
        self.monitor = ProcessMonitor()
        self.categorizer = ProcessCategorizer()
        self.analyzer = DataAnalyzer()
        self.running = True
        self.refresh_rate = 2.0  # seconds
        self.view_mode = "processes"  # Default view: processes, categories, resources
        self.selected_process = 0  # Selected process index in interactive mode
        self.hours = 24  # Default history hours
        self.sort_by = "cpu"  # Default sort: cpu, memory, name
        self.show_all = False  # Show all processes or just top ones

    def start_monitoring(self):
        """Start the process monitoring in a background thread."""
        self.monitor_thread = threading.Thread(
            target=self.monitor.monitor_processes,
            args=(self.refresh_rate,),
            daemon=True
        )
        self.monitor_thread.start()

    def get_top_processes(self, limit=10):
        """Get top processes sorted by specified criteria."""
        processes = self.monitor.get_running_processes()

        if self.sort_by == "cpu":
            sorted_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)
        elif self.sort_by == "memory":
            sorted_processes = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)
        elif self.sort_by == "name":
            sorted_processes = sorted(processes, key=lambda x: x['name'].lower())

        return sorted_processes if self.show_all else sorted_processes[:limit]

    def format_process_table(self, processes):
        """Format processes into a table."""
        now = time.time()
        table_data = []

        for proc in processes:
            running_time = now - datetime.fromisoformat(proc['create_time']).timestamp()
            hours, remainder = divmod(running_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{int(hours)}h {int(minutes)}m"

            category = proc.get('category', self.categorizer.categorize_process(proc['name']))

            table_data.append([
                proc['pid'],
                proc['name'],
                f"{proc['cpu_percent']:.1f}%",
                f"{proc['memory_percent']:.1f}%",
                time_str,
                category
            ])

        headers = ["PID", "Name", "CPU", "Memory", "Runtime", "Category"]
        return tabulate(table_data, headers=headers, tablefmt="simple")

    def format_resources_table(self):
        """Format system resources into a table."""
        resources = self.monitor.get_system_resources()
        active_window = self.monitor.get_active_window()
        idle_state = "IDLE" if self.monitor.idle_detector.is_idle() else "ACTIVE"
        idle_time = self.monitor.idle_detector.get_idle_time()

        # Format idle time
        minutes, seconds = divmod(idle_time, 60)
        hours, minutes = divmod(minutes, 60)
        idle_time_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

        table_data = [
            ["CPU Usage", f"{resources['cpu_percent']}%"],
            ["Memory Usage", f"{resources['memory']['percent']}%"],
            ["Memory Total", f"{resources['memory']['total'] / (1024**3):.2f} GB"],
            ["Memory Available", f"{resources['memory']['available'] / (1024**3):.2f} GB"],
            ["Disk Usage", f"{resources['disk']['percent']}%"],
            ["Active Window", active_window or "Unknown"],
            ["System State", idle_state],
            ["Idle Time", idle_time_str]
        ]

        return tabulate(table_data, tablefmt="simple")

    def format_category_table(self):
        """Format category summary into a table."""
        category_data = self.categorizer.get_category_summary(self.hours)

        table_data = []
        for category, seconds in category_data.items():
            hours_spent = seconds / 3600
            minutes = (seconds % 3600) // 60

            time_str = f"{int(hours_spent)}h {int(minutes)}m"
            percentage = seconds / sum(category_data.values()) * 100 if category_data.values() else 0

            table_data.append([
                category,
                time_str,
                f"{hours_spent:.2f}",
                f"{percentage:.1f}%"
            ])

        # Sort by time spent
        table_data.sort(key=lambda x: float(x[2]), reverse=True)

        headers = ["Category", "Time Spent", "Hours", "Percentage"]
        return tabulate(table_data, headers=headers, tablefmt="simple")

    def interactive_mode(self, stdscr):
        """Run the interactive CLI mode using curses."""
        # Set up curses
        curses.curs_set(0)  # Hide cursor
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)

        stdscr.clear()
        stdscr.nodelay(True)  # Non-blocking input

        # Start monitoring
        self.start_monitoring()

        # Main loop
        while self.running:
            height, width = stdscr.getmaxyx()
            stdscr.clear()

            # Show header
            header = f" PC Time Tracking - {self.view_mode.capitalize()} View "
            stdscr.addstr(0, (width - len(header)) // 2, header, curses.A_BOLD | curses.color_pair(1))

            # Show time and status
            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            stdscr.addstr(0, width - len(time_str) - 1, time_str, curses.A_BOLD)

            # Show help bar
            help_text = " [q]Quit [p]Processes [c]Categories [r]Resources [s]Sort [a]All [h]History "
            stdscr.addstr(height-1, 0, help_text, curses.A_BOLD | curses.color_pair(2))

            # Show content based on view mode
            if self.view_mode == "processes":
                processes = self.get_top_processes(limit=height-6)
                table = self.format_process_table(processes)
                lines = table.split('\n')

                for i, line in enumerate(lines[:height-6]):
                    if i == 0:  # Header
                        stdscr.addstr(2, 1, line, curses.A_BOLD | curses.color_pair(3))
                    else:
                        # Highlight selected process
                        if i-1 == self.selected_process and len(processes) > 0:
                            stdscr.addstr(2+i, 1, line, curses.A_REVERSE)
                        else:
                            stdscr.addstr(2+i, 1, line)

                # Show process details if one is selected
                if len(processes) > 0 and self.selected_process < len(processes):
                    selected_proc = processes[self.selected_process]
                    detail_str = f"Selected: {selected_proc['name']} (PID: {selected_proc['pid']})"
                    stdscr.addstr(height-3, 1, detail_str, curses.color_pair(3))

            elif self.view_mode == "categories":
                table = self.format_category_table()
                lines = table.split('\n')

                for i, line in enumerate(lines[:height-4]):
                    if i == 0:  # Header
                        stdscr.addstr(2, 1, line, curses.A_BOLD | curses.color_pair(3))
                    else:
                        stdscr.addstr(2+i, 1, line)

                # Show time period
                period_str = f"Time period: Last {self.hours} hours"
                stdscr.addstr(height-3, 1, period_str, curses.color_pair(3))

            elif self.view_mode == "resources":
                table = self.format_resources_table()
                lines = table.split('\n')

                for i, line in enumerate(lines[:height-4]):
                    if i % 2 == 0:  # Alternate colors for readability
                        stdscr.addstr(2+i, 1, line, curses.color_pair(2))
                    else:
                        stdscr.addstr(2+i, 1, line)

            # Process keyboard input
            try:
                key = stdscr.getch()
                if key == ord('q'):
                    self.running = False
                elif key == ord('p'):
                    self.view_mode = "processes"
                    self.selected_process = 0
                elif key == ord('c'):
                    self.view_mode = "categories"
                elif key == ord('r'):
                    self.view_mode = "resources"
                elif key == ord('s'):
                    # Cycle sort options
                    if self.sort_by == "cpu":
                        self.sort_by = "memory"
                    elif self.sort_by == "memory":
                        self.sort_by = "name"
                    else:
                        self.sort_by = "cpu"
                elif key == ord('a'):
                    self.show_all = not self.show_all
                elif key == ord('h'):
                    # Cycle history periods
                    if self.hours == 24:
                        self.hours = 48
                    elif self.hours == 48:
                        self.hours = 72
                    else:
                        self.hours = 24
                elif key == curses.KEY_UP and self.view_mode == "processes":
                    self.selected_process = max(0, self.selected_process - 1)
                elif key == curses.KEY_DOWN and self.view_mode == "processes":
                    self.selected_process = min(len(self.get_top_processes()) - 1, self.selected_process + 1)
            except:
                # Ignore input errors
                pass

            stdscr.refresh()
            time.sleep(self.refresh_rate)

    def standard_mode(self):
        """Run in standard non-interactive mode."""
        self.start_monitoring()

        try:
            while self.running:
                os.system('clear' if os.name == 'posix' else 'cls')

                print(f"\n{'=' * 50}")
                print(f" PC Time Tracking - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'=' * 50}")

                if self.view_mode == "processes":
                    processes = self.get_top_processes()
                    print("\nTop Processes:")
                    print(self.format_process_table(processes))

                elif self.view_mode == "categories":
                    print("\nTime by Category:")
                    print(self.format_category_table())

                elif self.view_mode == "resources":
                    print("\nSystem Resources:")
                    print(self.format_resources_table())

                print(f"\nView: {self.view_mode} | Sort: {self.sort_by} | Period: {self.hours}h")
                print("Press Ctrl+C to exit")

                time.sleep(self.refresh_rate)

        except KeyboardInterrupt:
            print("\nStopping process monitoring...")
            self.running = False

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description='PC Time Tracking CLI')
    parser.add_argument('--interactive', '-i', action='store_true',
                      help='Run in interactive mode with UI')
    parser.add_argument('--view', '-v', choices=['processes', 'categories', 'resources'],
                      default='processes', help='Initial view mode')
    parser.add_argument('--refresh', '-r', type=float, default=2.0,
                      help='Refresh rate in seconds')
    parser.add_argument('--sort', '-s', choices=['cpu', 'memory', 'name'],
                      default='cpu', help='Sort processes by')
    parser.add_argument('--hours', type=int, default=24,
                      help='Hours of history for summaries')
    parser.add_argument('--all', '-a', action='store_true',
                      help='Show all processes, not just top ones')

    args = parser.parse_args()

    cli = CLI()
    cli.refresh_rate = args.refresh
    cli.view_mode = args.view
    cli.sort_by = args.sort
    cli.hours = args.hours
    cli.show_all = args.all

    if args.interactive:
        try:
            curses.wrapper(cli.interactive_mode)
        except KeyboardInterrupt:
            print("\nStopping process monitoring...")
    else:
        cli.standard_mode()

if __name__ == "__main__":
    main()