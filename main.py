import psutil
import json

def get_processes():
    process_list = []
    for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            process_list.append({
                "pid": proc.info['pid'],
                "name": proc.info['name'],
                "cpu_percent": proc.info['cpu_percent'],
                "memory_mb": round(proc.info['memory_info'].rss / (1024 * 1024), 2)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return process_list

def save_processes_to_json(filename="processes.json"):
    processes = get_processes()
    with open(filename, "w") as f:
        json.dump(processes, f, indent=4)
    print(f"Process data saved to {filename}")

def print_processes():
    processes = get_processes()
    print(f"{'PID':<10}{'Name':<30}{'CPU%':<10}{'Memory(MB)':<10}")
    print("="*60)
    for p in processes[:10]:  # Display only top 10 for readability
        print(f"{p['pid']:<10}{p['name']:<30}{p['cpu_percent']:<10}{p['memory_mb']:<10}")

if __name__ == "__main__":
    print_processes()
    save_processes_to_json()
