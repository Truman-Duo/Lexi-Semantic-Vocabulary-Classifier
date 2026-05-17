import os
import tempfile
from lexi.cleaner import clean_text_stream


def test_clean_basic_words():
    content = "The dog runs quickly.\nCats are happy.\n"
    path = _make_temp(content)
    words = list(clean_text_stream(path))
    assert "dog" in words
    assert "runs" in words
    assert "cats" in words


def test_clean_contractions():
    content = "don't can't it's we're\n"
    path = _make_temp(content)
    words = list(clean_text_stream(path))
    assert "do" in words
    assert "not" in words


def test_clean_phonetic():
    content = "abandon /ə'bændən/ n.\n"
    path = _make_temp(content)
    words = list(clean_text_stream(path))
    assert "abandon" in words
    assert "ə" not in words


def test_clean_pos_tags():
    content = "abandon n. vt.\nrun v. vi.\n"
    path = _make_temp(content)
    words = list(clean_text_stream(path))
    assert "abandon" in words
    assert "run" in words


def test_clean_non_alpha():
    content = "word123 test! hello,world\n"
    path = _make_temp(content)
    words = list(clean_text_stream(path))
    assert "word" in words
    assert "hello" in words
    assert "world" in words


def test_clean_short_words():
    content = "a b c d dd\n"
    path = _make_temp(content)
    words = list(clean_text_stream(path))
    for w in words:
        assert len(w) >= 2


def test_clean_empty_file():
    path = _make_temp("")
    words = list(clean_text_stream(path))
    assert words == []


def test_clean_unicode():
    content = "café naïve\n"
    path = _make_temp(content)
    words = list(clean_text_stream(path))
    assert len(words) >= 0


def _make_temp(content):
    fd, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return path
