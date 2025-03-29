# PC Time Tracking

A cross-platform tool for monitoring and analyzing PC usage and application time.

## Features

- Process monitoring with detailed statistics
- System resource tracking (CPU, memory, disk usage)
- Idle time detection
- Process filtering and prioritization
- Process categorization
- REST API for data access
- Web dashboard for visualizing productivity
- Work and break tracking
- Exportable data in CSV or JSON format

## Architecture

The application is split into backend and frontend components:

- **Backend**: Python-based process monitoring engine with a REST API
- **Frontend**: JavaScript-based web dashboard for data visualization

## Installation

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/PC-Time-Tracking.git
   cd PC-Time-Tracking
   ```

2. Create a virtual environment and install dependencies:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:

   ```
   cp .env.example .env
   ```

   Edit the `.env` file to set your database connection details.

## Usage

### Starting the Application

To start the application with the dashboard:

```
./pc_time_tracker.py start
```

This will start both the API server and web server, and open the dashboard in your default web browser.

Additional options:

- `--api-port PORT` - Set custom API port (default: 5000)
- `--web-port PORT` - Set custom web port (default: 8080)
- `--no-browser` - Do not open browser automatically

### Checking Application Status

```
./pc_time_tracker.py status
```

### Managing Process Filters

List filter settings:

```
./pc_time_tracker.py filter list [--type {excluded,patterns,priorities,thresholds,all}]
```

Exclude/include processes:

```
./pc_time_tracker.py filter exclude "chrome"
./pc_time_tracker.py filter include "chrome"
```

Manage regex patterns:

```
./pc_time_tracker.py filter pattern "^python.*$"
./pc_time_tracker.py filter remove-pattern "^python.*$"
```

Set process priorities:

```
./pc_time_tracker.py filter priority "code" 5
./pc_time_tracker.py filter remove-priority "code"
```

Set resource thresholds:

```
./pc_time_tracker.py filter cpu-threshold 0.5
./pc_time_tracker.py filter memory-threshold 0.5
```

Include/exclude system processes:

```
./pc_time_tracker.py filter include-system
./pc_time_tracker.py filter exclude-system
```

Reset filters to defaults:

```
./pc_time_tracker.py filter reset
```

### Managing Process Categories

List categories:

```
./pc_time_tracker.py category list
```

Add/remove processes from categories:

```
./pc_time_tracker.py category add "chrome" "Browser"
./pc_time_tracker.py category remove "chrome" "Browser"
```

Add/remove regex patterns from categories:

```
./pc_time_tracker.py category add-pattern "^chrome.*$" "Browser"
./pc_time_tracker.py category remove-pattern "^chrome.*$" "Browser"
```

Create/delete categories:

```
./pc_time_tracker.py category create "Custom"
./pc_time_tracker.py category delete "Custom"
```

Reset categories to defaults:

```
./pc_time_tracker.py category reset
```

## Web Dashboard

The web dashboard provides a visual interface for monitoring and analyzing your computer usage data. It includes:

- Timeline visualization of your work day
- Work hours tracking and statistics
- Break timer and break-to-work ratio
- Recent activity tracking
- Work blocks visualization
- Project and category time breakdown
- Focus, meetings, and breaks scores

To access the dashboard, navigate to `http://localhost:8080` in your web browser after starting the application.

## REST API

The application exposes a REST API on port 5000 by default. Available endpoints:

- `GET /api/processes?date=YYYY-MM-DD` - Get processes for a specific date
- `GET /api/resources?date=YYYY-MM-DD` - Get system resources for a specific date
- `GET /api/idle?date=YYYY-MM-DD` - Get idle time data for a specific date
- `POST /api/tracking` - Toggle tracking on/off
- `GET /api/status` - Get current tracking status
- `POST /api/breaks` - Log a manual break
- `GET/POST /api/filters` - Get or update filter settings
- `GET /api/export?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&format=csv` - Export data
- `GET/POST /api/categories` - Get or update process categories
- `GET /api/statistics?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Get usage statistics

## Data Export

To export your tracking data, use the API endpoint or the following command:

```
curl -o export.csv "http://localhost:5000/api/export?start_date=2023-01-01&end_date=2023-01-31&format=csv"
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
