from lexi.lemmatizer import lemmatize_words


def test_lemmatize_basic(mock_lemminflect):
    result = lemmatize_words(["running", "walking"])
    assert "run" in result
    assert "walk" in result


def test_lemmatize_phrases_skipped(mock_lemminflect):
    result = lemmatize_words(["ad_hoc", "per_se"])
    assert "ad_hoc" in result


def test_lemmatize_empty(mock_lemminflect):
    assert lemmatize_words([]) == []


def test_lemmatize_fallback_to_original(mock_lemminflect):
    result = lemmatize_words(["xyznonexistent"])
    assert "xyznonexistent" in result


def test_lemmatize_filters_invalid(mock_lemminflect):
    result = lemmatize_words(["a", "b", "x_y"])
    for w in result:
        assert len(w) >= 2


def test_lemmatize_mixed(mock_lemminflect):
    result = lemmatize_words(["running", "dogs", "ad_hoc", "xyznonexistent"])
    assert "run" in result
    assert "dog" in result
    assert "ad_hoc" in result
    assert "xyznonexistent" in result
