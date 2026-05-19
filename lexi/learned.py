"""Learning state tracking with spaced repetition (Anki SM-2 algorithm)."""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple


DEFAULT_DB_PATH = os.path.expanduser("~/.lexi/learned.json")

RATINGS = {"again": 0, "hard": 1, "good": 2, "easy": 3}


@dataclass
class WordState:
    word: str
    status: str = "new"
    first_seen: str = ""
    last_reviewed: str = ""
    review_count: int = 0
    next_review: str = ""
    ease: float = 2.5
    interval: int = 0


class LearnedDB:
    """Persistent word learning state with SM-2 spaced repetition."""

    def __init__(self, path: Optional[str] = None):
        self.path = path or DEFAULT_DB_PATH
        self.words: Dict[str, WordState] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for w, d in data.get("words", {}).items():
                    self.words[w] = WordState(**d)
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        words_data = {w: asdict(ws) for w, ws in self.words.items()}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"words": words_data, "stats": self.get_stats()},
                      f, ensure_ascii=False, indent=2)

    def import_words(self, words: List[str]):
        """Add new words that aren't already tracked."""
        today = date.today().isoformat()
        for w in words:
            if w not in self.words:
                self.words[w] = WordState(
                    word=w, status="new", first_seen=today,
                )
        self.save()

    def mark_reviewed(self, word: str, rating: str):
        """Update word state after review. rating: again/hard/good/easy."""
        if word not in self.words:
            return
        ws = self.words[word]
        today = date.today()
        today_str = today.isoformat()

        ws.last_reviewed = today_str
        ws.review_count += 1

        if ws.status == "new":
            ws.status = "learning"

        if rating == "again":
            ws.interval = 1
            ws.ease = max(1.3, ws.ease - 0.2)
        elif rating == "hard":
            ws.interval = max(1, int(ws.interval * 1.2))
            ws.ease = max(1.3, ws.ease - 0.15)
        elif rating == "good":
            if ws.interval == 0:
                ws.interval = 1
            else:
                ws.interval = max(1, int(ws.interval * ws.ease))
        elif rating == "easy":
            if ws.interval == 0:
                ws.interval = 4
            else:
                ws.interval = max(1, int(ws.interval * ws.ease * 1.3))
            ws.ease += 0.15

        ws.next_review = (today + timedelta(days=ws.interval)).isoformat()

        if ws.interval >= 21 and ws.ease >= 2.0:
            ws.status = "mastered"

        self.save()

    def get_due(self, limit: int = 50) -> List[WordState]:
        """Return words due for review today."""
        today = date.today().isoformat()
        due = []
        for ws in self.words.values():
            if ws.status == "new":
                due.append(ws)
            elif ws.next_review and ws.next_review <= today:
                due.append(ws)
        due.sort(key=lambda ws: (0 if ws.status == "new" else 1, ws.next_review))
        return due[:limit]

    def get_all(self, status: Optional[str] = None) -> List[WordState]:
        """Return all words, optionally filtered by status."""
        words = list(self.words.values())
        if status:
            words = [w for w in words if w.status == status]
        words.sort(key=lambda w: w.word)
        return words

    def get_stats(self) -> dict:
        """Return learning statistics."""
        total = len(self.words)
        if total == 0:
            return {"total": 0, "mastered": 0, "learning": 0, "new": 0, "due_today": 0}
        counts = {"new": 0, "learning": 0, "mastered": 0}
        for ws in self.words.values():
            counts[ws.status] = counts.get(ws.status, 0) + 1
        return {
            "total": total,
            "mastered": counts.get("mastered", 0),
            "learning": counts.get("learning", 0),
            "new": counts.get("new", 0),
            "due_today": len(self.get_due()),
        }
