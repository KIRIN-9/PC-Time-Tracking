#!/usr/bin/env python3
"""
Script to reset the database schema for PC Time Tracker.
This will drop and recreate all tables, deleting any existing data.
"""
import os
import sys
import psycopg2
import dotenv
from typing import List, Dict, Optional

def reset_database():
    # Load .env file if it exists
    dotenv.load_dotenv()

    # Construct DB URI
    db_name = os.getenv("DB_NAME", "pc_time_tracking")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    # Connect to database
    print(f"Connecting to database: {db_uri}")
    conn = psycopg2.connect(db_uri)
    cur = conn.cursor()

    try:
        # Drop tables if they exist
        print("Dropping existing tables...")
        cur.execute("DROP TABLE IF EXISTS processes")
        cur.execute("DROP TABLE IF EXISTS system_resources")
        cur.execute("DROP TABLE IF EXISTS idle_times")
        conn.commit()

        # Create processes table
        print("Creating processes table...")
        cur.execute("""
            CREATE TABLE processes (
                id SERIAL PRIMARY KEY,
                pid INTEGER NOT NULL,
                name TEXT NOT NULL,
                cpu_percent FLOAT,
                memory_percent FLOAT,
                category TEXT,
                active_window TEXT,
                create_time TIMESTAMP,
                timestamp TIMESTAMP NOT NULL
            )
        """)

        # Create system resources table
        print("Creating system_resources table...")
        cur.execute("""
            CREATE TABLE system_resources (
                id SERIAL PRIMARY KEY,
                cpu_percent FLOAT,
                memory_percent FLOAT,
                disk_percent FLOAT,
                memory_total BIGINT,
                memory_available BIGINT,
                timestamp TIMESTAMP NOT NULL
            )
        """)

        # Create idle time table
        print("Creating idle_times table...")
        cur.execute("""
            CREATE TABLE idle_times (
                id SERIAL PRIMARY KEY,
                is_idle BOOLEAN NOT NULL,
                idle_time INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL
            )
        """)

        conn.commit()
        print("Database schema reset successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error resetting database schema: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("WARNING: This will delete all existing data in the PC Time Tracker database.")
    response = input("Do you want to continue? (y/N): ")

    if response.lower() == 'y':
        reset_database()
    else:
        print("Operation cancelled.")