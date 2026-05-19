"""Tests for learning state tracking and spaced repetition."""

import os
import json
from lexi.learned import LearnedDB, WordState, DEFAULT_DB_PATH


def test_import_words(temp_dir):
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    db.import_words(["dog", "cat", "run"])
    assert len(db.words) == 3
    assert db.words["dog"].status == "new"
    assert db.words["dog"].first_seen != ""


def test_import_duplicates(temp_dir):
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    db.import_words(["dog"])
    db.import_words(["dog", "cat"])
    assert len(db.words) == 2  # dog not duplicated


def test_mark_reviewed_good(temp_dir):
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    db.import_words(["dog"])
    db.mark_reviewed("dog", "good")
    ws = db.words["dog"]
    assert ws.status == "learning"
    assert ws.review_count == 1
    assert ws.interval == 1
    assert ws.next_review != ""


def test_mark_reviewed_again(temp_dir):
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    db.import_words(["dog"])
    db.mark_reviewed("dog", "good")
    db.mark_reviewed("dog", "again")
    ws = db.words["dog"]
    assert ws.interval == 1
    assert ws.ease < 2.5


def test_mark_reviewed_easy(temp_dir):
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    db.import_words(["dog"])
    db.mark_reviewed("dog", "easy")
    ws = db.words["dog"]
    assert ws.interval == 4
    assert ws.ease > 2.5


def test_mastered_threshold(temp_dir):
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    db.import_words(["dog"])
    ws = db.words["dog"]
    ws.interval = 21
    ws.ease = 2.5
    db.mark_reviewed("dog", "good")
    assert ws.status == "mastered"


def test_get_due(temp_dir):
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    db.import_words(["dog", "cat", "run", "walk"])
    # All new = all due
    due = db.get_due()
    assert len(due) == 4


def test_get_stats(temp_dir):
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    db.import_words(["a", "b", "c"])
    stats = db.get_stats()
    assert stats["total"] == 3
    assert stats["new"] == 3


def test_persistence(temp_dir):
    path = os.path.join(temp_dir, "learned.json")
    db1 = LearnedDB(path)
    db1.import_words(["dog"])
    db1.mark_reviewed("dog", "good")

    db2 = LearnedDB(path)
    ws = db2.words["dog"]
    assert ws.status == "learning"
    assert ws.review_count == 1


def test_empty_db(temp_dir):
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    assert db.get_due() == []
    assert db.get_stats()["total"] == 0


def test_interval_growth(temp_dir):
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    db.import_words(["dog"])
    for _ in range(5):
        db.mark_reviewed("dog", "good")
    ws = db.words["dog"]
    assert ws.interval >= 3  # Should grow
