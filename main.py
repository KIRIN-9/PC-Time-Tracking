import psutil
import json
from datetime import datetime
from tabulate import tabulate
import time
import os

def get_process_info():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'create_time']):
        try:
            process_info = proc.info
            pid = process_info['pid']
            name = process_info['name']
            proc.cpu_percent()
            memory_mb = process_info['memory_info'].rss / (1024 * 1024)

            # Calculate running time in seconds
            create_time = process_info['create_time']
            running_time = time.time() - create_time

            process_dict = {
                'pid': pid,
                'name': name,
                'cpu_percent': proc.cpu_percent(),
                'memory_mb': round(memory_mb, 2),
                'running_time': running_time
            }
            processes.append(process_dict)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes

def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

def save_process_data(processes):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # filename = f"process_data_{timestamp}.json"
    filename = f"process_data.json"
    with open(filename, 'w') as file:
        json.dump(processes, file, indent=4)
    print(f"Process data saved to {filename}")
    return filename

def display_process_table(processes):
    sorted_processes = sorted(processes, key=lambda x: x['memory_mb'], reverse=True)
    table_data = [
        [p['pid'], p['name'], f"{p['cpu_percent']:.1f}%", f"{p['memory_mb']:.2f}", format_time(p['running_time'])]
        for p in sorted_processes
    ]
    headers = ["PID", "Process Name", "CPU %", "Memory (MB)", "Running Time"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def main():
    print("Fetching running processes...")
    processes = get_process_info()
    print(f"Found {len(processes)} running processes")
    save_process_data(processes)
    print("\nCurrent Running Processes:")
    display_process_table(processes)

if __name__ == "__main__":
    main()