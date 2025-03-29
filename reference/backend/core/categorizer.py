import json
import os
import re
from typing import Dict, List, Optional
import psycopg2

class ProcessCategorizer:
    def __init__(self, categories_file: str = "custom_categories.json"):
        self.categories_file = categories_file
        self.categories = {}
        self.category_patterns = {}
        self._load_categories()

    def _load_categories(self):
        if os.path.exists(self.categories_file):
            try:
                with open(self.categories_file, 'r') as f:
                    data = json.load(f)
                    self.categories = data.get('categories', {})
                    self.category_patterns = data.get('patterns', {})
            except Exception as e:
                print(f"Error loading categories: {e}")
                self._init_default_categories()
        else:
            self._init_default_categories()

    def _init_default_categories(self):
        self.categories = {
            "Browser": ["chrome", "firefox", "brave", "edge", "safari", "opera"],
            "Development": ["code", "idea", "pycharm", "eclipse", "android studio", "vim", "emacs", "vscode", "atom"],
            "Communication": ["slack", "discord", "teams", "skype", "zoom", "telegram", "signal"],
            "Productivity": ["office", "word", "excel", "powerpoint", "docs", "sheets", "slides", "notes", "onenote"],
            "Media": ["spotify", "vlc", "music", "video", "netflix", "youtube", "media player"],
            "System": ["explorer", "finder", "systemd", "kernel", "gnome", "kde", "xorg", "wayland"],
            "Gaming": ["steam", "game", "epic games", "origin", "battle.net"]
        }

        self.category_patterns = {
            "Browser": [r"^chrome$", r"^firefox$", r"^brave$", r"^safari$", r"^edge$", r"^opera$"],
            "Development": [r"^code", r"^idea", r"^pycharm", r"^eclipse", r"^android.?studio", r"^vim", r"^emacs"],
            "Communication": [r"^slack$", r"^discord$", r"^teams$", r"^skype$", r"^zoom$", r"^telegram$", r"^signal$"],
            "System": [r"^systemd", r"^kernel", r"^gnome", r"^kde", r"^xorg", r"^wayland", r"^explorer$", r"^finder$"]
        }

        self._save_categories()

    def _save_categories(self):
        data = {
            "categories": self.categories,
            "patterns": self.category_patterns
        }

        try:
            with open(self.categories_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving categories: {e}")

    def categorize_process(self, process_name: str) -> str:
        process_name_lower = process_name.lower()

        # Check direct matches first
        for category, processes in self.categories.items():
            if process_name_lower in [p.lower() for p in processes]:
                return category

        # Check regex patterns
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                try:
                    if re.search(pattern, process_name_lower, re.IGNORECASE):
                        return category
                except re.error:
                    continue

        # Default category for uncategorized processes
        return "Other"

    def add_process_to_category(self, process_name: str, category: str):
        # Create category if it doesn't exist
        if category not in self.categories:
            self.categories[category] = []

        # Add process to category if not already present
        if process_name not in self.categories[category]:
            self.categories[category].append(process_name)
            self._save_categories()

    def add_pattern_to_category(self, pattern: str, category: str):
        # Validate pattern
        try:
            re.compile(pattern)
        except re.error:
            raise ValueError(f"Invalid regex pattern: {pattern}")

        # Create category if it doesn't exist
        if category not in self.category_patterns:
            self.category_patterns[category] = []

        # Add pattern to category if not already present
        if pattern not in self.category_patterns[category]:
            self.category_patterns[category].append(pattern)
            self._save_categories()

    def remove_process_from_category(self, process_name: str, category: str):
        if category in self.categories and process_name in self.categories[category]:
            self.categories[category].remove(process_name)
            self._save_categories()

    def remove_pattern_from_category(self, pattern: str, category: str):
        if category in self.category_patterns and pattern in self.category_patterns[category]:
            self.category_patterns[category].remove(pattern)
            self._save_categories()

    def get_category_summary(self, hours=24, db_connection=None) -> Dict[str, int]:
        if db_connection:
            try:
                query = """
                    SELECT category, COUNT(*) * 5 as seconds_spent
                    FROM processes
                    WHERE timestamp >= NOW() - interval '%s hours'
                      AND category IS NOT NULL
                    GROUP BY category
                    ORDER BY seconds_spent DESC
                """

                cursor = db_connection.cursor()
                cursor.execute(query, (hours,))

                result = {}
                for row in cursor.fetchall():
                    result[row[0]] = row[1]

                cursor.close()
                return result
            except Exception as e:
                print(f"Error getting category summary from database: {e}")
                return {}
        else:
            # Return empty summary if no database connection
            return {}

    def update_database_categories(self, db_connection=None):
        if not db_connection:
            return

        try:
            cursor = db_connection.cursor()

            # Get processes without categories
            cursor.execute("""
                SELECT DISTINCT name
                FROM processes
                WHERE category IS NULL
            """)

            for row in cursor.fetchall():
                process_name = row[0]
                category = self.categorize_process(process_name)

                # Update all occurrences of this process with the category
                cursor.execute("""
                    UPDATE processes
                    SET category = %s
                    WHERE name = %s AND category IS NULL
                """, (category, process_name))

            db_connection.commit()
            cursor.close()
        except Exception as e:
            print(f"Error updating database categories: {e}")
            if db_connection:
                db_connection.rollback()