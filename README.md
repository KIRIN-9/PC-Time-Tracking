# PC Time Tracking

A comprehensive process monitoring and time tracking system that helps you understand how you use your computer.

## Features

- Real-time process monitoring
- System resource tracking (CPU, Memory, Disk)
- Active window detection (Windows and Linux)
- Process categorization and time analytics
- Process filtering and prioritization
- Interactive CLI with colorful interface
- Custom alerts and notifications
- Process history logging
- Idle time detection
- Cross-platform support (Windows and Linux)

## Requirements

- Python 3.8 or higher
- Linux or Windows operating system
- Required Python packages (see requirements.txt)
- System packages (Linux):
  - xdotool (for window detection)
  - wmctrl (optional, fallback for window detection)
  - PostgreSQL (for data storage)
  - xprintidle (for idle detection)
  - libnotify-bin (for desktop notifications)

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
sudo pacman -S xdotool wmctrl libnotify postgresql

# For Ubuntu/Debian
sudo apt-get install xdotool wmctrl libnotify-bin postgresql
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The application provides a unified command interface:

```bash
./pc_time_tracker.py [command] [options]
```

Available commands:

- `monitor` - Run the basic process monitor
- `cli` - Launch the interactive CLI interface
- `alerts` - Manage alerts and notifications
- `report` - Generate reports and visualizations

### Basic Monitoring

```bash
./pc_time_tracker.py monitor [--interval SECONDS] [--output FILE] [--summary] [--categories]
```

### Interactive CLI

```bash
./pc_time_tracker.py cli --interactive
```

The interactive CLI provides:

- Real-time process monitoring with colorful interface
- Multiple views (processes, categories, resources)
- Process selection and details
- Keyboard shortcuts for easy navigation

### Standard CLI

```bash
./pc_time_tracker.py cli [--view {processes,categories,resources}] [--refresh SECONDS]
```

### Managing Process Filters

List filter settings:

```bash
./pc_time_tracker.py filter list [--type {excluded,patterns,priorities,thresholds}]
```

Exclude/include processes:

```bash
./pc_time_tracker.py filter exclude "chrome"
./pc_time_tracker.py filter include "chrome"
```

Manage regex patterns:

```bash
./pc_time_tracker.py filter pattern "^python.*$"
./pc_time_tracker.py filter remove-pattern "^python.*$"
```

Set process priorities (1-5, 5 is highest):

```bash
./pc_time_tracker.py filter priority "code" 5
./pc_time_tracker.py filter remove-priority "code"
```

Set resource thresholds:

```bash
./pc_time_tracker.py filter threshold cpu 0.5
./pc_time_tracker.py filter threshold memory 1.0
```

Include/exclude system processes:

```bash
./pc_time_tracker.py filter system yes
./pc_time_tracker.py filter system no
```

Reset to defaults:

```bash
./pc_time_tracker.py filter reset
```

### Managing Alerts

List configured alerts:

```bash
./pc_time_tracker.py alerts list
```

Add a new alert:

```bash
./pc_time_tracker.py alerts add --type resource --name "High CPU" --description "CPU usage alert" --resource cpu --threshold 90
```

Alert types:

- `resource` - Monitor CPU, memory, or disk usage
- `process` - Alert when specific processes are running
- `category` - Alert when too much time is spent in a category
- `idle` - Alert after system has been idle for a period

Monitor alerts in real-time:

```bash
./pc_time_tracker.py alerts monitor
```

View alert history:

```bash
./pc_time_tracker.py alerts history
```

### Generate Reports

```bash
./pc_time_tracker.py report [--hours HOURS] [--categories-only] [--output DIRECTORY]
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
  - Category

### Process Categorization

- Automatic categorization of processes into meaningful groups:
  - Development
  - Productivity
  - Web Browsing
  - Entertainment
  - System
  - Uncategorized
- Customizable categories via configuration files
- Time distribution analysis by category
- Visual reports showing category usage over time

### Process Filtering & Prioritization

- Filter out unwanted processes from monitoring
  - Exclude specific processes by name
  - Exclude processes matching regex patterns
  - Filter based on CPU and memory usage thresholds
  - Option to include/exclude system processes
- Prioritize important processes
  - Assign priority levels (1-5) to processes
  - Sort and display processes by priority
  - Focus on high-priority processes in reports
- Resource limits (planned)
  - Set CPU usage limits
  - Set memory usage limits
  - Enforce resource restrictions

### System Resource Tracking

- CPU Usage
- Memory Usage (Total, Available, Percentage)
- Disk Usage (Total, Used, Percentage)

### Alert System

- Resource usage alerts (CPU, memory, disk)
- Process-specific alerts
- Category usage time limits
- Idle time notifications
- Desktop notifications
- Configurable alert thresholds
- Alert history tracking

### CLI Interface

- Interactive mode with curses interface
- Multiple view modes
- Customizable refresh rate
- Sort processes by different criteria
- Color-coded interface
- Keyboard shortcuts

### Idle Detection

- Tracks computer idle time
- Configurable idle threshold
- Records idle periods for accurate time analysis

### Active Window Detection

- Windows: Uses win32gui
- Linux: Uses xdotool (primary) and wmctrl (fallback)
- Graceful fallback if window detection is not available

### Data Collection

- Continuous background monitoring
- Configurable update interval
- Database storage with PostgreSQL
- Real-time CLI display with tabulated output

## Development

See [ROADMAP.md](ROADMAP.md) for detailed development plans and progress.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
