"""Tests for phased learning plans."""

import os
from lexi.planner import PlanGenerator, LearningPlan, DailyPlan
from lexi.learned import LearnedDB


def _make_word_infos():
    from lexi.models import WordInfo, ClassificationResult
    return {
        "dog": WordInfo(word="dog", zipf_frequency=3.8, cefr_level="A1",
                        classifications=[ClassificationResult("客观类", "具体事物")]),
        "cat": WordInfo(word="cat", zipf_frequency=3.5, cefr_level="A1",
                        classifications=[ClassificationResult("客观类", "具体事物")]),
        "analyze": WordInfo(word="analyze", zipf_frequency=4.2, cefr_level="B2",
                            classifications=[ClassificationResult("主观类", "心理活动")]),
        "paradigm": WordInfo(word="paradigm", zipf_frequency=2.8, cefr_level="C1",
                             classifications=[ClassificationResult("抽象类", "基础概念")]),
    }


def test_create_plan(temp_dir):
    pg = PlanGenerator(os.path.join(temp_dir, "plan.json"))
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    word_infos = _make_word_infos()
    plan = pg.create_plan(word_infos, db, target_cefr="B2", daily_count=2)
    assert plan.target_cefr == "B2"
    assert plan.daily_count == 2
    assert len(plan.days) >= 1
    assert len(plan.days[0].words) <= 2


def test_create_plan_fallback(temp_dir):
    pg = PlanGenerator(os.path.join(temp_dir, "plan.json"))
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    word_infos = _make_word_infos()
    plan = pg.create_plan(word_infos, db, target_cefr="C2", daily_count=10)
    assert len(plan.days) >= 1


def test_get_today(temp_dir):
    pg = PlanGenerator(os.path.join(temp_dir, "plan.json"))
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    pg.create_plan(_make_word_infos(), db, target_cefr="A1", daily_count=2)
    today = pg.get_today()
    assert today is not None
    assert len(today.words) >= 1


def test_mark_completed(temp_dir):
    pg = PlanGenerator(os.path.join(temp_dir, "plan.json"))
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    pg.create_plan(_make_word_infos(), db, target_cefr="A1", daily_count=2)
    day = pg.plan.days[0]
    pg.mark_completed(day.date)
    assert pg.plan.days[0].completed


def test_get_progress(temp_dir):
    pg = PlanGenerator(os.path.join(temp_dir, "plan.json"))
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    pg.create_plan(_make_word_infos(), db, target_cefr="A1", daily_count=1)
    p = pg.get_progress()
    assert p["total_days"] > 1
    assert p["completed_days"] == 0


def test_persistence(temp_dir):
    path = os.path.join(temp_dir, "plan.json")
    pg1 = PlanGenerator(path)
    db = LearnedDB(os.path.join(temp_dir, "learned.json"))
    pg1.create_plan(_make_word_infos(), db, target_cefr="A1", daily_count=2)
    pg2 = PlanGenerator(path)
    assert pg2.plan.target_cefr == "A1"


def test_empty_plan(temp_dir):
    pg = PlanGenerator(os.path.join(temp_dir, "plan.json"))
    assert pg.get_today() is None
    assert pg.get_progress()["total_days"] == 0
