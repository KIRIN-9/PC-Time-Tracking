from app import app
from flask import render_template, url_for, redirect, jsonify, request, send_file
from .systeminfo import *
from .processinfo import get_process_list, get_process_details
import os
import psutil
from datetime import datetime
import time
import platform
import signal
import ctypes
import socket

@app.route('/')
def main():
    # Main landing page with access to all features
    return render_template("main.html")

@app.route('/dashboard')
def index():
    context = {
        'platform_info': get_platform_info(),
        'power_info': get_power_info(),
        'user_info': get_user_info(),
        'memory_info': get_memory_info(),
        'disk_info': get_disks_info(),
        'network_info': get_network_info(),
    }

    return render_template("index.html", context=context)

@app.route('/processes')
def processes():
    context = {
        'platform_info': get_platform_info(),
        'process_list': get_process_list(),
    }
    return render_template("processes.html", context=context)

@app.route('/processes/<int:process_id>')
def process_details(process_id=None):
    if process_id != None:
        context = {
            'platform_info': get_platform_info(),
            'process_data': get_process_details(process_id)
        }
        return render_template("process_details.html", context=context)
    return redirect(url_for('processes'))

@app.route('/network')
def network():
    context = {
        'platform_info': get_platform_info(),
        'network_info': get_network_info(),
        'network_connections': psutil.net_connections(kind='inet'),
    }
    return render_template("network.html", context=context)

@app.route('/disks')
def disks():
    context = {
        'platform_info': get_platform_info(),
        'disk_info': get_disks_info(),
        'disk_io': psutil.disk_io_counters(perdisk=True),
    }
    return render_template("disks.html", context=context)

@app.route('/logs')
def logs():
    log_files = []
    
    # Windows-specific log directories and event logs
    windows_logs = [
        os.path.join(os.environ.get('SYSTEMROOT', 'C:\\Windows'), 'Logs'),
        os.path.join(os.environ.get('SYSTEMROOT', 'C:\\Windows'), 'debug'),
        os.path.join(os.environ.get('SYSTEMROOT', 'C:\\Windows'), 'system32', 'winevt', 'Logs'),
        os.path.join(os.environ.get('SYSTEMROOT', 'C:\\Windows'), 'System32', 'LogFiles'),
        os.path.join(os.environ.get('SYSTEMROOT', 'C:\\Windows'), 'System32', 'config'),
        os.path.join(os.environ.get('SYSTEMDRIVE', 'C:'), 'ProgramData', 'Microsoft', 'Windows', 'WER'),
        'C:\\ProgramData\\Microsoft\\Windows\\WER\\ReportArchive',
        'C:\\ProgramData\\Microsoft\\Windows\\WER\\ReportQueue'
    ]
    
    # Common log file extensions
    log_extensions = ['.log', '.txt', '.evt', '.evtx', '.etl', '.wer', '.dmp']
    
    # Check Windows logs
    for log_dir in windows_logs:
        if os.path.exists(log_dir):
            try:
                for root, dirs, files in os.walk(log_dir):
                    for file in files:
                        file_ext = os.path.splitext(file)[1].lower()
                        if file_ext in log_extensions:
                            try:
                                full_path = os.path.join(root, file)
                                file_size = os.path.getsize(full_path)
                                log_files.append({
                                    'name': file,
                                    'path': full_path,
                                    'size': bytes2human(file_size),
                                    'modified': datetime.fromtimestamp(os.path.getmtime(full_path))
                                })
                                # Limit to 50 files to prevent overload
                                if len(log_files) >= 50:
                                    break
                            except (PermissionError, OSError):
                                continue
                    if len(log_files) >= 50:
                        break
            except (PermissionError, OSError):
                pass
    
    # Also check application logs
    app_log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    if not os.path.exists(app_log_dir):
        os.makedirs(app_log_dir, exist_ok=True)
        # Create a sample log file
        with open(os.path.join(app_log_dir, 'app.log'), 'w') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Application started\n")
    
    # Add application logs
    if os.path.exists(app_log_dir):
        for file in os.listdir(app_log_dir):
            if file.endswith(tuple(log_extensions)):
                full_path = os.path.join(app_log_dir, file)
                log_files.append({
                    'name': file,
                    'path': full_path,
                    'size': bytes2human(os.path.getsize(full_path)),
                    'modified': datetime.fromtimestamp(os.path.getmtime(full_path))
                })
    
    # Sort logs by modification time (newest first)
    log_files.sort(key=lambda x: x['modified'], reverse=True)
    
    context = {
        'platform_info': get_platform_info(),
        'log_files': log_files,
    }
    return render_template("logs.html", context=context)

@app.route('/api/system-stats')
def system_stats():
    import psutil
    
    # Get CPU usage as percentage
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # Get memory usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    
    # Get disk usage for the main disk
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    
    # Get process count
    process_count = len(psutil.pids())
    
    # Get battery information
    battery_info = {
        'percent': 0,
        'power_plugged': False,
        'status': 'Unknown',
        'time_remaining': 'Unknown'
    }
    
    try:
        battery = psutil.sensors_battery()
        if battery:
            battery_info['percent'] = battery.percent
            battery_info['power_plugged'] = battery.power_plugged
            
            # Determine status
            if battery.power_plugged:
                if battery.percent >= 100:
                    battery_info['status'] = 'Fully Charged'
                else:
                    battery_info['status'] = 'Charging'
            else:
                battery_info['status'] = 'Discharging'
            
            # Calculate time remaining
            if not battery.power_plugged:
                try:
                    # Get battery drain rate over last minute
                    battery_rate = psutil.sensors_battery().percent
                    # Wait for a short time to calculate rate
                    time.sleep(0.5)
                    current_percent = psutil.sensors_battery().percent
                    drain_rate = (battery_rate - current_percent) * 2  # percent per minute

                    if drain_rate > 0:  # If battery is actually draining
                        # Calculate minutes remaining based on current drain rate
                        minutes_remaining = current_percent / drain_rate if drain_rate > 0 else 0
                        hours = int(minutes_remaining // 60)
                        minutes = int(minutes_remaining % 60)
                        battery_info['time_remaining'] = f"{hours}h {minutes}m remaining"
                    else:
                        # Fallback to system provided value if available and reasonable
                        if battery.secsleft > 0 and battery.secsleft < 43200:  # Less than 12 hours
                            hours, remainder = divmod(battery.secsleft, 3600)
                            minutes, _ = divmod(remainder, 60)
                            battery_info['time_remaining'] = f"{hours}h {minutes}m remaining"
                        else:
                            # Very rough estimate as last resort
                            hours = int((battery.percent / 100.0) * 4)  # Assuming 4 hours at 100%
                            minutes = int(((battery.percent / 100.0) * 4 - hours) * 60)
                            battery_info['time_remaining'] = f"{hours}h {minutes}m remaining (estimated)"
                except:
                    # Fallback to basic calculation if rate calculation fails
                    if battery.percent > 0:
                        hours = int((battery.percent / 100.0) * 4)  # Assuming 4 hours at 100%
                        minutes = int(((battery.percent / 100.0) * 4 - hours) * 60)
                        battery_info['time_remaining'] = f"{hours}h {minutes}m remaining (estimated)"
                    else:
                        battery_info['time_remaining'] = "Low battery"
            elif battery.power_plugged:
                if battery.percent >= 100:
                    battery_info['time_remaining'] = "Fully charged"
                else:
                    battery_info['time_remaining'] = "Charging"
    except Exception as e:
        # Battery might not be available on desktop systems
        battery_info['status'] = "Not available"
        battery_info['time_remaining'] = "N/A"
    
    return jsonify({
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'disk_percent': disk_percent,
        'process_count': process_count,
        'battery': battery_info
    })

@app.route('/api/system-info')
def system_info():
    import psutil
    import platform
    from datetime import datetime
    
    # Get platform information
    uname = platform.uname()
    boot_time = psutil.boot_time()
    platform_info = {
        'system': uname.system,
        'node': uname.node,
        'release': uname.release,
        'version': uname.version,
        'machine': uname.machine,
        'processor': uname.processor,
        'boot_time': str(datetime.now() - datetime.fromtimestamp(boot_time))
    }
    
    # Get memory information
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    memory_info = {
        'total': memory.total,
        'available': memory.available,
        'used': memory.used,
        'free': memory.free,
        'swap_total': swap.total,
        'swap_used': swap.used
    }
    
    # Get network information
    network_info = {}
    interfaces = psutil.net_if_addrs()
    io_counters = psutil.net_io_counters(pernic=True)
    stats = psutil.net_if_stats()
    
    for interface, addrs in interfaces.items():
        ipv4_addr = next((addr.address for addr in addrs if addr.family == 2), None)
        network_info[interface] = {
            'address': ipv4_addr,
            'bytes_sent': io_counters[interface].bytes_sent if interface in io_counters else 0,
            'bytes_recv': io_counters[interface].bytes_recv if interface in io_counters else 0,
            'isup': stats[interface].isup if interface in stats else False
        }
    
    return jsonify({
        'platform_info': platform_info,
        'memory_info': memory_info,
        'network_info': network_info
    })

@app.route('/api/processes')
def get_processes():
    import psutil
    from datetime import datetime
    
    processes = []
    try:
        # Get all processes with detailed info
        for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 'cpu_percent', 'memory_percent', 'create_time', 'num_threads']):
            try:
                pinfo = proc.info
                # Format create time
                create_time = datetime.fromtimestamp(pinfo['create_time'])
                pinfo['create_time'] = create_time.strftime('%Y-%m-%d %H:%M:%S')
                
                processes.append({
                    'pid': pinfo['pid'],
                    'name': pinfo['name'],
                    'username': pinfo['username'] or 'N/A',
                    'status': pinfo['status'],
                    'cpu_percent': pinfo['cpu_percent'] or 0.0,
                    'memory_percent': round(pinfo['memory_percent'] or 0.0, 1),
                    'num_threads': pinfo['num_threads'],
                    'create_time': pinfo['create_time']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Calculate accurate process statistics
        process_stats = {
            'total': len(processes),
            'running': len([p for p in processes if p['status'].lower() == 'running']),
            'sleeping': len([p for p in processes if p['status'].lower() == 'sleeping']),
            'stopped': len([p for p in processes if p['status'].lower() == 'stopped']),
            'zombie': len([p for p in processes if p['status'].lower() == 'zombie']),
            'disk_sleep': len([p for p in processes if p['status'].lower() == 'disk-sleep']),
            'idle': len([p for p in processes if p['status'].lower() == 'idle'])
        }
        
        # Sort processes by CPU usage for most active first
        processes.sort(key=lambda x: (x['cpu_percent'], x['memory_percent']), reverse=True)
        
        return jsonify({
            'processes': processes,
            'stats': process_stats
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'processes': [],
            'stats': {
                'total': 0,
                'running': 0,
                'sleeping': 0,
                'stopped': 0,
                'zombie': 0,
                'disk_sleep': 0,
                'idle': 0
            }
        }), 500

@app.route('/api/processes/<int:pid>/kill', methods=['POST'])
def kill_process(pid):
    def terminate_windows_process(pid):
        try:
            # Try using ctypes to get higher privileges
            kernel32 = ctypes.WinDLL('kernel32')
            handle = kernel32.OpenProcess(1, False, pid)
            if handle:
                kernel32.TerminateProcess(handle, -1)
                kernel32.CloseHandle(handle)
                return True
        except:
            pass
        
        try:
            # Fallback to taskkill without /F first
            import subprocess
            subprocess.run(['taskkill', '/PID', str(pid)], 
                         check=True, 
                         capture_output=True,
                         creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except:
            try:
                # Last resort: taskkill with /F
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                             check=True, 
                             capture_output=True,
                             creationflags=subprocess.CREATE_NO_WINDOW)
                return True
            except:
                return False
        
    def terminate_unix_process(pid):
        try:
            # Try SIGTERM first (graceful shutdown)
            os.kill(pid, signal.SIGTERM)
            return True
        except:
            try:
                # Try SIGKILL as last resort
                os.kill(pid, signal.SIGKILL)
                return True
            except:
                return False

    try:
        process = psutil.Process(pid)
        
        # Don't allow termination of critical system processes
        if process.name().lower() in ['system', 'systemd', 'svchost.exe', 'csrss.exe', 'winlogon.exe', 'services.exe']:
            return jsonify({
                'success': False,
                'error': 'Cannot terminate critical system process'
            })
        
        # Try psutil's terminate first
        try:
            process.terminate()
            process.wait(timeout=3)
            return jsonify({'success': True})
        except psutil.TimeoutExpired:
            pass
        except:
            pass
        
        # If psutil's terminate fails, try system-specific methods
        if platform.system() == 'Windows':
            if terminate_windows_process(pid):
                return jsonify({'success': True})
        else:
            if terminate_unix_process(pid):
                return jsonify({'success': True})
        
        # If all methods fail, try psutil's kill as last resort
        try:
            process.kill()
            return jsonify({'success': True})
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': 'Failed to terminate process. The process might require higher privileges or might have already terminated.'
        })
        
    except psutil.NoSuchProcess:
        return jsonify({
            'success': True,
            'message': 'Process has already terminated'
        })
    except psutil.AccessDenied:
        # Try system-specific methods if psutil is denied access
        if platform.system() == 'Windows':
            if terminate_windows_process(pid):
                return jsonify({'success': True})
        else:
            if terminate_unix_process(pid):
                return jsonify({'success': True})
        
        return jsonify({
            'success': False,
            'error': 'Access denied. The process might require higher privileges to terminate.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/processes/<int:pid>/stats')
def get_process_stats(pid):
    try:
        process = psutil.Process(pid)
        with process.oneshot():  # Get all info in a single system call
            # Get initial CPU percent
            process.cpu_percent()
            time.sleep(0.1)  # Wait for accurate measurement
            
            # Get memory info directly
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # Get I/O counters safely
            try:
                io_counters = process.io_counters()
                io_info = {
                    'read_bytes': io_counters.read_bytes,
                    'write_bytes': io_counters.write_bytes
                }
            except (psutil.AccessDenied, AttributeError):
                io_info = {'read_bytes': 0, 'write_bytes': 0}
            
            # Get process status
            try:
                status = process.status()
            except (psutil.AccessDenied, AttributeError):
                status = "unknown"
            
            # Get thread count
            try:
                num_threads = process.num_threads()
            except (psutil.AccessDenied, AttributeError):
                num_threads = 0
            
            return jsonify({
                'cpu_percent': process.cpu_percent(),
                'memory_percent': memory_percent,
                'memory_info': {
                    'rss': getattr(memory_info, 'rss', 0),  # Physical memory
                    'vms': getattr(memory_info, 'vms', 0)   # Virtual memory
                },
                'num_threads': num_threads,
                'status': status,
                'io_info': io_info
            })
            
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
        return jsonify({
            'error': str(e),
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'memory_info': {
                'rss': 0,
                'vms': 0
            },
            'io_info': {
                'read_bytes': 0,
                'write_bytes': 0
            },
            'num_threads': 0,
            'status': 'unknown'
        })

@app.route('/api/network')
def network_stats():
    try:
        # Get network interfaces information
        interfaces = {}
        if_addrs = psutil.net_if_addrs()
        io_counters = psutil.net_io_counters(pernic=True)
        stats = psutil.net_if_stats()
        
        for interface, addrs in if_addrs.items():
            ipv4_addr = next((addr.address for addr in addrs if addr.family == 2), None)
            
            # Get interface stats
            interface_stats = stats.get(interface, None)
            is_up = interface_stats.isup if interface_stats else False
            
            # Get I/O counters
            io_counter = io_counters.get(interface, None)
            bytes_sent = io_counter.bytes_sent if io_counter else 0
            bytes_recv = io_counter.bytes_recv if io_counter else 0
            
            # Calculate max bytes for percentage (use 1GB as reference)
            max_bytes = 1024 * 1024 * 1024  # 1GB
            
            interfaces[interface] = {
                'address': ipv4_addr,
                'bytes_sent': bytes_sent,
                'bytes_recv': bytes_recv,
                'max_bytes': max_bytes,
                'isup': is_up
            }
        
        # Get network connections
        connections = []
        for conn in psutil.net_connections(kind='inet'):
            try:
                connections.append({
                    'type': 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP',
                    'laddr': list(conn.laddr) if conn.laddr else None,
                    'raddr': list(conn.raddr) if conn.raddr else None,
                    'status': conn.status,
                    'pid': conn.pid
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return jsonify({
            'interfaces': interfaces,
            'connections': connections
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'interfaces': {},
            'connections': []
        })

@app.route('/api/disks')
def disk_stats():
    try:
        disk_info = get_disks_info()
        disk_io = get_disk_io()
        return jsonify({
            'disk_info': disk_info,
            'disk_io': disk_io,
            'success': True
        })
    except Exception as e:
        return jsonify({
            'disk_info': {},
            'disk_io': {},
            'success': False,
            'error': str(e)
        })

@app.route('/api/logs')
def get_logs():
    try:
        log_files = []
        
        # Windows-specific log directories and event logs
        windows_logs = [
            os.path.join(os.environ.get('SYSTEMROOT', 'C:\\Windows'), 'Logs'),
            os.path.join(os.environ.get('SYSTEMROOT', 'C:\\Windows'), 'debug'),
            os.path.join(os.environ.get('SYSTEMROOT', 'C:\\Windows'), 'system32', 'winevt', 'Logs'),
            os.path.join(os.environ.get('SYSTEMROOT', 'C:\\Windows'), 'System32', 'LogFiles'),
            os.path.join(os.environ.get('SYSTEMROOT', 'C:\\Windows'), 'System32', 'config'),
            os.path.join(os.environ.get('SYSTEMDRIVE', 'C:'), 'ProgramData', 'Microsoft', 'Windows', 'WER'),
            'C:\\ProgramData\\Microsoft\\Windows\\WER\\ReportArchive',
            'C:\\ProgramData\\Microsoft\\Windows\\WER\\ReportQueue'
        ]
        
        # Common log file extensions
        log_extensions = ['.log', '.txt', '.evt', '.evtx', '.etl', '.wer', '.dmp']
        
        # Check Windows logs
        for log_dir in windows_logs:
            if os.path.exists(log_dir):
                try:
                    for root, dirs, files in os.walk(log_dir):
                        for file in files:
                            file_ext = os.path.splitext(file)[1].lower()
                            if file_ext in log_extensions:
                                try:
                                    full_path = os.path.join(root, file)
                                    file_size = os.path.getsize(full_path)
                                    modified_time = datetime.fromtimestamp(os.path.getmtime(full_path))
                                    log_files.append({
                                        'name': file,
                                        'path': full_path,
                                        'size': bytes2human(file_size),
                                        'modified': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                                        'type': 'system' if 'windows' in full_path.lower() else 'application'
                                    })
                                    # Limit to 50 files to prevent overload
                                    if len(log_files) >= 50:
                                        break
                                except (PermissionError, OSError):
                                    continue
                        if len(log_files) >= 50:
                            break
                except (PermissionError, OSError):
                    pass
        
        # Also check application logs
        app_log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        if os.path.exists(app_log_dir):
            for file in os.listdir(app_log_dir):
                if file.endswith(tuple(log_extensions)):
                    full_path = os.path.join(app_log_dir, file)
                    modified_time = datetime.fromtimestamp(os.path.getmtime(full_path))
                    log_files.append({
                        'name': file,
                        'path': full_path,
                        'size': bytes2human(os.path.getsize(full_path)),
                        'modified': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'application'
                    })
        
        # Sort logs by modification time (newest first)
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'log_files': log_files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'log_files': []
        })

@app.route('/api/logs/content')
def get_log_content():
    try:
        log_path = request.args.get('path')
        download = request.args.get('download', 'false').lower() == 'true'
        
        if not log_path or not os.path.exists(log_path):
            return jsonify({
                'success': False,
                'error': 'Log file not found',
                'content': ''
            })
        
        if download:
            try:
                return send_file(
                    log_path,
                    as_attachment=True,
                    download_name=os.path.basename(log_path)
                )
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to download file: {str(e)}',
                    'content': ''
                })
            
        # Read last 100 lines of the log file
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-100:]
                content = ''.join(lines)
        except UnicodeDecodeError:
            try:
                with open(log_path, 'r', encoding='latin1') as f:
                    lines = f.readlines()[-100:]
                    content = ''.join(lines)
            except:
                return jsonify({
                    'success': False,
                    'error': 'Unable to read log file - it may be binary',
                    'content': ''
                })
                
        return jsonify({
            'success': True,
            'content': content
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'content': ''
        })
