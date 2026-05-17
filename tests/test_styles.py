import os
from lexi.styles import StyleManager, Style


def test_list_empty(temp_dir):
    mgr = StyleManager(os.path.join(temp_dir, "styles"))
    assert mgr.list_styles() == []


def test_add_and_list(temp_dir):
    mgr = StyleManager(os.path.join(temp_dir, "styles"))
    mgr.add_style("test1", "The cat sat on the mat. The dog ran fast.", "Test desc", "Test source")
    styles = mgr.list_styles()
    assert len(styles) == 1
    assert styles[0].name == "test1"
    assert "The cat sat" in styles[0].body
    assert styles[0].profile.avg_word_length > 0


def test_get_style(temp_dir):
    mgr = StyleManager(os.path.join(temp_dir, "styles"))
    mgr.add_style("mystyle", "Body text", "A description", "A source")
    s = mgr.get_style("mystyle")
    assert s.name == "mystyle"
    assert s.description == "A description"
    assert s.source == "A source"
    assert s.body == "Body text"


def test_delete_style(temp_dir):
    mgr = StyleManager(os.path.join(temp_dir, "styles"))
    mgr.add_style("temp", "body")
    assert len(mgr.list_styles()) == 1
    mgr.delete_style("temp")
    assert len(mgr.list_styles()) == 0


def test_add_overwrite(temp_dir):
    mgr = StyleManager(os.path.join(temp_dir, "styles"))
    mgr.add_style("dup", "body1")
    mgr.add_style("dup", "body2")
    s = mgr.get_style("dup")
    assert s.body == "body2"


def test_delete_nonexistent(temp_dir):
    mgr = StyleManager(os.path.join(temp_dir, "styles"))
    import pytest
    with pytest.raises(FileNotFoundError):
        mgr.delete_style("nonexistent")


def test_custom_directory(temp_dir):
    custom = os.path.join(temp_dir, "custom_styles")
    mgr = StyleManager(custom)
    mgr.add_style("s", "body")
    assert os.path.isdir(custom)
    assert os.path.exists(os.path.join(custom, "s.md"))


def test_persists_to_disk(temp_dir):
    mgr = StyleManager(os.path.join(temp_dir, "styles"))
    mgr.add_style("persist", "persistent body", "desc", "src")
    mgr2 = StyleManager(os.path.join(temp_dir, "styles"))
    s = mgr2.get_style("persist")
    assert s.body == "persistent body"
    assert s.description == "desc"
    assert s.source == "src"


def test_file_format(temp_dir):
    mgr = StyleManager(os.path.join(temp_dir, "styles"))
    mgr.add_style("fmt", "the body text", "my desc", "my source")
    path = os.path.join(temp_dir, "styles", "fmt.md")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert 'name: "fmt"' in content
    assert 'description: "my desc"' in content
    assert 'source: "my source"' in content
    assert "the body text" in content


def test_style_names(temp_dir):
    mgr = StyleManager(os.path.join(temp_dir, "styles"))
    mgr.add_style("a", "body")
    mgr.add_style("b", "body")
    assert sorted(mgr.style_names()) == ["a", "b"]


def test_get_style_not_found(temp_dir):
    mgr = StyleManager(os.path.join(temp_dir, "styles"))
    import pytest
    with pytest.raises(FileNotFoundError):
        mgr.get_style("nonexistent")
