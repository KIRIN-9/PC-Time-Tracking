from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Tuple, Any

class ProductivityTracker:
    def __init__(self, data_file=None):
        """Initialize the productivity tracker with optional data file path."""
        self.data_file = data_file or os.path.join(os.path.dirname(__file__), 'data', 'productivity_data.json')
        self.today = datetime.now().date()
        self._ensure_data_file()

    def _ensure_data_file(self):
        """Ensure the data file exists, create it if it doesn't."""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({
                    "activities": [],
                    "workblocks": [],
                    "settings": {
                        "categories": [
                            {"name": "Focus", "color": "#00E5B9"},
                            {"name": "Meetings", "color": "#9747FF"},
                            {"name": "Breaks", "color": "#3E7BFA"},
                            {"name": "Code", "color": "#00E5B9"},
                            {"name": "Documentation", "color": "#00E5B9"},
                            {"name": "Design", "color": "#00E5B9"},
                            {"name": "Messaging", "color": "#9747FF"},
                            {"name": "Email", "color": "#9747FF"},
                            {"name": "Task Management", "color": "#3E7BFA"},
                            {"name": "Productivity", "color": "#3E7BFA"},
                            {"name": "Miscellaneous", "color": "#888888"}
                        ]
                    }
                }, f, indent=2)

    def load_data(self) -> Dict:
        """Load productivity data from the JSON file."""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"activities": [], "workblocks": [], "settings": {"categories": []}}

    def save_data(self, data: Dict) -> None:
        """Save productivity data to the JSON file."""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_activity(self, category: str, start_time: datetime, end_time: datetime, description: str = "") -> None:
        """Add a new activity to the tracker."""
        data = self.load_data()

        # Calculate duration in minutes
        duration = (end_time - start_time).total_seconds() / 60

        activity = {
            "id": len(data["activities"]) + 1,
            "category": category,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": duration,
            "description": description,
            "date": start_time.date().isoformat()
        }

        data["activities"].append(activity)
        self.save_data(data)

    def add_workblock(self, start_time: datetime, activity: str) -> None:
        """Add a new workblock to the tracker."""
        data = self.load_data()

        workblock = {
            "id": len(data["workblocks"]) + 1,
            "start_time": start_time.isoformat(),
            "activity": activity,
            "date": start_time.date().isoformat()
        }

        data["workblocks"].append(workblock)
        self.save_data(data)

    def get_daily_scores(self, date=None) -> Dict[str, Dict[str, Any]]:
        """Get the daily scores for focus, meetings, and breaks."""
        date = date or self.today
        date_str = date.isoformat() if isinstance(date, datetime) else date

        data = self.load_data()
        activities = [a for a in data["activities"] if a["date"] == date_str]

        # Calculate total minutes for the day
        total_minutes = sum(a["duration"] for a in activities)

        # Group by main categories
        categories = {
            "Focus": {"minutes": 0, "percentage": 0, "color": "#00E5B9"},
            "Meetings": {"minutes": 0, "percentage": 0, "color": "#9747FF"},
            "Breaks": {"minutes": 0, "percentage": 0, "color": "#3E7BFA"}
        }

        for activity in activities:
            category = activity["category"]
            if category in categories:
                categories[category]["minutes"] += activity["duration"]

        # Calculate percentages
        if total_minutes > 0:
            for category in categories:
                categories[category]["percentage"] = round((categories[category]["minutes"] / total_minutes) * 100)
                # Format time as hours and minutes
                hours, minutes = divmod(int(categories[category]["minutes"]), 60)
                categories[category]["formatted_time"] = f"{hours} hr {minutes} min"

        return categories

    def get_workblocks(self, date=None) -> List[Dict[str, Any]]:
        """Get the workblocks for a specific date."""
        date = date or self.today
        date_str = date.isoformat() if isinstance(date, datetime) else date

        data = self.load_data()
        workblocks = [w for w in data["workblocks"] if w["date"] == date_str]

        # Sort by start time
        workblocks.sort(key=lambda x: x["start_time"])

        # Format for display
        formatted_blocks = []
        for block in workblocks:
            start_time = datetime.fromisoformat(block["start_time"])
            formatted_blocks.append({
                "time": start_time.strftime("%H:%M"),
                "activity": block["activity"]
            })

        return formatted_blocks

    def get_time_breakdown(self, date=None) -> List[Dict[str, Any]]:
        """Get the time breakdown by activity category."""
        date = date or self.today
        date_str = date.isoformat() if isinstance(date, datetime) else date

        data = self.load_data()
        activities = [a for a in data["activities"] if a["date"] == date_str]

        # Group by all categories
        categories = {}
        for activity in activities:
            category = activity["category"]
            if category not in categories:
                # Find color from settings
                color = next((c["color"] for c in data["settings"]["categories"]
                             if c["name"] == category), "#888888")
                categories[category] = {
                    "minutes": 0,
                    "percentage": 0,
                    "color": color
                }
            categories[category]["minutes"] += activity["duration"]

        # Calculate total minutes
        total_minutes = sum(categories[c]["minutes"] for c in categories)

        # Calculate percentages and format time
        if total_minutes > 0:
            for category in categories:
                categories[category]["percentage"] = round((categories[category]["minutes"] / total_minutes) * 100)
                hours, minutes = divmod(int(categories[category]["minutes"]), 60)
                categories[category]["formatted_time"] = f"{hours} hr {minutes} min"

        # Convert to list and sort by percentage (descending)
        breakdown = [{"category": k, **v} for k, v in categories.items()]
        breakdown.sort(key=lambda x: x["percentage"], reverse=True)

        return breakdown

    def get_upcoming_meeting(self) -> Dict[str, Any]:
        """Get the next upcoming meeting."""
        now = datetime.now()
        data = self.load_data()

        # Filter activities for today and future that are meetings
        today_str = now.date().isoformat()
        upcoming_meetings = [
            a for a in data["activities"]
            if a["date"] >= today_str and
            a["category"] == "Meetings" and
            datetime.fromisoformat(a["start_time"]) > now
        ]

        # Sort by start time
        upcoming_meetings.sort(key=lambda x: x["start_time"])

        if upcoming_meetings:
            next_meeting = upcoming_meetings[0]
            start_time = datetime.fromisoformat(next_meeting["start_time"])
            minutes_until = int((start_time - now).total_seconds() / 60)

            return {
                "exists": True,
                "minutes_until": minutes_until,
                "description": next_meeting.get("description", "Upcoming meeting")
            }

        return {"exists": False}

    def generate_mock_data(self, date=None) -> None:
        """Generate mock productivity data for testing."""
        date = date or self.today
        if isinstance(date, str):
            date = datetime.fromisoformat(date).date()

        # Clear existing data for this date
        data = self.load_data()
        data["activities"] = [a for a in data["activities"] if a["date"] != date.isoformat()]
        data["workblocks"] = [w for w in data["workblocks"] if w["date"] != date.isoformat()]

        # Generate workblocks
        workblocks = [
            {"time": "09:00", "activity": "Daily Stand-Up"},
            {"time": "10:03", "activity": "Code"},
            {"time": "11:24", "activity": "Documentation"},
            {"time": "12:57", "activity": "Design"},
            {"time": "13:49", "activity": "Code"},
            {"time": "14:45", "activity": "Code"},
            {"time": "16:05", "activity": "Investor Meeting"},
            {"time": "17:10", "activity": "Documentation"}
        ]

        for block in workblocks:
            hour, minute = map(int, block["time"].split(":"))
            block_time = datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))
            self.add_workblock(block_time, block["activity"])

        # Generate activities with durations
        activities = [
            {"category": "Code", "duration": 166},  # 2 hr 46 min
            {"category": "Meetings", "duration": 85},  # 1 hr 25 min
            {"category": "Documentation", "duration": 75},  # 1 hr 15 min
            {"category": "Design", "duration": 45},  # 45 min
            {"category": "Messaging", "duration": 23},  # 23 min
            {"category": "Email", "duration": 20},  # 20 min
            {"category": "Task Management", "duration": 11},  # 11 min
            {"category": "Productivity", "duration": 10},  # 10 min
            {"category": "Miscellaneous", "duration": 4}  # 4 min
        ]

        # Calculate main category totals
        focus_time = activities[0]["duration"] + activities[2]["duration"] + activities[3]["duration"]  # Code + Documentation + Design
        meeting_time = activities[1]["duration"]  # Meetings
        break_time = activities[4]["duration"] + activities[5]["duration"] + activities[6]["duration"] + activities[7]["duration"] + activities[8]["duration"]  # Everything else

        # Add main category activities
        start_time = datetime.combine(date, datetime.min.time().replace(hour=9))

        self.add_activity("Focus", start_time, start_time + timedelta(minutes=focus_time))
        self.add_activity("Meetings", start_time, start_time + timedelta(minutes=meeting_time))
        self.add_activity("Breaks", start_time, start_time + timedelta(minutes=break_time))

        # Add detailed activities
        current_time = start_time
        for activity in activities:
            end_time = current_time + timedelta(minutes=activity["duration"])
            self.add_activity(activity["category"], current_time, end_time)
            current_time = end_time

        # Add upcoming meeting in 54 minutes from now
        now = datetime.now()
        meeting_time = now + timedelta(minutes=54)
        self.add_activity("Meetings", meeting_time, meeting_time + timedelta(minutes=30), "Team Sync")

        print(f"Generated mock data for {date.isoformat()}")

def get_productivity_data():
    """Get all productivity data for the dashboard."""
    tracker = ProductivityTracker()

    # For demo purposes, generate mock data if no data exists
    if not tracker.get_workblocks():
        tracker.generate_mock_data()

    return {
        "scores": tracker.get_daily_scores(),
        "workblocks": tracker.get_workblocks(),
        "time_breakdown": tracker.get_time_breakdown(),
        "upcoming_meeting": tracker.get_upcoming_meeting()
    }