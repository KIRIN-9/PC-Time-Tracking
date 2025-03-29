import psycopg2
from psycopg2.extras import DictCursor
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import dotenv

class Database:
    def __init__(self, db_uri=None):
        dotenv.load_dotenv()
        self.db_uri = db_uri or os.getenv("DATABASE_URL")
        if not self.db_uri:
            db_name = os.getenv("DB_NAME", "pc_time_tracking")
            db_user = os.getenv("DB_USER", "postgres")
            db_password = os.getenv("DB_PASSWORD", "postgres")
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            self.db_uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

        self.init_schema()

    def get_connection(self):
        return psycopg2.connect(self.db_uri)

    def init_schema(self):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            # Create processes table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS processes (
                    id SERIAL PRIMARY KEY,
                    pid INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    cpu_percent FLOAT,
                    memory_percent FLOAT,
                    category TEXT,
                    active_window TEXT,
                    create_time TIMESTAMP,
                    timestamp TIMESTAMP NOT NULL
                )
            """)

            # Create system resources table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS system_resources (
                    id SERIAL PRIMARY KEY,
                    cpu_percent FLOAT,
                    memory_percent FLOAT,
                    disk_percent FLOAT,
                    memory_total BIGINT,
                    memory_available BIGINT,
                    timestamp TIMESTAMP NOT NULL
                )
            """)

            # Create idle times table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS idle_times (
                    id SERIAL PRIMARY KEY,
                    is_idle BOOLEAN NOT NULL,
                    duration FLOAT NOT NULL,
                    timestamp TIMESTAMP NOT NULL
                )
            """)

            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error initializing database schema: {e}")
        finally:
            cur.close()
            conn.close()

    def save_process_data(self, timestamp, processes, active_window, system_resources):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            # Save processes
            for proc in processes:
                cur.execute("""
                    INSERT INTO processes
                    (pid, name, cpu_percent, memory_percent, category, active_window, create_time, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    proc['pid'],
                    proc['name'],
                    proc['cpu_percent'],
                    proc['memory_percent'],
                    proc.get('category'),
                    active_window,
                    datetime.fromisoformat(proc['create_time']),
                    datetime.fromisoformat(timestamp)
                ))

            # Save system resources
            cur.execute("""
                INSERT INTO system_resources
                (cpu_percent, memory_percent, disk_percent, memory_total, memory_available, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                system_resources['cpu_percent'],
                system_resources['memory']['percent'],
                system_resources['disk']['percent'],
                system_resources['memory']['total'],
                system_resources['memory']['available'],
                datetime.fromisoformat(timestamp)
            ))

            # Save idle time
            cur.execute("""
                INSERT INTO idle_times
                (is_idle, duration, timestamp)
                VALUES (%s, %s, %s)
            """, (
                system_resources.get('is_idle', False),
                system_resources.get('idle_time', 0),
                datetime.fromisoformat(timestamp)
            ))

            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error saving process data: {e}")
        finally:
            cur.close()
            conn.close()

    def get_process_history(self, start_time=None, end_time=None):
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)

        query = "SELECT * FROM processes WHERE 1=1"
        params = []

        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= %s"
            params.append(end_time)

        query += " ORDER BY timestamp DESC"

        try:
            cur.execute(query, params)
            return cur.fetchall()
        except Exception as e:
            print(f"Error retrieving process history: {e}")
            return []
        finally:
            cur.close()
            conn.close()

    def get_resource_history(self, hours=24):
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)

        query = """
            SELECT * FROM system_resources
            WHERE timestamp >= NOW() - interval '%s hours'
            ORDER BY timestamp DESC
        """

        try:
            cur.execute(query, (hours,))
            return cur.fetchall()
        except Exception as e:
            print(f"Error retrieving resource history: {e}")
            return []
        finally:
            cur.close()
            conn.close()

    def get_category_summary(self, hours=24):
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)

        query = """
            SELECT category, COUNT(*) * 5 as seconds_spent
            FROM processes
            WHERE timestamp >= NOW() - interval '%s hours'
              AND category IS NOT NULL
            GROUP BY category
            ORDER BY seconds_spent DESC
        """

        try:
            cur.execute(query, (hours,))
            result = {}
            for row in cur.fetchall():
                result[row['category']] = row['seconds_spent']
            return result
        except Exception as e:
            print(f"Error retrieving category summary: {e}")
            return {}
        finally:
            cur.close()
            conn.close()

    def clear_old_data(self, days=30):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            # Clear old process data
            cur.execute("DELETE FROM processes WHERE timestamp < %s", (cutoff_date,))

            # Clear old system resource data
            cur.execute("DELETE FROM system_resources WHERE timestamp < %s", (cutoff_date,))

            # Clear old idle time data
            cur.execute("DELETE FROM idle_times WHERE timestamp < %s", (cutoff_date,))

            conn.commit()
            print(f"Cleared data older than {days} days")
        except Exception as e:
            conn.rollback()
            print(f"Error clearing old data: {e}")
        finally:
            cur.close()
            conn.close()

    def save_idle_time(self, is_idle: bool, idle_time: float) -> None:
        """Save idle time data to the database"""
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO idle_times (is_idle, duration, timestamp)
                VALUES (%s, %s, %s)
            """, (is_idle, idle_time, datetime.now()))
            conn.commit()
        except Exception as e:
            print(f"Error saving idle time: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    def get_idle_times_in_range(self, start_time: float, end_time: float) -> List[Dict]:
        """Get idle time data within a time range"""
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        try:
            cur.execute("""
                SELECT is_idle, duration, timestamp
                FROM idle_times
                WHERE timestamp BETWEEN %s AND %s
                ORDER BY timestamp
            """, (datetime.fromtimestamp(start_time), datetime.fromtimestamp(end_time)))
            return cur.fetchall()
        except Exception as e:
            print(f"Error getting idle times: {e}")
            return []
        finally:
            cur.close()
            conn.close()