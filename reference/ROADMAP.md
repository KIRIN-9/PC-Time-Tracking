# Simplified Development Roadmap

## Part 1: CLI Process Monitor (Primary Focus)

### Core Features

- [ ] Real-time Process Monitoring
  - [ ] Process list with CPU/Memory usage (like bpytop)
  - [ ] Process start/end times
  - [ ] Active time tracking
  - [ ] Break detection
  - [ ] Work hours calculation
  - [ ] Focus/Break ratio tracking

### Database Integration

- [ ] PostgreSQL Setup
  - [ ] Environment configuration (.env)
  - [ ] Database schema for processes
  - [ ] Database schema for work sessions
  - [ ] Real-time data updates
  - [ ] Historical data storage

### CLI Interface

- [ ] Interactive Terminal UI
  - [ ] Process timeline view (like image)
  - [ ] Work hours summary
  - [ ] Break timer
  - [ ] Activity breakdown
  - [ ] Project tracking
  - [ ] Scores and metrics

### Data Analysis

- [ ] Productivity Metrics
  - [ ] Focus time calculation
  - [ ] Break patterns
  - [ ] Work patterns
  - [ ] Application usage statistics
  - [ ] Project time tracking

## Part 2: Web Interface

### Configuration

- [ ] Config File Setup
  - [ ] Database connection settings
  - [ ] Display preferences
  - [ ] Tracking rules
  - [ ] Categories and tags

### Data Visualization

- [ ] Timeline View
  - [ ] Daily activity timeline
  - [ ] Work blocks display
  - [ ] Break periods
  - [ ] Focus sessions

### Statistics Dashboard

- [ ] Productivity Metrics
  - [ ] Work hours summary
  - [ ] Focus/break ratio
  - [ ] Application usage
  - [ ] Project breakdown

Note: Part 1 must be fully functional and stable before moving to Part 2.
The web interface will only read and display data from the PostgreSQL database populated by the CLI tool.
