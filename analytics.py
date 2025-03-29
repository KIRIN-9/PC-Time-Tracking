from datetime import datetime, date, timedelta
from collections import defaultdict

class Analytics:
    def __init__(self, db):
        self.db = db

    def calculate_daily_metrics(self, target_date=None):
        """Calculate daily productivity metrics."""
        target_date = target_date or date.today()
        
        with self.db.conn.cursor() as cur:
            # Get work sessions for the day
            cur.execute("""
                SELECT start_time, end_time, focus_time, break_time
                FROM work_sessions
                WHERE DATE(start_time) = %s
            """, (target_date,))
            sessions = cur.fetchall()

            # Get window activity for the day
            cur.execute("""
                SELECT w.window_title, w.workspace, w.start_time, w.end_time, p.name
                FROM window_activity w
                JOIN processes p ON w.process_id = p.id
                WHERE DATE(w.start_time) = %s
            """, (target_date,))
            window_activities = cur.fetchall()

            # Calculate metrics
            total_work_time = timedelta()
            total_break_time = timedelta()
            app_usage = defaultdict(timedelta)
            workspace_usage = defaultdict(timedelta)
            hourly_activity = defaultdict(timedelta)

            # Process work sessions
            for start, end, focus, break_time in sessions:
                if end:
                    total_work_time += focus
                    total_break_time += break_time

            # Process window activities
            for title, workspace, start, end, app_name in window_activities:
                if end:
                    duration = end - start
                    app_usage[app_name] += duration
                    workspace_usage[workspace] += duration
                    hour = start.hour
                    hourly_activity[hour] += duration

            # Calculate focus ratio
            total_time = total_work_time + total_break_time
            focus_ratio = (total_work_time.total_seconds() / total_time.total_seconds() 
                         if total_time.total_seconds() > 0 else 0)

            # Find most used app and workspace
            most_used_app = max(app_usage.items(), key=lambda x: x[1])[0] if app_usage else None
            most_active_workspace = max(workspace_usage.items(), key=lambda x: x[1])[0] if workspace_usage else None
            peak_hour = max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else None

            # Store analytics
            cur.execute("""
                INSERT INTO analytics 
                (date, total_work_time, total_break_time, focus_ratio, 
                 most_used_app, most_active_workspace, peak_productivity_hour)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (date) DO UPDATE SET
                    total_work_time = EXCLUDED.total_work_time,
                    total_break_time = EXCLUDED.total_break_time,
                    focus_ratio = EXCLUDED.focus_ratio,
                    most_used_app = EXCLUDED.most_used_app,
                    most_active_workspace = EXCLUDED.most_active_workspace,
                    peak_productivity_hour = EXCLUDED.peak_productivity_hour
            """, (
                target_date, total_work_time, total_break_time, focus_ratio,
                most_used_app, most_active_workspace, peak_hour
            ))
            self.db.conn.commit()

    def get_daily_summary(self, target_date=None):
        """Get the daily productivity summary."""
        target_date = target_date or date.today()
        
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT total_work_time, total_break_time, focus_ratio,
                       most_used_app, most_active_workspace, peak_productivity_hour
                FROM analytics
                WHERE date = %s
            """, (target_date,))
            row = cur.fetchone()
            
            if row:
                return {
                    'total_work_time': row[0],
                    'total_break_time': row[1],
                    'focus_ratio': row[2],
                    'most_used_app': row[3],
                    'most_active_workspace': row[4],
                    'peak_hour': row[5]
                }
            return None

    def get_weekly_trends(self):
        """Get productivity trends for the last 7 days."""
        end_date = date.today()
        start_date = end_date - timedelta(days=6)
        
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT date, total_work_time, total_break_time, focus_ratio
                FROM analytics
                WHERE date BETWEEN %s AND %s
                ORDER BY date
            """, (start_date, end_date))
            
            return cur.fetchall()
