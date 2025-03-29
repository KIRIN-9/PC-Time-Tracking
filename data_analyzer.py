"""Data analysis and visualization module for PC Time Tracking."""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import DictCursor
from config import DB_URI
from process_categorizer import ProcessCategorizer

class DataAnalyzer:
    def __init__(self):
        """Initialize the DataAnalyzer with database connection."""
        self.conn = psycopg2.connect(DB_URI)
        self.categorizer = ProcessCategorizer()

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

    def get_category_summary(self, hours=24):
        """Get summary of time spent in different process categories."""
        # Ensure categories are updated in the database
        self.categorizer.update_database_categories()

        query = """
            SELECT
                category,
                COUNT(*) * 5 as seconds_spent  -- Assuming 5-second intervals
            FROM processes
            WHERE
                timestamp >= NOW() - interval '%s hours'
                AND category IS NOT NULL
            GROUP BY category
            ORDER BY seconds_spent DESC
        """

        df = pd.read_sql_query(query, self.conn, params=(hours,))
        # Convert seconds to hours
        df['hours_spent'] = df['seconds_spent'] / 3600
        return df

    def plot_category_distribution(self, hours=24):
        """Plot distribution of time spent in different process categories."""
        df = self.get_category_summary(hours)

        plt.figure(figsize=(10, 6))

        # Create pie chart
        plt.pie(df['hours_spent'], labels=df['category'], autopct='%1.1f%%')
        plt.title(f'Time Distribution by Process Category (Last {hours} Hours)')
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle

        # Save the plot
        plt.savefig('category_distribution.png')
        plt.close()

        # Also create a bar chart for comparison
        plt.figure(figsize=(10, 6))
        sns.barplot(data=df, x='category', y='hours_spent')
        plt.title(f'Time Spent by Process Category (Last {hours} Hours)')
        plt.xlabel('Category')
        plt.ylabel('Hours Spent')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the plot
        plt.savefig('category_hours.png')
        plt.close()

    def get_category_usage_over_time(self, hours=24, interval_minutes=30):
        """Get category usage over time with specified interval."""
        # Ensure categories are updated
        self.categorizer.update_database_categories()

        query = """
            SELECT
                category,
                date_trunc('hour', timestamp) +
                    make_interval(mins => floor(date_part('minute', timestamp) / %s) * %s) as time_bucket,
                COUNT(*) * 5 as seconds_spent
            FROM processes
            WHERE
                timestamp >= NOW() - interval '%s hours'
                AND category IS NOT NULL
            GROUP BY category, time_bucket
            ORDER BY time_bucket, category
        """

        df = pd.read_sql_query(query, self.conn, params=(interval_minutes, interval_minutes, hours))
        # Convert seconds to hours
        df['hours_spent'] = df['seconds_spent'] / 3600
        return df

    def plot_category_timeline(self, hours=24, interval_minutes=30):
        """Plot timeline of category usage over the specified period."""
        df = self.get_category_usage_over_time(hours, interval_minutes)

        # Pivot the data for stacked area chart
        pivot_df = df.pivot(index='time_bucket', columns='category', values='hours_spent').fillna(0)

        plt.figure(figsize=(12, 6))
        pivot_df.plot.area(stacked=True, figsize=(12, 6))
        plt.title(f'Process Category Usage Over Time (Last {hours} Hours)')
        plt.xlabel('Time')
        plt.ylabel('Hours Spent')
        plt.legend(title='Category', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()

        # Save the plot
        plt.savefig('category_timeline.png')
        plt.close()

    def __del__(self):
        """Close database connection when object is destroyed."""
        if hasattr(self, 'conn'):
            self.conn.close()