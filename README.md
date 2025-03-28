# PC Time Tracking

A comprehensive process monitoring and time tracking system that helps you understand how you use your computer.

## Features

- Real-time process monitoring
- System resource tracking (CPU, Memory, Disk)
- Active window detection (Windows and Linux)
- Process history logging
- Cross-platform support (Windows and Linux)
- Beautiful CLI interface with tabulated output

## Requirements

- Python 3.8 or higher
- Linux or Windows operating system
- Required Python packages (see requirements.txt)
- System packages (Linux):
  - xdotool (for window detection)
  - wmctrl (optional, fallback for window detection)
  - PostgreSQL (for data storage)
  - xprintidle (for idle detection)

## Installation

### Automated Setup (Recommended)

1. Clone the repository:

```bash
git clone https://github.com/yourusername/PC-Time-Tracking.git
cd PC-Time-Tracking
```

2. Run the setup script with sudo privileges:

```bash
sudo python setup.py
```

This will:

- Install system dependencies (PostgreSQL, xdotool, wmctrl)
- Set up PostgreSQL database and user
- Create configuration file
- Install Python dependencies

### Manual Setup

If you prefer to set up manually:

1. Install system dependencies:

```bash
# For Arch Linux
sudo pacman -S xdotool wmctrl

# For Ubuntu/Debian
sudo apt-get install xdotool wmctrl
```

## Usage

Run the process monitor with default settings:

```bash
python main.py
```

Options:

- `--interval`: Set the monitoring interval in seconds (default: 1.0)
- `--output`: Save process history to a JSON file

Example:

```bash
python main.py --interval 2.0 --output process_history.json
```

## Current Implementation Details

### Process Monitoring

- Real-time tracking of all running processes
- Captures process details:
  - Process ID (PID)
  - Process Name
  - CPU Usage
  - Memory Usage
  - Creation Time
  - Running Duration

### System Resource Tracking

- CPU Usage
- Memory Usage (Total, Available, Percentage)
- Disk Usage (Total, Used, Percentage)

### Active Window Detection

- Windows: Uses win32gui
- Linux: Uses xdotool (primary) and wmctrl (fallback)
- Graceful fallback if window detection is not available

### Data Collection

- Continuous background monitoring
- Configurable update interval
- JSON-based process history storage
- Real-time CLI display with tabulated output

## Development

See [ROADMAP.md](ROADMAP.md) for detailed development plans and progress.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
