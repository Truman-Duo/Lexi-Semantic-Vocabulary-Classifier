"""Phased learning plans — CEFR-targeted daily vocabulary schedules."""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta
from typing import Dict, List, Optional


DEFAULT_PLAN_PATH = os.path.expanduser("~/.lexi/plan.json")
CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]


@dataclass
class DailyPlan:
    date: str = ""
    words: List[str] = field(default_factory=list)
    completed: bool = False
    story_generated: bool = False


@dataclass
class LearningPlan:
    target_cefr: str = ""
    daily_count: int = 20
    start_date: str = ""
    days: List[DailyPlan] = field(default_factory=list)


class PlanGenerator:
    def __init__(self, path: Optional[str] = None):
        self.path = path or DEFAULT_PLAN_PATH
        self.plan = LearningPlan()
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.plan = LearningPlan(
                    target_cefr=data.get("target_cefr", ""),
                    daily_count=data.get("daily_count", 20),
                    start_date=data.get("start_date", ""),
                    days=[DailyPlan(**d) for d in data.get("days", [])],
                )
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.plan), f, ensure_ascii=False, indent=2)

    def create_plan(
        self, word_infos: Dict, learned_db, target_cefr: str, daily_count: int = 20,
    ) -> LearningPlan:
        """Auto-select words at target CEFR level, distribute across days."""
        target_idx = CEFR_ORDER.index(target_cefr) if target_cefr in CEFR_ORDER else 2
        candidates = {}
        for w, wi in word_infos.items():
            cefr = wi.cefr_level
            if cefr in CEFR_ORDER and CEFR_ORDER.index(cefr) >= target_idx:
                if w in learned_db.words and learned_db.words[w].status == "mastered":
                    continue
                candidates[w] = wi

        if not candidates:
            candidates = {w: wi for w, wi in word_infos.items()
                         if w not in learned_db.words or learned_db.words[w].status != "mastered"}

        sorted_words = sorted(candidates.keys(),
                             key=lambda w: candidates[w].zipf_frequency, reverse=True)

        today = date.today()
        days = []
        for i in range(0, len(sorted_words), daily_count):
            chunk = sorted_words[i:i + daily_count]
            day_date = (today + timedelta(days=len(days))).isoformat()
            days.append(DailyPlan(date=day_date, words=chunk))

        self.plan = LearningPlan(
            target_cefr=target_cefr,
            daily_count=daily_count,
            start_date=today.isoformat(),
            days=days,
        )
        self.save()
        return self.plan

    def get_today(self) -> Optional[DailyPlan]:
        today_str = date.today().isoformat()
        for d in self.plan.days:
            if d.date == today_str:
                return d
        for d in self.plan.days:
            if d.date >= today_str and not d.completed:
                return d
        return None

    def mark_completed(self, day_date: str):
        for d in self.plan.days:
            if d.date == day_date:
                d.completed = True
                self.save()
                return

    def get_progress(self) -> dict:
        days = self.plan.days
        if not days:
            return {"total_days": 0, "completed_days": 0, "total_words": 0, "completed_words": 0, "pct": 0}
        completed_days = sum(1 for d in days if d.completed)
        total_words = sum(len(d.words) for d in days)
        completed_words = sum(len(d.words) for d in days if d.completed)
        return {
            "total_days": len(days),
            "completed_days": completed_days,
            "total_words": total_words,
            "completed_words": completed_words,
            "pct": round(completed_days / len(days) * 100) if days else 0,
        }
