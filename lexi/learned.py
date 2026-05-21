"""Learning state tracking with spaced repetition (Anki SM-2)."""

import csv
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional


DEFAULT_DB_PATH = os.path.expanduser("~/.lexi/learned.json")
RATINGS = {"again": 0, "hard": 1, "good": 2, "easy": 3}


@dataclass
class ReviewEvent:
    timestamp: str = ""           # ISO 8601
    rating: str = ""              # "认识"/"模糊"/"不认识"
    response_time_ms: int = 0
    card_type: int = 1            # 1=self-assessment, 2=word→meaning, 3=meaning→word


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
    review_log: List[dict] = field(default_factory=list)
    posterior_alpha: float = 1.0
    posterior_beta: float = 1.0
    chinese_meaning: str = ""

    @property
    def p_know(self) -> float:
        denom = self.posterior_alpha + self.posterior_beta
        return self.posterior_alpha / denom if denom > 0 else 0.5


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
                    self.words[w] = WordState(
                        word=w, status=d.get("status", "new"),
                        first_seen=d.get("first_seen", ""),
                        last_reviewed=d.get("last_reviewed", ""),
                        review_count=d.get("review_count", 0),
                        next_review=d.get("next_review", ""),
                        ease=d.get("ease", 2.5),
                        interval=d.get("interval", 0),
                        review_log=d.get("review_log", []),
                        posterior_alpha=d.get("posterior_alpha", 1.0),
                        posterior_beta=d.get("posterior_beta", 1.0),
                        chinese_meaning=d.get("chinese_meaning", ""),
                    )
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        words_data = {}
        for w, ws in self.words.items():
            d = asdict(ws)
            del d["word"]
            words_data[w] = d
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"words": words_data, "stats": self.get_stats()},
                      f, ensure_ascii=False, indent=2)

    def import_words(self, words: List[str]):
        today = date.today().isoformat()
        for w in words:
            if w not in self.words:
                self.words[w] = WordState(word=w, status="new", first_seen=today)
        self.save()

    def log_review(self, word: str, rating: str, response_time_ms: int = 0, card_type: int = 1):
        """Record a review event. Does NOT save (caller batches with mark_reviewed)."""
        if word not in self.words:
            return
        ws = self.words[word]
        ts = datetime.now().isoformat()
        event = ReviewEvent(timestamp=ts, rating=rating, response_time_ms=response_time_ms, card_type=card_type)
        ws.review_log.append(asdict(event))
        if len(ws.review_log) > 500:
            ws.review_log = ws.review_log[-100:]

    def mark_reviewed(self, word: str, rating: str):
        """Update word state after review. rating: again/hard/good/easy."""
        if word not in self.words:
            return
        ws = self.words[word]
        t = date.today()
        ts = t.isoformat()
        ws.last_reviewed = ts
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
        ws.next_review = (t + timedelta(days=ws.interval)).isoformat()
        if ws.interval >= 21 and ws.ease >= 2.0:
            ws.status = "mastered"
        self.save()

    def get_due(self, limit: int = 50) -> List[WordState]:
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
        words = list(self.words.values())
        if status:
            words = [w for w in words if w.status == status]
        words.sort(key=lambda w: w.word)
        return words

    def get_stats(self) -> dict:
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

    def export_csv(self, path: str):
        """Export all words to CSV."""
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["word", "status", "interval", "ease", "review_count",
                             "first_seen", "last_reviewed", "next_review",
                             "posterior_alpha", "posterior_beta", "p_know", "chinese_meaning"])
            for ws in self.words.values():
                writer.writerow([ws.word, ws.status, ws.interval, ws.ease,
                                ws.review_count, ws.first_seen, ws.last_reviewed, ws.next_review,
                                round(ws.posterior_alpha, 3), round(ws.posterior_beta, 3),
                                round(ws.p_know, 3), ws.chinese_meaning])

    def generate_meanings(self, config=None, batch_size=20):
        """Generate Chinese meanings for words without one, using AI API."""
        words_needed = [w for w, ws in self.words.items() if not ws.chinese_meaning]
        if not words_needed:
            return 0
        if not config or not config.api_key:
            return 0
        try:
            from openai import OpenAI
            client = OpenAI(api_key=config.api_key, base_url=config.api_base_url)
            generated = 0
            for i in range(0, len(words_needed), batch_size):
                batch = words_needed[i:i + batch_size]
                prompt = (
                    f"For each English word below, output its most common Chinese translation.\n"
                    f"Format: 'word: Chinese'\n\n" + "\n".join(batch)
                )
                resp = client.chat.completions.create(
                    model=config.model,
                    messages=[{"role":"user","content":prompt}],
                    temperature=0.3, max_tokens=500)
                text = resp.choices[0].message.content or ""
                for line in text.strip().split("\n"):
                    if ":" in line:
                        parts = line.split(":", 1)
                        w = parts[0].strip().lower()
                        meaning = parts[1].strip()
                        if w in self.words and not self.words[w].chinese_meaning:
                            self.words[w].chinese_meaning = meaning
                            generated += 1
            if generated:
                self.save()
            return generated
        except Exception:
            return 0
