#!/usr/bin/env python3
"""Generate analysis reports from PC Time Tracking data."""
import argparse
from tabulate import tabulate
from data_analyzer import DataAnalyzer

def format_time(seconds):
    """Format seconds into a human-readable string."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{int(hours)}h {int(minutes)}m"

def main():
    parser = argparse.ArgumentParser(description='Generate PC Time Tracking reports')
    parser.add_argument('--hours', type=int, default=24,
                      help='Number of hours to analyze (default: 24)')
    parser.add_argument('--no-plots', action='store_true',
                      help='Skip generating plots')
    parser.add_argument('--categories-only', action='store_true',
                      help='Only show category-based reports')
    args = parser.parse_args()

    analyzer = DataAnalyzer()

    if not args.categories_only:
        # Get process usage summary
        print("\n=== Process Usage Summary ===")
        process_summary = analyzer.get_process_usage_summary(args.hours)
        print(tabulate(process_summary, headers='keys', floatfmt=".2f", showindex=False))

        # Get active window summary
        print("\n=== Active Window Summary ===")
        window_summary = analyzer.get_active_window_summary(args.hours)
        # Format the time spent
        window_summary['time_spent'] = window_summary['seconds_spent'].apply(format_time)
        print(tabulate(window_summary[['active_window', 'time_spent']],
                      headers=['Window', 'Time Spent'],
                      showindex=False))

    # Get category summary
    print("\n=== Process Category Summary ===")
    category_summary = analyzer.get_category_summary(args.hours)
    # Format the time spent
    category_summary['time_spent'] = category_summary['seconds_spent'].apply(format_time)
    print(tabulate(category_summary[['category', 'time_spent', 'hours_spent']],
                  headers=['Category', 'Time Spent', 'Hours'],
                  floatfmt=".2f",
                  showindex=False))

    if not args.no_plots:
        print("\nGenerating plots...")

        if not args.categories_only:
            # Generate CPU usage plot
            analyzer.plot_process_cpu_usage(args.hours)
            print("- CPU usage plot saved as 'cpu_usage.png'")

            # Generate system resources plot
            analyzer.plot_system_resources(args.hours)
            print("- System resources plot saved as 'system_resources.png'")

        # Generate category distribution plots
        analyzer.plot_category_distribution(args.hours)
        print("- Category distribution plot saved as 'category_distribution.png'")
        print("- Category hours bar chart saved as 'category_hours.png'")

        # Generate category timeline
        analyzer.plot_category_timeline(args.hours)
        print("- Category timeline plot saved as 'category_timeline.png'")

if __name__ == '__main__':
    main()