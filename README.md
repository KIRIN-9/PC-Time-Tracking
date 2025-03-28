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

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/PC-Time-Tracking.git
cd PC-Time-Tracking
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
.\venv\Scripts\activate  # On Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install system dependencies (Linux):

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

## Development Roadmap

### Phase 1: Core Process Monitoring & Data Collection ✓

- [x] Process Tracking
- [x] Real-Time Monitoring
- [x] Foreground Process Detection
- [x] System Resource Monitoring
- [x] Process Start/Stop Logging

### Phase 2: Data Storage & Processing (In Progress)

- [ ] Database Integration
- [ ] Data Structuring & Categorization
- [ ] Historical Data & Trends
- [ ] Idle Time Detection
- [ ] Energy Consumption Tracking

### Phase 3: User Interaction & Control (Planned)

- [ ] CLI Interface
- [ ] Custom Alerts & Notifications
- [ ] Process Prioritization & Filtering
- [ ] Custom Scheduling & Automation
- [ ] Break & Focus Mode

### Phase 4: Web Dashboard & API (Planned)

- [ ] REST API for Remote Monitoring
- [ ] Web Dashboard
- [ ] Multi-User Authentication
- [ ] Data Export & Reports
- [ ] Remote Control for Processes

### Phase 5: Advanced Features & Enhancements (Planned)

- [ ] Application Window Focus Tracking
- [ ] Process Dependency Mapping
- [ ] Integration with External Tools
- [ ] AI-Based Insights
- [ ] Security & Privacy Controls

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
