from lexi.sorter import zipf_to_cefr, sort_by_frequency, get_zipf


def test_zipf_to_cefr_a1(mock_wordfreq):
    assert zipf_to_cefr(5.0) == "A1"
    assert zipf_to_cefr(4.5) == "A1"


def test_zipf_to_cefr_a2(mock_wordfreq):
    assert zipf_to_cefr(4.0) == "A2"


def test_zipf_to_cefr_b1(mock_wordfreq):
    assert zipf_to_cefr(3.5) == "B1"


def test_zipf_to_cefr_b2(mock_wordfreq):
    assert zipf_to_cefr(3.0) == "B2"


def test_zipf_to_cefr_c1(mock_wordfreq):
    assert zipf_to_cefr(2.5) == "C1"


def test_zipf_to_cefr_c2(mock_wordfreq):
    assert zipf_to_cefr(1.0) == "C2"
    assert zipf_to_cefr(0.0) == "C2"


def test_get_zipf(mock_wordfreq):
    assert get_zipf("dog") == 3.8
    assert get_zipf("unknown") == 3.0


def test_sort_by_frequency_descending(mock_wordfreq):
    words = ["angry", "dog", "time"]
    result = sort_by_frequency(words)
    assert result == ["time", "dog", "angry"]


def test_sort_by_frequency_empty(mock_wordfreq):
    assert sort_by_frequency([]) == []
