from lexi.story import (
    StoryGenerator, StoryResult, _verify_word_usage,
    _load_word_infos_from_json, _save_story_markdown,
)
from lexi.config import LexiConfig
import os
import tempfile


def make_config():
    return LexiConfig(api_key="sk-test", model="gpt-4o-mini")


def test_build_prompt_includes_words():
    gen = StoryGenerator(make_config())
    sys_msg, user_msg = gen._build_prompt(["dog", "cat", "run"])
    assert "dog" in user_msg
    assert "cat" in user_msg
    assert "run" in user_msg


def test_build_prompt_with_cefr(sample_classified_json):
    gen = StoryGenerator(make_config())
    word_infos = _load_word_infos_from_json(sample_classified_json)
    _, user_msg = gen._build_prompt(["dog", "run"], word_infos)
    assert "B1" in user_msg
    assert "A2" in user_msg


def test_build_prompt_zh():
    gen = StoryGenerator(make_config())
    sys_msg, user_msg = gen._build_prompt(["dog"], language="zh")
    assert "语言学习" in sys_msg
    assert "加粗" in user_msg


def test_build_prompt_with_style():
    gen = StoryGenerator(make_config())
    sys_msg, _ = gen._build_prompt(["dog"], style_text="Reference passage here.")
    assert "Reference passage here" in sys_msg
    assert "Mimic" in sys_msg


def test_generate_story_empty_words():
    gen = StoryGenerator(make_config())
    import pytest
    with pytest.raises(ValueError):
        gen.generate_story([])


def test_generate_story_too_many_words():
    gen = StoryGenerator(make_config())
    import pytest
    words = [f"word{i}" for i in range(51)]
    with pytest.raises(ValueError):
        gen.generate_story(words)


def test_select_words_balanced(sample_classified_json):
    gen = StoryGenerator(make_config())
    word_infos = _load_word_infos_from_json(sample_classified_json)
    selected = gen.select_words(word_infos, count=4, strategy="balanced")
    assert len(selected) == 4
    assert all(w in word_infos for w in selected)


def test_select_words_top_frequency(sample_classified_json):
    gen = StoryGenerator(make_config())
    word_infos = _load_word_infos_from_json(sample_classified_json)
    selected = gen.select_words(word_infos, count=3, strategy="top_frequency")
    assert len(selected) == 3
    assert selected[0] == "run"


def test_select_words_random(sample_classified_json):
    gen = StoryGenerator(make_config())
    word_infos = _load_word_infos_from_json(sample_classified_json)
    selected = gen.select_words(word_infos, count=3, strategy="random")
    assert len(selected) == 3


def test_select_words_stratified(sample_classified_json):
    gen = StoryGenerator(make_config())
    word_infos = _load_word_infos_from_json(sample_classified_json)
    selected = gen.select_words(word_infos, count=4, strategy="stratified")
    assert len(selected) == 4


def test_select_words_empty(sample_classified_json):
    gen = StoryGenerator(make_config())
    word_infos = _load_word_infos_from_json(sample_classified_json)
    selected = gen.select_words(word_infos, count=0, strategy="balanced")
    assert selected == []


def test_select_words_with_exclude(sample_classified_json):
    gen = StoryGenerator(make_config())
    word_infos = _load_word_infos_from_json(sample_classified_json)
    selected = gen.select_words(word_infos, count=3, strategy="top_frequency", exclude=["run"])
    assert "run" not in selected


def test_verify_word_usage_all_used():
    passage = "The **dog** and **cat** run in the house."
    used, missed = _verify_word_usage(passage, ["dog", "cat", "run"])
    assert sorted(used) == sorted(["dog", "cat", "run"])
    assert missed == []


def test_verify_word_usage_some_missed():
    passage = "The **dog** runs in the house."
    used, missed = _verify_word_usage(passage, ["dog", "cat"])
    assert used == ["dog"]
    assert missed == ["cat"]


def test_verify_word_usage_underscore():
    passage = "The ad hoc committee met yesterday."
    used, missed = _verify_word_usage(passage, ["ad_hoc"])
    assert "ad_hoc" in used


def test_load_word_infos_from_json(sample_classified_json):
    word_infos = _load_word_infos_from_json(sample_classified_json)
    assert "dog" in word_infos
    assert word_infos["dog"].zipf_frequency == 3.8
    assert word_infos["dog"].cefr_level == "B1"


def test_save_story_markdown(sample_classified_json):
    result = StoryResult(
        passage="The **dog** runs.",
        words_used=["dog"],
        words_missed=["cat"],
        word_count=3,
        model="gpt-4o-mini",
    )
    word_infos = _load_word_infos_from_json(sample_classified_json)
    fd, path = tempfile.mkstemp(suffix=".md")
    os.close(fd)
    _save_story_markdown(result, path, word_infos)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "dog" in content
    assert "cat" in content
    assert "✓" in content
    assert "未使用" in content
    os.unlink(path)
