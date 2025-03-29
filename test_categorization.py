#!/usr/bin/env python3
"""Test script for process categorization functionality."""
import argparse
import json
from tabulate import tabulate
from process_categorizer import ProcessCategorizer
from process_monitor import ProcessMonitor
import psutil
from pathlib import Path

def test_current_processes():
    """Test categorization of currently running processes."""
    categorizer = ProcessCategorizer()

    # Get current processes
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            process_info = proc.info
            name = process_info['name']
            category = categorizer.categorize_process(name)
            processes.append({
                'pid': process_info['pid'],
                'name': name,
                'category': category
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Group by category
    by_category = {}
    for proc in processes:
        category = proc['category']
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(proc)

    # Print results
    print("\n=== Process Categorization Test ===")
    print(f"Total processes: {len(processes)}")

    # Print category summary
    summary_data = []
    for category, procs in by_category.items():
        summary_data.append([
            category,
            len(procs),
            f"{len(procs)/len(processes)*100:.1f}%"
        ])

    # Sort by count
    summary_data.sort(key=lambda x: x[1], reverse=True)

    print("\nCategory Summary:")
    print(tabulate(summary_data, headers=['Category', 'Count', 'Percentage'], tablefmt="grid"))

    # Print sample processes for each category
    print("\nSample Processes by Category:")
    for category, procs in by_category.items():
        print(f"\n{category.upper()} ({len(procs)} processes):")
        # Take up to 5 samples
        samples = procs[:5]
        sample_data = [[proc['pid'], proc['name']] for proc in samples]
        print(tabulate(sample_data, headers=['PID', 'Process Name'], tablefmt="simple"))

def create_custom_rules(output_file):
    """Create a template for custom categorization rules."""
    categorizer = ProcessCategorizer()

    # Get current processes
    processes = set()
    for proc in psutil.process_iter(['name']):
        try:
            processes.add(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Create a template with current categorization
    rules = {}
    for name in processes:
        rules[name] = categorizer.categorize_process(name)

    # Save to file
    with open(output_file, 'w') as f:
        json.dump(rules, f, indent=2, sort_keys=True)

    print(f"Custom rules template saved to {output_file}")
    print("You can edit this file to customize process categorization.")

def main():
    parser = argparse.ArgumentParser(description='Test Process Categorization')
    parser.add_argument('--create-rules', type=str,
                      help='Create template for custom categorization rules')
    parser.add_argument('--load-rules', type=str,
                      help='Load custom categorization rules from file')
    parser.add_argument('--save-output', type=str,
                      help='Save test results to file')

    args = parser.parse_args()

    if args.create_rules:
        create_custom_rules(args.create_rules)
        return

    # Initialize categorizer with custom rules if provided
    categorizer = ProcessCategorizer()
    if args.load_rules:
        categorizer.load_custom_rules(args.load_rules)
        print(f"Loaded custom rules from {args.load_rules}")

    # Run the test
    test_current_processes()

    if args.save_output:
        # Save current terminal output (unfortunately this doesn't work directly)
        # But we can save the loaded rules if any
        if args.load_rules:
            with open(args.save_output, 'w') as f:
                json.dump(categorizer.custom_rules, f, indent=2)
            print(f"Custom rules saved to {args.save_output}")

if __name__ == "__main__":
    main()