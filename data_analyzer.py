"""Data analysis and visualization module for PC Time Tracking."""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import DictCursor
from config import DB_URI

class DataAnalyzer:
    def __init__(self):
        """Initialize the DataAnalyzer with database connection."""
        self.conn = psycopg2.connect(DB_URI)

    def get_process_usage_summary(self, hours=24):
        """Get summary of process CPU and memory usage over the specified time period."""
        query = """
            SELECT
                name,
                AVG(cpu_percent) as avg_cpu,
                MAX(cpu_percent) as max_cpu,
                AVG(memory_percent) as avg_memory,
                MAX(memory_percent) as max_memory,
                COUNT(*) as sample_count
            FROM processes
            WHERE timestamp >= NOW() - interval '%s hours'
            GROUP BY name
            HAVING COUNT(*) > 10
            ORDER BY avg_cpu DESC
            LIMIT 10
        """

        df = pd.read_sql_query(query, self.conn, params=(hours,))
        return df

    def plot_process_cpu_usage(self, hours=24):
        """Plot top processes by CPU usage over time."""
        query = """
            SELECT
                timestamp,
                name,
                cpu_percent
            FROM processes
            WHERE
                timestamp >= NOW() - interval '%s hours'
                AND name IN (
                    SELECT name
                    FROM processes
                    WHERE timestamp >= NOW() - interval '%s hours'
                    GROUP BY name
                    ORDER BY AVG(cpu_percent) DESC
                    LIMIT 5
                )
        """

        df = pd.read_sql_query(query, self.conn, params=(hours, hours))

        plt.figure(figsize=(12, 6))
        sns.lineplot(data=df, x='timestamp', y='cpu_percent', hue='name')
        plt.title(f'Top Process CPU Usage Over Past {hours} Hours')
        plt.xlabel('Time')
        plt.ylabel('CPU Usage (%)')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the plot
        plt.savefig('cpu_usage.png')
        plt.close()

    def get_system_resource_trends(self, hours=24):
        """Get system resource usage trends."""
        query = """
            SELECT
                timestamp,
                cpu_percent,
                memory_percent,
                disk_percent
            FROM system_resources
            WHERE timestamp >= NOW() - interval '%s hours'
            ORDER BY timestamp
        """

        df = pd.read_sql_query(query, self.conn, params=(hours,))
        return df

    def plot_system_resources(self, hours=24):
        """Plot system resource usage over time."""
        df = self.get_system_resource_trends(hours)

        plt.figure(figsize=(12, 8))

        # Create three subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))

        # CPU Usage
        sns.lineplot(data=df, x='timestamp', y='cpu_percent', ax=ax1)
        ax1.set_title('CPU Usage Over Time')
        ax1.set_ylabel('CPU Usage (%)')

        # Memory Usage
        sns.lineplot(data=df, x='timestamp', y='memory_percent', ax=ax2)
        ax2.set_title('Memory Usage Over Time')
        ax2.set_ylabel('Memory Usage (%)')

        # Disk Usage
        sns.lineplot(data=df, x='timestamp', y='disk_percent', ax=ax3)
        ax3.set_title('Disk Usage Over Time')
        ax3.set_ylabel('Disk Usage (%)')

        # Adjust layout and save
        plt.tight_layout()
        plt.savefig('system_resources.png')
        plt.close()

    def get_active_window_summary(self, hours=24):
        """Get summary of time spent in different windows."""
        query = """
            SELECT
                active_window,
                COUNT(*) * 5 as seconds_spent  -- Assuming 5-second intervals
            FROM processes
            WHERE
                timestamp >= NOW() - interval '%s hours'
                AND active_window IS NOT NULL
            GROUP BY active_window
            ORDER BY seconds_spent DESC
            LIMIT 10
        """

        df = pd.read_sql_query(query, self.conn, params=(hours,))
        # Convert seconds to hours
        df['hours_spent'] = df['seconds_spent'] / 3600
        return df

    def __del__(self):
        """Close database connection when object is destroyed."""
        if hasattr(self, 'conn'):
            self.conn.close()