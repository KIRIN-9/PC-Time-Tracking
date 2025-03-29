"""Database configuration settings."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# PostgreSQL database configuration
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'pc_tracking'),
    'user': os.getenv('DB_USER', 'aura'),
    'password': os.getenv('DB_PASSWORD', 'auraX'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

# Environment configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Database connection string
DB_URI = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# SSL configuration for production
if ENVIRONMENT == 'production':
    DB_CONFIG['sslmode'] = 'require'
    DB_URI += "?sslmode=require"
