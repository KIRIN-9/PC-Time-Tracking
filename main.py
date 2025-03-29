import time
import psutil
import threading
from datetime import datetime, timedelta
from blessed import Terminal
from database import Database
from config import Config
from hyprland_monitor import HyprlandMonitor
from analytics import Analytics

class ProcessMonitor:
    def __init__(self):
        self.term = Terminal()
        self.db = Database()
        self.analytics = Analytics(self.db)
        self.running = True
        self.current_session = None
        self.active_processes = {}
        self.last_cpu_check = datetime.now()
        self.idle_time = timedelta(0)
        self.current_window = None
        self.current_workspace = 'default'
        
        try:
            self.hyprland = HyprlandMonitor()
            self.hyprland.on_window_change(self.handle_window_change)
            self.hyprland.on_workspace_change(self.handle_workspace_change)
        except EnvironmentError:
            print("Warning: Hyprland not detected, window tracking disabled")
            self.hyprland = None

    def start(self):
        """Start the process monitor."""
        try:
            with self.term.fullscreen(), self.term.cbreak(), self.term.hidden_cursor():
                # Start monitoring thread
                monitor_thread = threading.Thread(target=self.monitor_processes)
                monitor_thread.daemon = True
                monitor_thread.start()

                # Main UI loop
                while self.running:
                    self.draw_ui()
                    if self.term.inkey(timeout=Config.REFRESH_RATE).lower() == 'q':
                        self.running = False

        except KeyboardInterrupt:
            self.running = False
        finally:
            self.cleanup()

    def monitor_processes(self):
        """Monitor system processes in a separate thread."""
        while self.running:
            current_time = datetime.now()

            # Check for new processes
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'create_time']):
                try:
                    proc_info = proc.info()
                    if proc_info['pid'] not in self.active_processes:
                        self.active_processes[proc_info['pid']] = {
                            'name': proc_info['name'],
                            'executable_path': proc.exe(),
                            'cpu_usage': proc_info['cpu_percent'],
                            'memory_usage': proc_info['memory_info'].rss,
                            'start_time': datetime.fromtimestamp(proc_info['create_time']),
                            'db_id': self.db.insert_process({
                                'name': proc_info['name'],
                                'executable_path': proc.exe(),
                                'cpu_usage': proc_info['cpu_percent'],
                                'memory_usage': proc_info['memory_info'].rss,
                                'start_time': datetime.fromtimestamp(proc_info['create_time'])
                            })
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Check for ended processes
            ended_pids = []
            for pid, proc_info in self.active_processes.items():
                try:
                    psutil.Process(pid)
                except psutil.NoSuchProcess:
                    self.db.update_process(
                        proc_info['db_id'],
                        datetime.now(),
                        datetime.now() - proc_info['start_time']
                    )
                    ended_pids.append(pid)

            for pid in ended_pids:
                del self.active_processes[pid]

            # Check for idle state
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent < Config.CPU_THRESHOLD:
                self.idle_time += timedelta(seconds=Config.UPDATE_INTERVAL)
                if self.idle_time.total_seconds() >= Config.IDLE_THRESHOLD:
                    self.handle_break()
            else:
                self.idle_time = timedelta(0)
                self.handle_activity()

            time.sleep(Config.UPDATE_INTERVAL)

    def handle_break(self):
        """Handle system idle state."""
        if self.current_session and not self.current_session.get('is_break'):
            self.current_session['is_break'] = True
            self.current_session['break_start'] = datetime.now()

    def handle_activity(self):
        """Handle system activity state."""
        if self.current_session and self.current_session.get('is_break'):
            break_duration = datetime.now() - self.current_session['break_start']
            self.current_session['break_time'] += break_duration
            self.current_session['is_break'] = False
        elif not self.current_session:
            self.current_session = {
                'start_time': datetime.now(),
                'focus_time': timedelta(0),
                'break_time': timedelta(0),
                'is_break': False
            }

    def handle_window_change(self, window_data):
        """Handle window focus change from Hyprland."""
        if self.current_window:
            # Update end time for previous window
            with self.db.conn.cursor() as cur:
                cur.execute("""
                    UPDATE window_activity
                    SET end_time = %s, duration = %s - start_time
                    WHERE window_title = %s AND end_time IS NULL
                """, (datetime.now(), datetime.now(), self.current_window))

        self.current_window = window_data
        if window_data:
            # Insert new window activity
            with self.db.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO window_activity 
                    (process_id, window_title, workspace, start_time)
                    VALUES (
                        (SELECT id FROM processes WHERE name = %s ORDER BY start_time DESC LIMIT 1),
                        %s, %s, %s
                    )
                """, (window_data.split(' ')[0], window_data, self.current_workspace, datetime.now()))
            self.db.conn.commit()

    def handle_workspace_change(self, workspace_data):
        """Handle workspace change from Hyprland."""
        self.current_workspace = workspace_data

    def draw_ui(self):
        """Draw the terminal user interface."""
        print(self.term.clear())

        # Draw header with current window/workspace
        print(self.term.blue("PC Time Tracking Monitor") + self.term.normal)
        if self.hyprland and self.current_window:
            print(f"Current Window: {self.current_window}")
            print(f"Workspace: {self.current_workspace}")
        print(self.term.blue("=" * self.term.width) + self.term.normal)

        # Draw process list
        print(self.term.blue("\nActive Processes:") + self.term.normal)
        print("-" * Config.PROCESS_LIST_WIDTH)

        for pid, proc in self.active_processes.items():
            status = self.term.green("●") if proc['cpu_usage'] > Config.CPU_THRESHOLD else self.term.yellow("●")
            print(f"{status} {proc['name']:<30} CPU: {proc['cpu_usage']:>5.1f}% MEM: {proc['memory_usage']/1024/1024:>5.1f}MB")

        # Draw analytics
        print(self.term.blue("\nDaily Summary:") + self.term.normal)
        print("-" * Config.TIMELINE_WIDTH)

        daily_summary = self.analytics.get_daily_summary()
        if daily_summary:
            print(f"Total Work Time: {daily_summary['total_work_time']}")
            print(f"Total Break Time: {daily_summary['total_break_time']}")
            print(f"Focus Ratio: {daily_summary['focus_ratio']:.1%}")
            print(f"Most Used App: {daily_summary['most_used_app']}")
            print(f"Most Active Workspace: {daily_summary['most_active_workspace']}")
            if daily_summary['peak_hour'] is not None:
                print(f"Peak Productivity Hour: {daily_summary['peak_hour']:02d}:00")

        if self.current_session:
            print(self.term.blue("\nCurrent Session:") + self.term.normal)
            print("-" * Config.TIMELINE_WIDTH)
            focus_ratio = (self.current_session['focus_time'].total_seconds() /
                         (self.current_session['focus_time'] + self.current_session['break_time']).total_seconds()
                         if (self.current_session['focus_time'] + self.current_session['break_time']).total_seconds() > 0
                         else 0)

            print(f"Session Duration: {datetime.now() - self.current_session['start_time']}")
            print(f"Focus Time: {self.current_session['focus_time']}")
            print(f"Break Time: {self.current_session['break_time']}")
            print(f"Focus Ratio: {focus_ratio:.1%}")

        # Draw footer with controls
        print(self.term.blue("\n" + "=" * self.term.width) + self.term.normal)
        print("Controls: 'q' Quit | 'r' Refresh Analytics | 's' Show Weekly Summary")

    def cleanup(self):
        """Clean up resources before exit."""
        if self.current_session:
            self.db.update_work_session(
                self.current_session['db_id'],
                datetime.now(),
                self.current_session['focus_time'],
                self.current_session['break_time']
            )
        if self.hyprland:
            self.hyprland.stop()
        self.analytics.calculate_daily_metrics()
        self.db.close()

if __name__ == "__main__":
    monitor = ProcessMonitor()
    monitor.start()