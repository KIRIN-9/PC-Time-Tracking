# PC Time Tracker

A productivity tracking tool with a bpytop-like interface that monitors your processes and work patterns.

## Features

- Real-time process monitoring with CPU and memory usage
- Work session tracking with break detection
- Focus and productivity metrics
- Project-based time tracking
- PostgreSQL storage for historical data

## Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/PC-Time-Tracking.git
cd PC-Time-Tracking
```

2. Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

5. Run the application:

```bash
python main.py
```

## Project Structure

```
PC-Time-Tracking/
├── src/
│   ├── core/          # Process monitoring and core logic
│   ├── database/      # Database models and connection
│   └── ui/           # Terminal UI components
├── main.py           # Application entry point
├── requirements.txt  # Python dependencies
├── .env.example      # Example environment variables
└── README.md        # This file
```

## Usage

The application provides a terminal user interface similar to bpytop with:

- Process list with CPU/Memory usage
- Work session timeline
- Break timer
- Focus metrics
- Project tracking

Press `q` to quit, `h` for help menu.

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```
DATABASE_URL=postgresql://user:password@localhost/pc_time_tracking
DB_NAME=pc_time_tracking
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### Process Categories

You can customize process categories in the web interface or by editing the configuration file.

### Filter Settings

Adjust process filtering settings in the web interface to control which processes are tracked.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
