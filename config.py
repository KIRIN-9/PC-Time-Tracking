import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'pc_time_tracking')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # Application settings
    UPDATE_INTERVAL = float(os.getenv('UPDATE_INTERVAL', '1.0'))
    IDLE_THRESHOLD = int(os.getenv('IDLE_THRESHOLD', '300'))

    # UI settings
    PROCESS_LIST_WIDTH = 40
    TIMELINE_WIDTH = 80
    REFRESH_RATE = 1.0  # seconds

    # Process monitoring settings
    CPU_THRESHOLD = 0.1  # 10% CPU usage threshold for active process
    MEMORY_THRESHOLD = 50 * 1024 * 1024  # 50MB memory threshold

    # Colors for UI
    COLORS = {
        'active': 'green',
        'idle': 'yellow',
        'break': 'red',
        'text': 'white',
        'header': 'blue'
    }