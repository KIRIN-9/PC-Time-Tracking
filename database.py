import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
from typing import Dict, List, Optional
import json
from config import DB_URI

class Database:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        with psycopg2.connect(DB_URI) as conn:
            cursor = conn.cursor()

            # Create processes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processes (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    pid INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    cpu_percent REAL NOT NULL,
                    memory_percent REAL NOT NULL,
                    create_time TIMESTAMP NOT NULL,
                    active_window TEXT,
                    category TEXT,
                    UNIQUE(timestamp, pid)
                )
            ''')

            # Create system_resources table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_resources (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    cpu_percent REAL NOT NULL,
                    memory_total BIGINT NOT NULL,
                    memory_available BIGINT NOT NULL,
                    memory_percent REAL NOT NULL,
                    disk_total BIGINT NOT NULL,
                    disk_used BIGINT NOT NULL,
                    disk_percent REAL NOT NULL,
                    idle_time INTEGER,
                    is_idle BOOLEAN,
                    UNIQUE(timestamp)
                )
            ''')

            # Create idle_periods table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS idle_periods (
                    id SERIAL PRIMARY KEY,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    duration INTEGER NOT NULL,
                    UNIQUE(start_time)
                )
            ''')

            conn.commit()

    def save_process_data(self, timestamp: str, processes: List[Dict],
                         active_window: Optional[str], system_resources: Dict):
        """Save process and system resource data to database."""
        with psycopg2.connect(DB_URI) as conn:
            cursor = conn.cursor()

            # Save system resources
            cursor.execute('''
                INSERT INTO system_resources
                (timestamp, cpu_percent, memory_total, memory_available,
                memory_percent, disk_total, disk_used, disk_percent,
                idle_time, is_idle)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (timestamp) DO UPDATE SET
                    cpu_percent = EXCLUDED.cpu_percent,
                    memory_total = EXCLUDED.memory_total,
                    memory_available = EXCLUDED.memory_available,
                    memory_percent = EXCLUDED.memory_percent,
                    disk_total = EXCLUDED.disk_total,
                    disk_used = EXCLUDED.disk_used,
                    disk_percent = EXCLUDED.disk_percent,
                    idle_time = EXCLUDED.idle_time,
                    is_idle = EXCLUDED.is_idle
            ''', (
                timestamp,
                system_resources['cpu_percent'],
                system_resources['memory']['total'],
                system_resources['memory']['available'],
                system_resources['memory']['percent'],
                system_resources['disk']['total'],
                system_resources['disk']['used'],
                system_resources['disk']['percent'],
                system_resources.get('idle_time', 0),
                system_resources.get('is_idle', False)
            ))

            # Save processes
            for proc in processes:
                cursor.execute('''
                    INSERT INTO processes
                    (timestamp, pid, name, cpu_percent, memory_percent,
                    create_time, active_window, category)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (timestamp, pid) DO UPDATE SET
                        name = EXCLUDED.name,
                        cpu_percent = EXCLUDED.cpu_percent,
                        memory_percent = EXCLUDED.memory_percent,
                        create_time = EXCLUDED.create_time,
                        active_window = EXCLUDED.active_window,
                        category = EXCLUDED.category
                ''', (
                    timestamp,
                    proc['pid'],
                    proc['name'],
                    proc['cpu_percent'],
                    proc['memory_percent'],
                    proc['create_time'],
                    active_window,
                    proc.get('category', 'uncategorized')
                ))

            conn.commit()

    def get_process_history(self, start_time: Optional[str] = None,
                          end_time: Optional[str] = None) -> Dict:
        """Retrieve process history within the specified time range."""
        with psycopg2.connect(DB_URI) as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)

            # Build time range query
            time_condition = ""
            params = []
            if start_time:
                time_condition += "WHERE timestamp >= %s"
                params.append(start_time)
            if end_time:
                time_condition += " AND" if time_condition else "WHERE"
                time_condition += " timestamp <= %s"
                params.append(end_time)

            # Get processes
            cursor.execute(f'''
                SELECT timestamp, pid, name, cpu_percent, memory_percent,
                       create_time, active_window, category
                FROM processes
                {time_condition}
                ORDER BY timestamp
            ''', params)
            processes = cursor.fetchall()

            # Get system resources
            cursor.execute(f'''
                SELECT timestamp, cpu_percent, memory_total, memory_available,
                       memory_percent, disk_total, disk_used, disk_percent
                FROM system_resources
                {time_condition}
                ORDER BY timestamp
            ''', params)
            resources = cursor.fetchall()

            # Format results
            history = {}
            for row in resources:
                timestamp = row['timestamp'].isoformat()
                history[timestamp] = {
                    'system_resources': {
                        'cpu_percent': row['cpu_percent'],
                        'memory': {
                            'total': row['memory_total'],
                            'available': row['memory_available'],
                            'percent': row['memory_percent']
                        },
                        'disk': {
                            'total': row['disk_total'],
                            'used': row['disk_used'],
                            'percent': row['disk_percent']
                        }
                    },
                    'processes': []
                }

            for row in processes:
                timestamp = row['timestamp'].isoformat()
                if timestamp not in history:
                    history[timestamp] = {'processes': [], 'system_resources': {}}
                history[timestamp]['processes'].append({
                    'pid': row['pid'],
                    'name': row['name'],
                    'cpu_percent': row['cpu_percent'],
                    'memory_percent': row['memory_percent'],
                    'create_time': row['create_time'].isoformat(),
                    'active_window': row['active_window'],
                    'category': row['category']
                })

            return history

    def get_process_summary(self, start_time: Optional[str] = None,
                          end_time: Optional[str] = None) -> Dict:
        """Get summary statistics for processes within the time range."""
        with psycopg2.connect(DB_URI) as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)

            # Build time range query
            time_condition = ""
            params = []
            if start_time:
                time_condition += "WHERE timestamp >= %s"
                params.append(start_time)
            if end_time:
                time_condition += " AND" if time_condition else "WHERE"
                time_condition += " timestamp <= %s"
                params.append(end_time)

            # Get process statistics
            cursor.execute(f'''
                SELECT name,
                       COUNT(*) as count,
                       AVG(cpu_percent) as avg_cpu,
                       AVG(memory_percent) as avg_memory,
                       MIN(timestamp) as first_seen,
                       MAX(timestamp) as last_seen
                FROM processes
                {time_condition}
                GROUP BY name
                ORDER BY avg_cpu DESC
            ''', params)

            summary = {
                'processes': [],
                'time_range': {
                    'start': start_time,
                    'end': end_time
                }
            }

            for row in cursor.fetchall():
                summary['processes'].append({
                    'name': row['name'],
                    'count': row['count'],
                    'avg_cpu': round(float(row['avg_cpu']), 2),
                    'avg_memory': round(float(row['avg_memory']), 2),
                    'first_seen': row['first_seen'].isoformat(),
                    'last_seen': row['last_seen'].isoformat()
                })

            return summary