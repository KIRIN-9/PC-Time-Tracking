#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API module for PC Time Tracker
Provides REST endpoints for the web dashboard
"""

import os
import json
import datetime
import csv
import io
from typing import Dict, List, Any, Optional, Tuple, Union
import threading
from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
from dotenv import load_dotenv

from core.monitor import ProcessMonitor
from core.database import Database
from core.filter import ProcessFilter
from core.idle import IdleDetector
from core.categorizer import ProcessCategorizer

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global objects
monitor = None
db = None
process_filter = None
idle_detector = None
categorizer = None
monitor_thread = None
monitoring_active = False
monitor_lock = threading.Lock()

def initialize_components():
    """Initialize all components"""
    global db, process_filter, idle_detector, categorizer, monitor

    # Initialize database
    db = Database()
    db.connect()
    db.init_schema()

    # Initialize process filter
    process_filter = ProcessFilter()

    # Initialize idle detector
    idle_detector = IdleDetector()

    # Initialize categorizer
    categorizer = ProcessCategorizer()

    # Initialize process monitor
    monitor = ProcessMonitor(db, process_filter, idle_detector, categorizer)

def start_monitoring():
    """Start the monitoring thread"""
    global monitor_thread, monitoring_active

    with monitor_lock:
        if monitoring_active:
            return

        monitoring_active = True

        if monitor_thread is None or not monitor_thread.is_alive():
            monitor_thread = threading.Thread(target=monitor.start_monitoring)
            monitor_thread.daemon = True
            monitor_thread.start()

def stop_monitoring():
    """Stop the monitoring thread"""
    global monitoring_active

    with monitor_lock:
        if not monitoring_active:
            return

        monitoring_active = False
        monitor.stop_monitoring()

@app.route('/api/processes', methods=['GET'])
def get_processes():
    """Get processes for a specific date"""
    date_str = request.args.get('date', datetime.date.today().isoformat())

    try:
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Get processes from database
    start_time = datetime.datetime.combine(date, datetime.time.min)
    end_time = datetime.datetime.combine(date, datetime.time.max)

    processes = db.get_processes_in_range(start_time, end_time)

    return jsonify({"processes": processes})

@app.route('/api/resources', methods=['GET'])
def get_resources():
    """Get system resources for a specific date"""
    date_str = request.args.get('date', datetime.date.today().isoformat())

    try:
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Get resources from database
    start_time = datetime.datetime.combine(date, datetime.time.min)
    end_time = datetime.datetime.combine(date, datetime.time.max)

    resources = db.get_resources_in_range(start_time, end_time)

    return jsonify({"resources": resources})

@app.route('/api/idle', methods=['GET'])
def get_idle_time():
    """Get idle time for a specific date"""
    date_str = request.args.get('date', datetime.date.today().isoformat())

    try:
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Get idle time from database
    start_time = datetime.datetime.combine(date, datetime.time.min)
    end_time = datetime.datetime.combine(date, datetime.time.max)

    idle_times = db.get_idle_times_in_range(start_time, end_time)

    return jsonify({"idle_times": idle_times})

@app.route('/api/tracking', methods=['POST'])
def toggle_tracking():
    """Toggle tracking on/off"""
    data = request.json

    if data and 'enabled' in data:
        enabled = data['enabled']

        if enabled:
            start_monitoring()
            return jsonify({"success": True, "tracking": True})
        else:
            stop_monitoring()
            return jsonify({"success": True, "tracking": False})

    return jsonify({"error": "Missing 'enabled' parameter"}), 400

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current tracking status"""
    return jsonify({
        "tracking": monitoring_active,
        "uptime": monitor.get_uptime() if monitor else 0,
        "version": "1.0.0"
    })

@app.route('/api/breaks', methods=['POST'])
def log_break():
    """Log a manual break"""
    data = request.json

    if not data or 'start_time' not in data or 'end_time' not in data:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        start_time = datetime.datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        end_time = datetime.datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"error": "Invalid datetime format"}), 400

    # Calculate break duration in seconds
    duration = (end_time - start_time).total_seconds()

    # Log as idle time
    db.save_idle_time(True, duration, start_time)

    return jsonify({"success": True, "duration": duration})

@app.route('/api/filters', methods=['GET', 'POST'])
def manage_filters():
    """Get or update filter settings"""
    if request.method == 'GET':
        # Return current filter settings
        return jsonify({
            "excluded_processes": process_filter.excluded_processes,
            "regex_patterns": process_filter.regex_patterns,
            "process_priorities": process_filter.process_priorities,
            "cpu_threshold": process_filter.cpu_threshold,
            "memory_threshold": process_filter.memory_threshold,
            "include_system_processes": process_filter.include_system_processes
        })
    else:
        # Update filter settings
        data = request.json

        if not data:
            return jsonify({"error": "No data provided"}), 400

        if 'excluded_processes' in data:
            process_filter.excluded_processes = data['excluded_processes']

        if 'regex_patterns' in data:
            process_filter.regex_patterns = data['regex_patterns']

        if 'process_priorities' in data:
            process_filter.process_priorities = data['process_priorities']

        if 'cpu_threshold' in data:
            process_filter.cpu_threshold = float(data['cpu_threshold'])

        if 'memory_threshold' in data:
            process_filter.memory_threshold = float(data['memory_threshold'])

        if 'include_system_processes' in data:
            process_filter.include_system_processes = bool(data['include_system_processes'])

        # Save filter settings
        process_filter.save_settings()

        return jsonify({"success": True})

@app.route('/api/export', methods=['GET'])
def export_data():
    """Export data for a date range"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    export_format = request.args.get('format', 'csv')

    if not start_date_str or not end_date_str:
        return jsonify({"error": "Missing start_date or end_date parameter"}), 400

    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Get data from database
    start_time = datetime.datetime.combine(start_date, datetime.time.min)
    end_time = datetime.datetime.combine(end_date, datetime.time.max)

    processes = db.get_processes_in_range(start_time, end_time)
    resources = db.get_resources_in_range(start_time, end_time)
    idle_times = db.get_idle_times_in_range(start_time, end_time)

    # Prepare export data
    if export_format == 'json':
        export_data = {
            "processes": processes,
            "resources": resources,
            "idle_times": idle_times
        }

        return jsonify(export_data)
    else:  # CSV format
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(['Type', 'Timestamp', 'PID', 'Name', 'CPU%', 'Memory%', 'Category',
                         'Active Window', 'Is Idle', 'Idle Time', 'Create Time'])

        # Write processes
        for process in processes:
            writer.writerow([
                'Process',
                process.get('timestamp', ''),
                process.get('pid', ''),
                process.get('name', ''),
                process.get('cpu_percent', ''),
                process.get('memory_percent', ''),
                process.get('category', ''),
                process.get('active_window', ''),
                '',
                '',
                process.get('create_time', '')
            ])

        # Write resources
        for resource in resources:
            writer.writerow([
                'Resource',
                resource.get('timestamp', ''),
                '',
                '',
                resource.get('cpu_percent', ''),
                resource.get('memory_percent', ''),
                '',
                '',
                '',
                '',
                ''
            ])

        # Write idle times
        for idle in idle_times:
            writer.writerow([
                'Idle',
                idle.get('timestamp', ''),
                '',
                '',
                '',
                '',
                '',
                '',
                idle.get('is_idle', ''),
                idle.get('idle_time', ''),
                ''
            ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=pc_time_tracker_export_{start_date_str}_{end_date_str}.csv'}
        )

@app.route('/api/categories', methods=['GET', 'POST'])
def manage_categories():
    """Get or update process categories"""
    if request.method == 'GET':
        # Return current categories
        return jsonify(categorizer.categories)
    else:
        # Update categories
        data = request.json

        if not data:
            return jsonify({"error": "No data provided"}), 400

        categorizer.categories = data
        categorizer.save_categories()

        return jsonify({"success": True})

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get usage statistics for a date range"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date', datetime.date.today().isoformat())

    if not start_date_str:
        return jsonify({"error": "Missing start_date parameter"}), 400

    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Get data from database
    start_time = datetime.datetime.combine(start_date, datetime.time.min)
    end_time = datetime.datetime.combine(end_date, datetime.time.max)

    # Get category summary from categorizer
    category_summary = categorizer.generate_category_summary(start_time, end_time)

    # Calculate idle vs. active time
    idle_times = db.get_idle_times_in_range(start_time, end_time)

    total_idle_seconds = sum(
        int(idle['idle_time']) for idle in idle_times if idle.get('is_idle', False)
    )

    # Calculate total tracked time
    total_time = (end_time - start_time).total_seconds()
    active_time = total_time - total_idle_seconds if total_time > total_idle_seconds else 0

    # Calculate focus time (development, code, documentation)
    focus_categories = ['Development', 'Code', 'Documentation', 'Design']
    focus_time = sum(
        category_summary.get(category, {}).get('seconds', 0)
        for category in focus_categories
        if category in category_summary
    )

    # Calculate meeting time
    meeting_categories = ['Meeting', 'Call', 'Communication']
    meeting_time = sum(
        category_summary.get(category, {}).get('seconds', 0)
        for category in meeting_categories
        if category in category_summary
    )

    return jsonify({
        "total_time": total_time,
        "active_time": active_time,
        "idle_time": total_idle_seconds,
        "focus_time": focus_time,
        "meeting_time": meeting_time,
        "categories": category_summary
    })

def run_api_server(port=5000, debug=False):
    """Run the API server"""
    initialize_components()
    start_monitoring()
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    run_api_server(debug=True)