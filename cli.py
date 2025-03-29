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
from process_filter import ProcessFilter
from data_analyzer import DataAnalyzer

class CLI:
    """Enhanced CLI interface with interactive mode."""

    def __init__(self):
        """Initialize the CLI interface."""
        self.monitor = ProcessMonitor()
        self.categorizer = ProcessCategorizer()
        self.analyzer = DataAnalyzer()
        self.process_filter = ProcessFilter()
        self.running = True
        self.refresh_rate = 2.0  # seconds
        self.view_mode = "processes"  # Default view: processes, categories, resources, filter
        self.selected_process = 0  # Selected process index in interactive mode
        self.selected_filter_item = 0  # Selected filter item in filter view
        self.hours = 24  # Default history hours
        self.sort_by = "cpu"  # Default sort: cpu, memory, name, priority
        self.show_all = False  # Show all processes or just top ones
        self.filter_view_mode = "excluded"  # excluded, patterns, priorities, thresholds

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
        elif self.sort_by == "priority":
            sorted_processes = sorted(processes, key=lambda x: x.get('priority', 1), reverse=True)

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

    def format_filter_table(self):
        """Format process filter settings into a table."""
        if self.filter_view_mode == "excluded":
            # Show excluded processes
            excluded = list(self.process_filter.excluded_processes)
            excluded.sort()

            table_data = []
            for proc in excluded:
                table_data.append([proc])

            return tabulate(table_data, headers=["Excluded Processes"], tablefmt="simple")

        elif self.filter_view_mode == "patterns":
            # Show excluded patterns
            patterns = self.process_filter.excluded_patterns

            table_data = []
            for pattern in patterns:
                table_data.append([pattern])

            return tabulate(table_data, headers=["Excluded Patterns"], tablefmt="simple")

        elif self.filter_view_mode == "priorities":
            # Show process priorities
            priorities = self.process_filter.priority_processes

            table_data = []
            for proc, priority in sorted(priorities.items(), key=lambda x: x[1], reverse=True):
                table_data.append([proc, priority])

            return tabulate(table_data, headers=["Process", "Priority"], tablefmt="simple")

        elif self.filter_view_mode == "thresholds":
            # Show resource thresholds
            table_data = [
                ["CPU Threshold", f"{self.process_filter.threshold_cpu}%" if self.process_filter.threshold_cpu is not None else "None"],
                ["Memory Threshold", f"{self.process_filter.threshold_memory}%" if self.process_filter.threshold_memory is not None else "None"],
                ["Include System", "Yes" if self.process_filter.system_processes else "No"]
            ]

            return tabulate(table_data, tablefmt="simple")

        return ""

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
            help_text = " [q]Quit [p]Processes [c]Categories [r]Resources [f]Filter [s]Sort [a]All [h]History "
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
                    detail_str = f"Selected: {selected_proc['name']} (PID: {selected_proc['pid']}, Priority: {selected_proc.get('priority', 1)})"
                    stdscr.addstr(height-3, 1, detail_str, curses.color_pair(3))

                    # Show additional command help
                    if self.selected_process >= 0:
                        cmd_help = " [e]Exclude [P]riority [+/-]Change Priority "
                        stdscr.addstr(height-2, 1, cmd_help, curses.color_pair(2))

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

            elif self.view_mode == "filter":
                # Show filter view mode selector
                filter_menu = " [1]Excluded [2]Patterns [3]Priorities [4]Thresholds "
                stdscr.addstr(2, 1, filter_menu, curses.A_BOLD | curses.color_pair(2))

                # Highlight current filter view mode
                if self.filter_view_mode == "excluded":
                    stdscr.addstr(2, 3, "1", curses.A_REVERSE | curses.color_pair(2))
                elif self.filter_view_mode == "patterns":
                    stdscr.addstr(2, 13, "2", curses.A_REVERSE | curses.color_pair(2))
                elif self.filter_view_mode == "priorities":
                    stdscr.addstr(2, 24, "3", curses.A_REVERSE | curses.color_pair(2))
                elif self.filter_view_mode == "thresholds":
                    stdscr.addstr(2, 38, "4", curses.A_REVERSE | curses.color_pair(2))

                # Show filter settings
                table = self.format_filter_table()
                lines = table.split('\n')

                for i, line in enumerate(lines[:height-8]):
                    if i == 0:  # Header
                        stdscr.addstr(4, 1, line, curses.A_BOLD | curses.color_pair(3))
                    else:
                        # Highlight selected item
                        if i-1 == self.selected_filter_item and self.filter_view_mode != "thresholds":
                            stdscr.addstr(4+i, 1, line, curses.A_REVERSE)
                        else:
                            stdscr.addstr(4+i, 1, line)

                # Show filter command help
                if self.filter_view_mode in ["excluded", "patterns"]:
                    cmd_help = " [d]Delete Selected [n]New Entry "
                    stdscr.addstr(height-3, 1, cmd_help, curses.color_pair(2))
                elif self.filter_view_mode == "priorities":
                    cmd_help = " [d]Delete Selected [n]New Priority [+/-]Change Priority "
                    stdscr.addstr(height-3, 1, cmd_help, curses.color_pair(2))
                elif self.filter_view_mode == "thresholds":
                    cmd_help = " [c]Set CPU Threshold [m]Set Memory Threshold [t]Toggle System Processes "
                    stdscr.addstr(height-3, 1, cmd_help, curses.color_pair(2))

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
                elif key == ord('f'):
                    self.view_mode = "filter"
                    self.selected_filter_item = 0
                elif key == ord('s'):
                    # Cycle sort options
                    if self.sort_by == "cpu":
                        self.sort_by = "memory"
                    elif self.sort_by == "memory":
                        self.sort_by = "priority"
                    elif self.sort_by == "priority":
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

                # Process view specific keys
                elif self.view_mode == "processes":
                    if key == curses.KEY_UP:
                        self.selected_process = max(0, self.selected_process - 1)
                    elif key == curses.KEY_DOWN:
                        self.selected_process = min(len(self.get_top_processes()) - 1, self.selected_process + 1)

                    # Process commands if a process is selected
                    if len(self.get_top_processes()) > 0 and self.selected_process >= 0:
                        selected_proc = self.get_top_processes()[self.selected_process]

                        if key == ord('e'):  # Exclude process
                            self.process_filter.add_excluded_process(selected_proc['name'])
                        elif key == ord('P'):  # Set priority
                            # Here we would ideally have a dialog, but for simplicity:
                            self.process_filter.set_process_priority(selected_proc['name'],
                                                                 selected_proc.get('priority', 1))
                        elif key == ord('+'):  # Increase priority
                            current = selected_proc.get('priority', 1)
                            if current < 5:
                                self.process_filter.set_process_priority(selected_proc['name'], current + 1)
                        elif key == ord('-'):  # Decrease priority
                            current = selected_proc.get('priority', 1)
                            if current > 1:
                                self.process_filter.set_process_priority(selected_proc['name'], current - 1)

                # Filter view specific keys
                elif self.view_mode == "filter":
                    # Switch filter view mode
                    if key == ord('1'):
                        self.filter_view_mode = "excluded"
                        self.selected_filter_item = 0
                    elif key == ord('2'):
                        self.filter_view_mode = "patterns"
                        self.selected_filter_item = 0
                    elif key == ord('3'):
                        self.filter_view_mode = "priorities"
                        self.selected_filter_item = 0
                    elif key == ord('4'):
                        self.filter_view_mode = "thresholds"

                    # Navigation in lists
                    if self.filter_view_mode != "thresholds":
                        if key == curses.KEY_UP:
                            self.selected_filter_item = max(0, self.selected_filter_item - 1)
                        elif key == curses.KEY_DOWN:
                            if self.filter_view_mode == "excluded":
                                max_idx = len(self.process_filter.excluded_processes) - 1
                            elif self.filter_view_mode == "patterns":
                                max_idx = len(self.process_filter.excluded_patterns) - 1
                            elif self.filter_view_mode == "priorities":
                                max_idx = len(self.process_filter.priority_processes) - 1
                            else:
                                max_idx = 0

                            self.selected_filter_item = min(max_idx, self.selected_filter_item + 1)

                    # Actions based on filter view mode
                    if self.filter_view_mode == "excluded":
                        if key == ord('d') and len(self.process_filter.excluded_processes) > 0:
                            # Delete selected exclusion
                            excluded = sorted(list(self.process_filter.excluded_processes))
                            if 0 <= self.selected_filter_item < len(excluded):
                                self.process_filter.remove_excluded_process(excluded[self.selected_filter_item])

                    elif self.filter_view_mode == "patterns":
                        if key == ord('d') and len(self.process_filter.excluded_patterns) > 0:
                            # Delete selected pattern
                            if 0 <= self.selected_filter_item < len(self.process_filter.excluded_patterns):
                                self.process_filter.remove_excluded_pattern(
                                    self.process_filter.excluded_patterns[self.selected_filter_item])

                    elif self.filter_view_mode == "priorities":
                        if key == ord('d'):
                            # Delete selected priority
                            priorities = list(self.process_filter.priority_processes.items())
                            priorities.sort(key=lambda x: x[1], reverse=True)
                            if 0 <= self.selected_filter_item < len(priorities):
                                self.process_filter.remove_process_priority(priorities[self.selected_filter_item][0])

                    elif self.filter_view_mode == "thresholds":
                        if key == ord('t'):
                            # Toggle system processes
                            self.process_filter.set_system_processes(
                                not self.process_filter.system_processes)
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