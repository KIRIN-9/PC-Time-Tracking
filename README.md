# PC Time Tracking

A minimalist CLI process monitor for Arch Linux with Hyprland that tracks real-time system processes, work sessions, and break periods.

## Features

- Real-time process monitoring with CPU and memory usage
- Work session tracking with focus/break detection
- PostgreSQL database integration for data persistence
- Simple and efficient terminal user interface
- Minimal dependencies

## Requirements

- Python 3.8+
- PostgreSQL
- Arch Linux with Hyprland (optional)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/PC-Time-Tracking.git
cd PC-Time-Tracking
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up the database:

```bash
createdb pc_time_tracking
```

5. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your database credentials and preferences
```

## Usage

1. Start the monitor:

```bash
python main.py
```

2. The interface will show:

   - Active processes with CPU and memory usage
   - Current work session statistics
   - Focus/break ratio

3. Controls:
   - Press 'q' to quit
   - The monitor automatically detects idle periods and work sessions

## Database Schema

The application uses three main tables:

- `processes`: Stores process information and resource usage
- `work_sessions`: Tracks work sessions and their metrics
- `activity_timeline`: Records process activity over time

## Configuration

Edit the `.env` file to customize:

- Database connection settings
- Update intervals
- Idle detection thresholds
- UI preferences

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
