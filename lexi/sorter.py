from typing import List


def _get_wordfreq():
    try:
        from wordfreq import zipf_frequency
        return zipf_frequency
    except ImportError:
        raise ImportError(
            "Missing dependency 'wordfreq'. Run: pip install wordfreq"
        )


# Zipf threshold -> CEFR mapping
_ZIPF_TO_CEFR = [
    (4.5, "A1"),
    (4.0, "A2"),
    (3.5, "B1"),
    (3.0, "B2"),
    (2.5, "C1"),
    (0.0, "C2"),
]


def zipf_to_cefr(zipf: float) -> str:
    for threshold, level in _ZIPF_TO_CEFR:
        if zipf >= threshold:
            return level
    return "C2"


def get_zipf(word: str) -> float:
    zf = _get_wordfreq()
    return zf(word, 'en')


def sort_by_frequency(words: List[str]) -> List[str]:
    zf = _get_wordfreq()
    return sorted(words, key=lambda w: zf(w, 'en'), reverse=True)
