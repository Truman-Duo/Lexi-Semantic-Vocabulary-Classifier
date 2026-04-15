from wordfreq import zipf_frequency
from typing import List

def sort_by_frequency(words: List[str]) -> List[str]:
    return sorted(words, key=lambda w: zipf_frequency(w, 'en'), reverse=True)