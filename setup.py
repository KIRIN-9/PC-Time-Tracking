#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import getpass
import json
from pathlib import Path

def run_command(command, error_message="Command failed"):
    """Run a shell command and handle errors."""
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {error_message}")
        print(f"Command failed with exit code {e.returncode}")
        sys.exit(1)

def check_sudo():
    """Check if running with sudo privileges."""
    if os.geteuid() != 0:
        print("This script needs to be run with sudo privileges.")
        print("Please run: sudo python setup.py")
        sys.exit(1)

def install_system_dependencies():
    """Install system dependencies based on the OS."""
    system = platform.system()
    if system == "Linux":
        if os.path.exists("/etc/arch-release"):  # Arch Linux
            print("Installing system dependencies for Arch Linux...")
            run_command("pacman -S --noconfirm postgresql xdotool wmctrl",
                       "Failed to install system dependencies")
        elif os.path.exists("/etc/debian_version"):  # Debian/Ubuntu
            print("Installing system dependencies for Debian/Ubuntu...")
            run_command("apt-get update && apt-get install -y postgresql xdotool wmctrl",
                       "Failed to install system dependencies")
        else:
            print("Unsupported Linux distribution")
            sys.exit(1)
    elif system == "Windows":
        print("Windows is not supported for automated setup")
        sys.exit(1)
    else:
        print(f"Unsupported operating system: {system}")
        sys.exit(1)

def setup_postgresql():
    """Set up PostgreSQL database and user."""
    print("Setting up PostgreSQL...")

    # Initialize database if not already initialized
    if not os.path.exists("/var/lib/postgres/data/PG_VERSION"):
        print("Initializing PostgreSQL database...")
        run_command("sudo -u postgres initdb -D /var/lib/postgres/data",
                   "Failed to initialize PostgreSQL database")

    # Start PostgreSQL service
    print("Starting PostgreSQL service...")
    run_command("systemctl start postgresql",
                "Failed to start PostgreSQL service")
    run_command("systemctl enable postgresql",
                "Failed to enable PostgreSQL service")

    # Create database and user
    db_name = "pc_time_tracking"
    db_user = "pctt_user"
    db_password = "pctt_password"  # You might want to make this configurable

    print("Creating database and user...")
    commands = [
        f"sudo -u postgres psql -c 'CREATE DATABASE {db_name};'",
        f"sudo -u postgres psql -c \"CREATE USER {db_user} WITH PASSWORD '{db_password}';\"",
        f"sudo -u postgres psql -c 'GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};'",
        f"sudo -u postgres psql -d {db_name} -c 'GRANT ALL ON SCHEMA public TO {db_user};'",
        f"sudo -u postgres psql -d {db_name} -c 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {db_user};'",
        f"sudo -u postgres psql -d {db_name} -c 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {db_user};'"
    ]

    for cmd in commands:
        run_command(cmd, "Failed to execute PostgreSQL command")

    return db_password

def create_config_file(db_password):
    """Create or update the config.py file with database credentials."""
    config_content = f'''"""Database configuration settings."""

# PostgreSQL database configuration
DB_CONFIG = {{
    'dbname': 'pc_time_tracking',
    'user': 'pctt_user',
    'password': '{db_password}',
    'host': 'localhost',
    'port': '5432'
}}

# Database connection string
DB_URI = f"postgresql://{{DB_CONFIG['user']}}:{{DB_CONFIG['password']}}@{{DB_CONFIG['host']}}:{{DB_CONFIG['port']}}/{{DB_CONFIG['dbname']}}"
'''

    with open('config.py', 'w') as f:
        f.write(config_content)
    print("Created config.py with database credentials")

def install_python_dependencies():
    """Install Python dependencies using pip."""
    print("Installing Python dependencies...")
    run_command("pip install -r requirements.txt",
                "Failed to install Python dependencies")

def main():
    print("Starting PC Time Tracking setup...")

    # Check for sudo privileges
    check_sudo()

    # Install system dependencies
    install_system_dependencies()

    # Setup PostgreSQL
    db_password = setup_postgresql()

    # Create config file
    create_config_file(db_password)

    # Install Python dependencies
    install_python_dependencies()

    print("\nSetup completed successfully!")
    print("\nYou can now run the program with:")
    print("python main.py")
    print("\nOr with summary statistics:")
    print("python main.py --summary")

if __name__ == "__main__":
    main()