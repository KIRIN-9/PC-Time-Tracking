"""Process categorization for PC Time Tracking."""
import re
import json
import os
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import DictCursor
from config import DB_URI

class ProcessCategorizer:
    # Default categories
    DEFAULT_CATEGORIES = {
        "development": [
            "code", "visual studio", "pycharm", "intellij", "eclipse", "android studio",
            "vim", "emacs", "sublime", "atom", "vscode", "terminal", "cmd", "powershell",
            "git", "npm", "node", "python", "java", "gcc", "clang", "make", "gradle", "maven"
        ],
        "productivity": [
            "office", "word", "excel", "powerpoint", "outlook", "teams", "zoom", "slack",
            "notion", "evernote", "onenote", "google docs", "sheets", "slides", "calendar",
            "trello", "jira", "asana", "notion"
        ],
        "web_browsing": [
            "chrome", "firefox", "edge", "safari", "opera", "brave", "vivaldi"
        ],
        "entertainment": [
            "vlc", "netflix", "spotify", "youtube", "hulu", "plex", "steam", "epic games",
            "discord", "game", "player", "media", "music", "video"
        ],
        "system": [
            "explorer", "finder", "systemd", "system", "service", "daemon", "kernel",
            "svchost", "winlogon", "init", "launchd", "wininit", "csrss"
        ]
    }

    def __init__(self, custom_categories_file: Optional[str] = None):
        """Initialize the process categorizer.

        Args:
            custom_categories_file: Optional path to JSON file with custom categories
        """
        self.categories = self.DEFAULT_CATEGORIES.copy()
        self.custom_rules = {}

        # Load custom categories if provided
        if custom_categories_file and os.path.exists(custom_categories_file):
            try:
                with open(custom_categories_file, 'r') as f:
                    custom_categories = json.load(f)

                # Merge custom categories with defaults
                for category, keywords in custom_categories.items():
                    if category in self.categories:
                        self.categories[category].extend(keywords)
                    else:
                        self.categories[category] = keywords
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading custom categories: {e}")

    def categorize_process(self, process_name: str) -> str:
        """Categorize a process based on its name.

        Args:
            process_name: Name of the process to categorize

        Returns:
            Category name as string
        """
        # Check if we have a custom rule for this exact process
        if process_name in self.custom_rules:
            return self.custom_rules[process_name]

        # Convert to lowercase for case-insensitive matching
        name_lower = process_name.lower()

        # Check each category's keywords
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword.lower() in name_lower:
                    return category

        # Default category if no match found
        return "uncategorized"

    def add_custom_rule(self, process_name: str, category: str) -> None:
        """Add a custom categorization rule for a specific process.

        Args:
            process_name: The exact process name to match
            category: The category to assign
        """
        self.custom_rules[process_name] = category

    def save_custom_rules(self, output_file: str) -> None:
        """Save custom categorization rules to a JSON file.

        Args:
            output_file: Path to the output JSON file
        """
        with open(output_file, 'w') as f:
            json.dump(self.custom_rules, f, indent=2)

    def load_custom_rules(self, input_file: str) -> None:
        """Load custom categorization rules from a JSON file.

        Args:
            input_file: Path to the input JSON file
        """
        if os.path.exists(input_file):
            try:
                with open(input_file, 'r') as f:
                    self.custom_rules = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading custom rules: {e}")

    def update_database_categories(self) -> None:
        """Update process categories in the database."""
        # First check if categories column exists, if not add it
        with psycopg2.connect(DB_URI) as conn:
            cursor = conn.cursor()

            # Check if category column exists
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='processes' AND column_name='category'
            """)

            if cursor.fetchone() is None:
                # Add category column
                cursor.execute("""
                    ALTER TABLE processes
                    ADD COLUMN category VARCHAR(50)
                """)
                conn.commit()

            # Get all distinct process names
            cursor.execute("SELECT DISTINCT name FROM processes")
            process_names = [row[0] for row in cursor.fetchall()]

            # Update categories for each process
            for name in process_names:
                category = self.categorize_process(name)
                cursor.execute("""
                    UPDATE processes
                    SET category = %s
                    WHERE name = %s
                """, (category, name))

            conn.commit()

    def get_category_summary(self, hours: int = 24) -> Dict[str, int]:
        """Get summary of time spent in each category over the specified time period.

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary mapping categories to seconds spent
        """
        with psycopg2.connect(DB_URI) as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)

            # Make sure categories are updated first
            self.update_database_categories()

            # Get category summary
            cursor.execute("""
                SELECT
                    category,
                    COUNT(*) * 5 as seconds_spent  -- Assuming 5-second intervals
                FROM processes
                WHERE timestamp >= NOW() - interval '%s hours'
                GROUP BY category
                ORDER BY seconds_spent DESC
            """, (hours,))

            return {row['category']: row['seconds_spent'] for row in cursor.fetchall()}