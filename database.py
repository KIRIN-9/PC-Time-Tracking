import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        """Establish database connection using environment variables."""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT'),
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD')
            )
            self.create_schema()
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def create_schema(self):
        """Create the database schema if it doesn't exist."""
        with self.conn.cursor() as cur:
            # Create processes table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS processes (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    executable_path TEXT,
                    cpu_usage FLOAT,
                    memory_usage FLOAT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration INTERVAL
                )
            """)

            # Create work_sessions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS work_sessions (
                    id SERIAL PRIMARY KEY,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration INTERVAL,
                    focus_time INTERVAL,
                    break_time INTERVAL,
                    focus_ratio FLOAT
                )
            """)

            # Create activity_timeline table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS activity_timeline (
                    id SERIAL PRIMARY KEY,
                    process_id INTEGER REFERENCES processes(id),
                    session_id INTEGER REFERENCES work_sessions(id),
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    is_active BOOLEAN DEFAULT true
                )
            """)

            # Create window_activity table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS window_activity (
                    id SERIAL PRIMARY KEY,
                    process_id INTEGER REFERENCES processes(id),
                    window_title TEXT NOT NULL,
                    workspace TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration INTERVAL,
                    is_focused BOOLEAN DEFAULT true
                )
            """)

            # Create analytics table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    total_work_time INTERVAL,
                    total_break_time INTERVAL,
                    focus_ratio FLOAT,
                    most_used_app TEXT,
                    most_active_workspace TEXT,
                    peak_productivity_hour INTEGER,
                    UNIQUE (date)
                )
            """)

            self.conn.commit()

    def insert_process(self, process_data):
        """Insert a new process record."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO processes (name, executable_path, cpu_usage, memory_usage, start_time)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                process_data['name'],
                process_data['executable_path'],
                process_data['cpu_usage'],
                process_data['memory_usage'],
                process_data['start_time']
            ))
            return cur.fetchone()[0]

    def insert_work_session(self, session_data):
        """Insert a new work session."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO work_sessions (start_time)
                VALUES (%s)
                RETURNING id
            """, (session_data['start_time'],))
            return cur.fetchone()[0]

    def update_process(self, process_id, end_time, duration):
        """Update process end time and duration."""
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE processes
                SET end_time = %s, duration = %s
                WHERE id = %s
            """, (end_time, duration, process_id))
            self.conn.commit()

    def update_work_session(self, session_id, end_time, focus_time, break_time):
        """Update work session with end time and metrics."""
        with self.conn.cursor() as cur:
            duration = end_time - focus_time - break_time
            focus_ratio = focus_time.total_seconds() / duration.total_seconds() if duration.total_seconds() > 0 else 0

            cur.execute("""
                UPDATE work_sessions
                SET end_time = %s,
                    duration = %s,
                    focus_time = %s,
                    break_time = %s,
                    focus_ratio = %s
                WHERE id = %s
            """, (end_time, duration, focus_time, break_time, focus_ratio, session_id))
            self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()