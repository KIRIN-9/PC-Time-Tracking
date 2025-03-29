import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'pc_tracking')
    DB_USER = os.getenv('DB_USER', 'aura')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'auraX')

    # Application settings
    UPDATE_INTERVAL = 1.0  # Process monitoring interval in seconds
    IDLE_THRESHOLD = 300  # Seconds of CPU inactivity to consider as break

    # UI settings
    PROCESS_LIST_WIDTH = 40
    TIMELINE_WIDTH = 80
    REFRESH_RATE = 1.0  # seconds

    # Process monitoring settings
    CPU_THRESHOLD = 0.1  # 10% CPU usage threshold for active process
    MEMORY_THRESHOLD = 50 * 1024 * 1024  # 50MB memory threshold
    PROCESS_BATCH_SIZE = 50  # Number of processes to insert in a single batch

    # Analytics settings
    ANALYTICS_UPDATE_INTERVAL = 300  # Update analytics every 5 minutes
    PRODUCTIVITY_THRESHOLDS = {
        'high': 0.8,  # >80% focus ratio
        'medium': 0.6,  # >60% focus ratio
        'low': 0.4  # >40% focus ratio
    }

    # Hyprland settings
    WORKSPACE_IDLE_TIME = 60  # Time in seconds before marking a workspace as idle
    WINDOW_FOCUS_THRESHOLD = 5  # Minimum seconds to consider a window as focused

    # Colors for UI
    COLORS = {
        'active': 'green',
        'idle': 'yellow',
        'break': 'red',
        'text': 'white',
        'header': 'blue',
        'high_productivity': 'bright_green',
        'medium_productivity': 'yellow',
        'low_productivity': 'red'
    }