import re
from typing import Iterator, Set
from nltk.corpus import wordnet as wn

CONTRACTIONS = {
    "don't": "do not",
    "can't": "cannot",
    "won't": "will not",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "hasn't": "has not",
    "haven't": "have not",
    "hadn't": "had not",
    "doesn't": "does not",
    "didn't": "did not",
    "wouldn't": "would not",
    "shouldn't": "should not",
    "couldn't": "could not",
    "mightn't": "might not",
    "mustn't": "must not",
    "needn't": "need not",
    "i'm": "i am",
    "you're": "you are",
    "he's": "he is",
    "she's": "she is",
    "it's": "it is",
    "we're": "we are",
    "they're": "they are",
    "i've": "i have",
    "you've": "you have",
    "we've": "we have",
    "they've": "they have",
    "i'd": "i would",
    "you'd": "you would",
    "he'd": "he would",
    "she'd": "she would",
    "we'd": "we would",
    "they'd": "they would",
    "i'll": "i will",
    "you'll": "you will",
    "he'll": "he will",
    "she'll": "she will",
    "we'll": "we will",
    "they'll": "they will",
    "let's": "let us",
    "who's": "who is",
    "what's": "what is",
    "that's": "that is",
    "there's": "there is",
    "here's": "here is"
}

_multiword_cache = None

def _get_multiword_set() -> Set[str]:
    global _multiword_cache
    if _multiword_cache is not None:
        return _multiword_cache
    multiwords = set()
    for ss in wn.all_synsets():
        for lemma in ss.lemmas():
            name = lemma.name()
            if '_' in name:
                multiwords.add(name.lower())
    _multiword_cache = multiwords
    return multiwords

def _protect_phrases(text: str) -> str:
    words = text.split()
    if len(words) < 2:
        return text
    multiwords = _get_multiword_set()
    i = 0
    result_parts = []
    while i < len(words):
        found = False
        for length in range(3, 1, -1):
            if i + length <= len(words):
                candidate = '_'.join(words[i:i+length])
                if candidate in multiwords:
                    result_parts.append(candidate)
                    i += length
                    found = True
                    break
        if not found:
            result_parts.append(words[i])
            i += 1
    return ' '.join(result_parts)

def clean_text_stream(file_path: str) -> Iterator[str]:
    phonetic_pattern = re.compile(r'[a-zA-Z]?:?/.*?/')
    pos_pattern = re.compile(r'\b(?:n|v|vt|vi|adj|adv|prep|conj|pron|num|art)\.\s*', re.IGNORECASE)
    non_alpha = re.compile(r'[^a-zA-Z\s_]')
    multi_space = re.compile(r'\s+')

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.lower()
            line = phonetic_pattern.sub('', line)
            line = pos_pattern.sub('', line)
            for contr, full in CONTRACTIONS.items():
                line = re.sub(rf"\b{re.escape(contr)}\b", full, line)
            line = non_alpha.sub(' ', line)
            line = multi_space.sub(' ', line).strip()
            line = _protect_phrases(line)

            for word in line.split():
                if len(word) >= 2 and re.match(r'^[a-z_]+$', word):
                    yield word