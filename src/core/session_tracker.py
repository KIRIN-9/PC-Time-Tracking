from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class WorkSession:
    start_time: datetime
    end_time: Optional[datetime] = None
    is_break: bool = False
    duration: Optional[timedelta] = None

class SessionTracker:
    def __init__(self, break_threshold_minutes: int = 40):
        self.break_threshold = timedelta(minutes=break_threshold_minutes)
        self.current_session: Optional[WorkSession] = None
        self.sessions: List[WorkSession] = []
        self.total_work_time = timedelta()
        self.total_break_time = timedelta()

    def start_session(self):
        """Start a new work session"""
        if not self.current_session:
            self.current_session = WorkSession(start_time=datetime.now())

    def end_session(self):
        """End the current session"""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self.current_session.duration = (
                self.current_session.end_time - self.current_session.start_time
            )

            if self.current_session.is_break:
                self.total_break_time += self.current_session.duration
            else:
                self.total_work_time += self.current_session.duration

            self.sessions.append(self.current_session)
            self.current_session = None

    def start_break(self):
        """Start a break session"""
        self.end_session()  # End current work session if any
        self.current_session = WorkSession(
            start_time=datetime.now(),
            is_break=True
        )

    def get_current_session_duration(self) -> timedelta:
        """Get duration of current session"""
        if not self.current_session:
            return timedelta()
        return datetime.now() - self.current_session.start_time

    def get_session_stats(self) -> Dict:
        """Get statistics about work/break sessions"""
        current_duration = self.get_current_session_duration()

        if self.current_session and not self.current_session.is_break:
            total_work = self.total_work_time + current_duration
            total_break = self.total_break_time
        elif self.current_session and self.current_session.is_break:
            total_work = self.total_work_time
            total_break = self.total_break_time + current_duration
        else:
            total_work = self.total_work_time
            total_break = self.total_break_time

        return {
            "total_work_time": total_work,
            "total_break_time": total_break,
            "session_count": len(self.sessions),
            "current_session": "break" if self.current_session and self.current_session.is_break else "work" if self.current_session else None,
            "current_duration": current_duration
        }

    def should_take_break(self) -> bool:
        """Check if it's time to take a break"""
        if not self.current_session or self.current_session.is_break:
            return False
        return self.get_current_session_duration() >= self.break_threshold