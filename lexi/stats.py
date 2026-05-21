"""Learning duration tracking. Persisted to ~/.lexi/stats.json."""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


DEFAULT_STATS_PATH = os.path.expanduser("~/.lexi/stats.json")
MAX_GAP_SEC = 300  # Max seconds attributed to a single action


@dataclass
class LearningStats:
    total_seconds: int = 0
    session_start: Optional[str] = None


class StatsTracker:
    def __init__(self, path: str = DEFAULT_STATS_PATH):
        self.path = path
        self.data = LearningStats()
        self._last_action: Optional[datetime] = None
        self._dirty_seconds = 0
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                import json
                with open(self.path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                self.data = LearningStats(total_seconds=d.get("total_seconds", 0))
            except Exception:
                pass

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        import json
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"total_seconds": self.data.total_seconds}, f)

    def start_session(self):
        self._last_action = datetime.now()

    def record_action(self):
        now = datetime.now()
        if self._last_action:
            elapsed = min(int((now - self._last_action).total_seconds()), MAX_GAP_SEC)
            self.data.total_seconds += elapsed
            self._dirty_seconds += elapsed
        self._last_action = now
        if self._dirty_seconds >= 60:
            self._dirty_seconds = 0
            self.save()

    @property
    def hours(self) -> int:
        return self.data.total_seconds // 3600

    @property
    def minutes(self) -> int:
        return (self.data.total_seconds % 3600) // 60

    @property
    def display(self) -> str:
        h, m = self.hours, self.minutes
        if h > 0:
            return f"{h} 小时 {m} 分钟"
        return f"{m} 分钟"
