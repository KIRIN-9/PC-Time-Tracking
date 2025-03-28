"""Database configuration settings."""

# PostgreSQL database configuration
DB_CONFIG = {
    'dbname': 'pc_time_tracking',
    'user': 'pctt_user',
    'password': 'your_password',
    'host': 'localhost',
    'port': '5432'
}

# Database connection string
DB_URI = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"