# PC Time Tracking Documentation

## Overview

PC Time Tracking is a comprehensive system monitoring tool that tracks processes, system resources, and user activity. It provides insights into how your computer is used, allowing you to analyze process and resource usage over time.

## Installation

### Prerequisites

- Python 3.6 or higher
- PostgreSQL database
- Required packages (specified in requirements.txt)

### Steps

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/pc-time-tracking.git
   cd pc-time-tracking
   ```

2. Create a virtual environment (optional but recommended):

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Create a PostgreSQL database for the application

5. Create a `.env` file with the following variables:

   ```
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

6. Initialize the database:
   ```
   python setup.py
   ```

## Basic Usage

### Starting the Monitor

To start monitoring in interactive mode:

```
python pc_time_tracker.py interactive
```

To monitor for a specific period:

```
python pc_time_tracker.py monitor --time 300 --interval 5
```

### Viewing Statistics

To view basic statistics:

```
python pc_time_tracker.py stats
```

To generate statistics files:

```
python pc_time_tracker.py stats --output
```

### Exporting Data

To export all tracking data:

```
python pc_time_tracker.py export
```

To export specific data types:

```
python pc_time_tracker.py export --type processes --format csv
```

## Features

### Process Monitoring

The application monitors all running processes and records information such as:

- Process name and PID
- CPU and memory usage
- Runtime
- Active window/foreground process

### System Resource Monitoring

System-wide resources are tracked:

- CPU usage
- Memory usage and availability
- Disk usage

### Process Categorization

Processes are categorized for better analysis:

- Default categories based on process types
- Custom categorization through configuration
- Time spent per category analysis

### Idle Detection

The system detects when the computer is idle:

- Configurable idle threshold
- Tracks idle periods
- Distinguishes between active and idle time

### Process Filtering

Filter which processes are tracked:

- Exclude specific processes
- Set process priorities
- Define resource thresholds
- Filtering by regex patterns

### Statistics and Visualization

Analyze usage patterns with:

- Process usage summaries
- Category time distribution
- System resource trends
- Usage visualization through charts and graphs

### Data Export

Export collected data for external analysis:

- CSV or JSON format
- Export specific data types
- Configurable time periods

## Command Line Interface

### Main Commands

- `interactive`: Interactive monitoring mode with curses UI
- `monitor`: Basic monitoring mode for specified duration
- `filter`: Process filtering operations
- `stats`: Statistics generation and viewing
- `export`: Data export functionality

### Process Filtering

- List filter settings:

  ```
  ./pc_time_tracker.py filter list --type all
  ```

- Exclude a process:

  ```
  ./pc_time_tracker.py filter exclude "chrome"
  ```

- Include a previously excluded process:

  ```
  ./pc_time_tracker.py filter include "chrome"
  ```

- Add a regex pattern filter:

  ```
  ./pc_time_tracker.py filter pattern "^python.*$"
  ```

- Remove a pattern:

  ```
  ./pc_time_tracker.py filter remove-pattern "^python.*$"
  ```

- Set process priority:

  ```
  ./pc_time_tracker.py filter priority "code" 5
  ```

- Remove process priority:

  ```
  ./pc_time_tracker.py filter remove-priority "code"
  ```

- Set resource threshold:

  ```
  ./pc_time_tracker.py filter cpu-threshold 10
  ./pc_time_tracker.py filter memory-threshold 15
  ```

- Include/exclude system processes:

  ```
  ./pc_time_tracker.py filter system include
  ./pc_time_tracker.py filter system exclude
  ```

- Reset all filters:
  ```
  ./pc_time_tracker.py filter reset
  ```

### Statistics

- View statistics for last 24 hours:

  ```
  ./pc_time_tracker.py stats
  ```

- View statistics for custom time period:

  ```
  ./pc_time_tracker.py stats --hours 48
  ```

- Generate statistics files:
  ```
  ./pc_time_tracker.py stats --output
  ```

### Data Export

- Export all data:

  ```
  ./pc_time_tracker.py export
  ```

- Export specific data:

  ```
  ./pc_time_tracker.py export --type processes
  ./pc_time_tracker.py export --type resources
  ./pc_time_tracker.py export --type categories
  ```

- Choose export format:

  ```
  ./pc_time_tracker.py export --format json
  ```

- Export data for custom time period:
  ```
  ./pc_time_tracker.py export --hours 48
  ```

## Interactive Mode

The interactive mode provides a TUI (Text User Interface) with the following views:

1. **Processes View**: Shows running processes with resource usage
2. **Categories View**: Shows time spent per process category
3. **Resources View**: Shows system resource usage
4. **Filter View**: Shows and allows editing filter settings

### Keyboard Controls

- Arrow keys: Navigate and select items
- Tab: Switch between views
- F5: Refresh data manually
- +/-: Adjust refresh rate
- S: Change sort order
- H: Toggle between showing all processes or top processes
- Q or Esc: Quit

## Configuration Files

### process_filter.json

Contains process filtering settings:

- Excluded processes
- Process priority settings
- Resource thresholds
- System process inclusion setting

### custom_categories.json

Defines custom process categorization rules

### alerts_config.json

Configures notification alerts for:

- High CPU usage
- High memory usage
- Process start/stop events

## Troubleshooting

### Common Issues

- **Database Connection Errors**: Ensure PostgreSQL is running and your `.env` file has correct credentials
- **Permission Errors**: Some system monitoring features may require elevated permissions
- **High CPU Usage**: Adjust the monitoring interval to reduce system load

### Logs

Check `alerts.log` for any alert notifications or issues.

## Development

### Architecture

The application consists of several modules:

- `process_monitor.py`: Core process tracking
- `database.py`: Database operations
- `process_categorizer.py`: Process categorization
- `process_filter.py`: Process filtering
- `data_analyzer.py`: Data analysis and reporting
- `stats_view.py`: Statistics visualization
- `data_export.py`: Data export functionality
- `idle_detector.py`: Idle state detection
- `cli.py`: Command-line interface

### Extending the Application

- Add new categories in `custom_categories.json`
- Implement custom analysis in `data_analyzer.py`
- Add new CLI commands in `cli.py`
