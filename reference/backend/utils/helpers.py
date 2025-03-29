"""
Helper functions for the PC Time Tracker application.
"""
import os
import json
import datetime
from typing import Dict, Any, Optional, List, Union

def load_json_file(file_path: str, default: Dict = None) -> Dict:
    """
    Load a JSON file, returning a default value if the file doesn't exist.

    Args:
        file_path: Path to the JSON file
        default: Default value to return if file doesn't exist or is invalid

    Returns:
        The JSON data as a dictionary, or the default value
    """
    if default is None:
        default = {}

    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return default
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading JSON file {file_path}: {e}")
        return default

def save_json_file(file_path: str, data: Dict, indent: int = 2) -> bool:
    """
    Save data to a JSON file.

    Args:
        file_path: Path to the JSON file
        data: Data to save
        indent: JSON indentation level

    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=indent)
        return True
    except OSError as e:
        print(f"Error saving JSON file {file_path}: {e}")
        return False

def format_timedelta(delta: datetime.timedelta) -> str:
    """
    Format a timedelta object into a human-readable string.

    Args:
        delta: The timedelta object to format

    Returns:
        A string representation of the timedelta
    """
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def format_bytes(num_bytes: int) -> str:
    """
    Format a number of bytes into a human-readable string.

    Args:
        num_bytes: The number of bytes to format

    Returns:
        A string representation of the bytes
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"