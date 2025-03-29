#!/usr/bin/env python3
"""Basic statistics visualization module for PC Time Tracking."""
import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate
from data_analyzer import DataAnalyzer

class StatsView:
    """Simple statistics visualization for PC Time Tracking."""

    def __init__(self):
        """Initialize the stats view with data analyzer."""
        self.analyzer = DataAnalyzer()
        self.output_dir = "stats"
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_basic_stats(self, hours=24):
        """Generate and save basic statistics reports."""
        # Process usage summary
        self._generate_process_usage_report(hours)

        # Category time distribution
        self._generate_category_report(hours)

        # System resources
        self._generate_system_resources_report(hours)

        print(f"Statistics reports generated in '{self.output_dir}' directory")

    def _generate_process_usage_report(self, hours):
        """Generate process usage report."""
        # Get process usage data
        df = self.analyzer.get_process_usage_summary(hours)

        # Save as CSV
        csv_path = os.path.join(self.output_dir, "process_usage.csv")
        df.to_csv(csv_path, index=False)

        # Generate plot
        plt.figure(figsize=(10, 6))
        df_plot = df.sort_values('avg_cpu', ascending=True).tail(10)
        df_plot.plot.barh(x='name', y='avg_cpu', color='blue', alpha=0.6, title=f'Top Processes by CPU Usage (Last {hours} Hours)')
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "top_processes_cpu.png"))
        plt.close()

        # Generate memory plot
        plt.figure(figsize=(10, 6))
        df_plot = df.sort_values('avg_memory', ascending=True).tail(10)
        df_plot.plot.barh(x='name', y='avg_memory', color='green', alpha=0.6, title=f'Top Processes by Memory Usage (Last {hours} Hours)')
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "top_processes_memory.png"))
        plt.close()

    def _generate_category_report(self, hours):
        """Generate category time distribution report."""
        # Get category summary
        df = self.analyzer.get_category_summary(hours)

        # Save as CSV
        csv_path = os.path.join(self.output_dir, "category_summary.csv")
        df.to_csv(csv_path, index=False)

        # Generate pie chart
        plt.figure(figsize=(10, 7))
        plt.pie(df['hours_spent'], labels=df['category'], autopct='%1.1f%%')
        plt.title(f'Time Distribution by Process Category (Last {hours} Hours)')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "category_distribution.png"))
        plt.close()

        # Generate bar chart
        plt.figure(figsize=(10, 6))
        df_sorted = df.sort_values('hours_spent', ascending=False)
        df_sorted.plot.bar(x='category', y='hours_spent', color='purple', alpha=0.7,
                          title=f'Hours Spent per Category (Last {hours} Hours)')
        plt.xlabel('Category')
        plt.ylabel('Hours')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "category_hours.png"))
        plt.close()

    def _generate_system_resources_report(self, hours):
        """Generate system resources report."""
        # Get system resource data
        df = self.analyzer.get_system_resource_trends(hours)

        # Save as CSV
        csv_path = os.path.join(self.output_dir, "system_resources.csv")
        df.to_csv(csv_path, index=False)

        # Generate plot with subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10))

        # CPU Usage subplot
        ax1.plot(df['timestamp'], df['cpu_percent'], color='red')
        ax1.set_title('CPU Usage')
        ax1.set_ylabel('CPU %')
        ax1.grid(True, alpha=0.3)

        # Memory Usage subplot
        ax2.plot(df['timestamp'], df['memory_percent'], color='blue')
        ax2.set_title('Memory Usage')
        ax2.set_ylabel('Memory %')
        ax2.grid(True, alpha=0.3)

        # Disk Usage subplot
        ax3.plot(df['timestamp'], df['disk_percent'], color='green')
        ax3.set_title('Disk Usage')
        ax3.set_ylabel('Disk %')
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "system_resources.png"))
        plt.close()

    def print_stats_summary(self, hours=24):
        """Print a summary of stats to the console."""
        print(f"\n===== PC Time Tracking Statistics Summary (Last {hours} Hours) =====\n")

        # Process usage summary
        print("=== Top Processes by CPU Usage ===")
        df = self.analyzer.get_process_usage_summary(hours)
        if not df.empty:
            table_data = df[['name', 'avg_cpu', 'max_cpu', 'avg_memory']].head(5).values.tolist()
            headers = ["Process", "Avg CPU %", "Max CPU %", "Avg Memory %"]
            print(tabulate(table_data, headers=headers, tablefmt="simple"))
        else:
            print("No process data available")

        # Category summary
        print("\n=== Time Spent by Category ===")
        df = self.analyzer.get_category_summary(hours)
        if not df.empty:
            table_data = []
            for _, row in df.iterrows():
                table_data.append([
                    row['category'],
                    f"{row['hours_spent']:.2f} hours"
                ])
            headers = ["Category", "Time Spent"]
            print(tabulate(table_data, headers=headers, tablefmt="simple"))
        else:
            print("No category data available")

        # System resources summary
        print("\n=== System Resources ===")
        df = self.analyzer.get_system_resource_trends(hours)
        if not df.empty:
            avg_cpu = df['cpu_percent'].mean()
            avg_memory = df['memory_percent'].mean()
            avg_disk = df['disk_percent'].mean()

            table_data = [
                ["CPU", f"{avg_cpu:.1f}%"],
                ["Memory", f"{avg_memory:.1f}%"],
                ["Disk", f"{avg_disk:.1f}%"]
            ]
            headers = ["Resource", "Average Usage"]
            print(tabulate(table_data, headers=headers, tablefmt="simple"))
        else:
            print("No resource data available")

def main():
    """Run the stats view as a standalone module."""
    import argparse

    parser = argparse.ArgumentParser(description="PC Time Tracking Statistics")
    parser.add_argument("--hours", type=int, default=24, help="Number of hours to include in statistics")
    parser.add_argument("--output", action="store_true", help="Generate output files")

    args = parser.parse_args()

    stats = StatsView()

    # Print summary to console
    stats.print_stats_summary(args.hours)

    # Generate output files if requested
    if args.output:
        stats.generate_basic_stats(args.hours)

if __name__ == "__main__":
    main()