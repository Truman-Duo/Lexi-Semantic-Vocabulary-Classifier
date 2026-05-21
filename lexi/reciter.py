"""ReciterEngine — word selection strategies with Beta posterior + data cleaning."""

import random
import time as _time
from typing import List, Optional

from .learned import LearnedDB, WordState

TIMEOUT_SEC = 30
GAP_THRESHOLD_SEC = 120
RT_CAP_MULTIPLIER = 3.0
EPSILON_EXPLORE = 0.15
BETA_PRIOR_ALPHA = 1.0
BETA_PRIOR_BETA = 1.0
MAX_GAP_SEC = 300  # Record at most 5min per action for learning duration


class ReciterEngine:
    def __init__(self, learned_db: LearnedDB):
        self.db = learned_db
        self.session_events: List[dict] = []

    def select_words(self, count: int, strategy: str, word_pool: Optional[List[str]] = None) -> List[WordState]:
        if word_pool:
            filtered = [ws for ws in self.db.get_all() if ws.word in word_pool]
            if strategy == "复习优先":
                return self._filter_strategy(filtered, count, self._review_first)
            elif strategy == "新词优先":
                return self._filter_strategy(filtered, count, self._new_first)
            elif strategy == "混合出词":
                return self._filter_strategy(filtered, count, self._mixed)
            elif strategy == "智能出词":
                return self._filter_strategy(filtered, count, self._smart)
            return filtered[:count]
        if strategy == "复习优先":
            return self._review_first(count)
        elif strategy == "新词优先":
            return self._new_first(count)
        elif strategy == "混合出词":
            return self._mixed(count)
        elif strategy == "智能出词":
            return self._smart(count)
        return self._review_first(count)

    def _filter_strategy(self, candidates, count, strategy_fn):
        if not candidates:
            return []
        return strategy_fn(count)[:count]

    def _review_first(self, count: int) -> List[WordState]:
        result = self.db.get_due(limit=count)
        if len(result) < count:
            new_words = [ws for ws in self.db.get_all("new") if ws not in result]
            result += new_words[:count - len(result)]
        return result

    def _new_first(self, count: int) -> List[WordState]:
        result = self.db.get_all("new")
        if len(result) < count:
            due = [ws for ws in self.db.get_due(limit=count) if ws not in result]
            result += due[:count - len(result)]
        return result[:count]

    def _mixed(self, count: int) -> List[WordState]:
        all_words = self.db.get_all()
        new_words = [w for w in all_words if w.status == "new"]
        reviewed_words = [w for w in all_words if w.status != "new"]
        new_n = int(count * len(new_words) / max(1, len(all_words)))
        due_n = count - new_n
        result = random.sample(new_words, min(new_n, len(new_words)))
        result += random.sample(reviewed_words, min(due_n, len(reviewed_words)))
        random.shuffle(result)
        return result

    def _smart(self, count: int) -> List[WordState]:
        candidates = self.db.get_all()
        explore_n = max(1, int(count * EPSILON_EXPLORE))
        exploit_n = count - explore_n
        scored = sorted(candidates, key=lambda ws: self.compute_need_score(ws), reverse=True)
        exploit = scored[:exploit_n]
        remaining = [ws for ws in candidates if ws not in exploit]
        explore = random.sample(remaining, min(explore_n, len(remaining)))
        return exploit + explore

    def compute_need_score(self, ws: WordState) -> float:
        p = ws.p_know
        urgency = 1.0 if ws.status == "new" else max(0.1, 1.0 - ws.review_count * 0.2)
        return (1.0 - p) * urgency

    def log_and_update(self, word: str, rating: str, response_time_ms: int):
        if response_time_ms / 1000.0 > TIMEOUT_SEC:
            return
        ts_now = _time.time() * 1000
        if self.session_events:
            last_ev = self.session_events[-1]
            last_ts = last_ev.get("_ts", ts_now)
            # gap detected but event still recorded
        event = {"word": word, "rating": rating, "rt_ms": response_time_ms, "_ts": ts_now}
        self.session_events.append(event)
        sm2_rating = {"认识": "easy", "模糊": "hard", "不认识": "again"}.get(rating, "good")
        self.db.log_review(word, rating, response_time_ms)
        self.db.mark_reviewed(word, sm2_rating)
        self.db.save()  # single save after both operations
        ws = self.db.words.get(word)
        if ws:
            cw = self._confidence_weight(response_time_ms)
            if rating == "认识":
                ws.posterior_alpha += cw
            elif rating == "不认识":
                ws.posterior_beta += cw
            elif rating == "模糊":
                ws.posterior_alpha += cw * 0.3
                ws.posterior_beta += cw * 0.7

    def _confidence_weight(self, rt_ms: int) -> float:
        rt_sec = rt_ms / 1000.0
        avg_rt = self._session_avg_rt()
        capped = min(rt_sec, avg_rt * RT_CAP_MULTIPLIER) if avg_rt > 0 else rt_sec
        return 1.0 / (1.0 + capped / 3.0)

    def _session_avg_rt(self) -> float:
        if not self.session_events:
            return 3.0
        total = sum(e["rt_ms"] for e in self.session_events)
        return total / (len(self.session_events) * 1000.0)

    def session_stats(self) -> dict:
        if not self.session_events:
            return {"total": 0, "认识": 0, "模糊": 0, "不认识": 0, "avg_rt_ms": 0}
        counts = {"认识": 0, "模糊": 0, "不认识": 0}
        for e in self.session_events:
            counts[e["rating"]] = counts.get(e["rating"], 0) + 1
        total_rt = sum(e["rt_ms"] for e in self.session_events)
        return {
            "total": len(self.session_events),
            "认识": counts["认识"],
            "模糊": counts["模糊"],
            "不认识": counts["不认识"],
            "avg_rt_ms": int(total_rt / len(self.session_events)),
        }
