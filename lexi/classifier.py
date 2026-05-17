import json
import os
from typing import Dict, List, Set, Optional

import nltk

from .models import ClassificationResult

_NLTK_INITIALIZED = False


def _ensure_nltk_resources():
    global _NLTK_INITIALIZED
    if _NLTK_INITIALIZED:
        return
    try:
        nltk.data.find('taggers/averaged_perceptron_tagger_eng')
    except LookupError:
        nltk.download('averaged_perceptron_tagger_eng')
    except Exception:
        try:
            nltk.download('averaged_perceptron_tagger')
        except Exception:
            pass
    _NLTK_INITIALIZED = True


# Suffix patterns for derivational matching.
# Each entry: (suffix_to_strip, replacement_ending)
# E.g., ("iness", "y") means strip "iness", append "y": happiness -> happy
_DERIVATIONAL_PATTERNS = [
    ("iness", "y"),     # happiness -> happy
    ("ivity", "ive"),   # activity -> active
    ("ivity", ""),      # sensitivity -> sensitiv... fallback
    ("ness", ""),       # darkness -> dark
    ("fully", ""),      # beautifully -> beautiful (but already lemmatized usually)
    ("fully", "ful"),   # beautifully -> beautiful
    ("lessly", "less"), # recklessly -> reckless
    ("lessly", "less"),
    ("fully", "ful"),
    ("ment", ""),       # enjoyment -> enjoy
    ("tion", "te"),     # activation -> activate
    ("tion", ""),       # action -> act
    ("sion", "de"),     # decision -> decide
    ("sion", ""),       # expansion -> expans... hmm
    ("ness", ""),
    ("able", ""),       # readable -> read
    ("ible", ""),       # visible -> vis (weak)
    ("less", ""),       # helpless -> help
    ("ful", ""),        # hopeful -> hope
    ("ous", ""),        # dangerous -> danger
    ("ity", "e"),       # equality -> equal (actually strip ity, add e? no...)
    ("ity", ""),        # curiosity -> curiou... not great
    ("al", ""),         # natural -> natur -> nature? no
    ("ive", ""),        # active -> act
    ("ize", ""),        # realize -> real
    ("ise", ""),        # realise -> real
    ("ify", ""),        # classify -> class
    ("er", ""),         # teacher -> teach
    ("or", ""),         # actor -> act
    ("ing", ""),        # reading -> read
    ("ed", ""),         # walked -> walk
    ("en", ""),         # widen -> wide
    ("ly", ""),         # quickly -> quick
    ("ily", "y"),       # happily -> happy
    ("ly", ""),
    ("ist", ""),        # artist -> art
    ("ism", ""),        # capitalism -> capital
    ("ian", ""),        # musician -> music
    ("ic", ""),         # poetic -> poet
]

# Define which POS tag patterns map to which category
_POS_NOUN_ABSTRACT = {'idea', 'concept', 'theory', 'law', 'system', 'method',
                      'process', 'result', 'reason', 'cause', 'effect',
                      'condition', 'relation', 'fact', 'truth', 'meaning',
                      'sense', 'value', 'quality', 'quantity', 'time', 'space',
                      'energy', 'force', 'power', 'ability', 'capacity',
                      'opportunity', 'chance', 'way', 'means'}


def get_wordnet_pos(nltk_tag: str) -> Optional[str]:
    if nltk_tag.startswith('J'):
        return 'ADJ'
    elif nltk_tag.startswith('V'):
        return 'VERB'
    elif nltk_tag.startswith('N'):
        return 'NOUN'
    elif nltk_tag.startswith('R'):
        return 'ADV'
    return None


def pos_fallback_category(word: str) -> List[ClassificationResult]:
    _ensure_nltk_resources()
    pos_tag = nltk.pos_tag([word])[0][1]
    pos = get_wordnet_pos(pos_tag)
    if pos == 'ADJ':
        return [ClassificationResult("客观类", "属性特征", 0.4, "pos_fallback")]
    elif pos == 'ADV':
        return [ClassificationResult("抽象类", "关系连接", 0.4, "pos_fallback")]
    elif pos == 'VERB':
        return [ClassificationResult("主观类", "主观动作", 0.4, "pos_fallback")]
    elif pos == 'NOUN':
        if word.endswith(('tion', 'sion', 'ment', 'ance', 'ence', 'ity', 'ness', 'ism', 'logy', 'sis')):
            return [ClassificationResult("抽象类", "基础概念", 0.4, "pos_fallback")]
        if word in _POS_NOUN_ABSTRACT:
            return [ClassificationResult("抽象类", "基础概念", 0.4, "pos_fallback")]
        return [ClassificationResult("客观类", "具体事物", 0.4, "pos_fallback")]
    else:
        return [ClassificationResult("抽象类", "关系连接", 0.4, "pos_fallback")]


class Classifier:
    def __init__(self, categories_path: str, stopwords_path: str = None,
                 overrides_path: str = None):
        _ensure_nltk_resources()
        self.word_to_cat = self._load_categories(categories_path)
        self.stopwords = self._load_stopwords(stopwords_path)
        self.overrides = self._load_overrides(overrides_path)

    def _load_categories(self, path: str) -> Dict[str, List[ClassificationResult]]:
        with open(path, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        mapping = {}
        for main_cat, sub_cats in rules.items():
            for sub_cat, word_list in sub_cats.items():
                for word in word_list:
                    mapping.setdefault(word, []).append(
                        ClassificationResult(main_cat, sub_cat, 1.0, "dictionary"))
        return mapping

    def _load_stopwords(self, path: str) -> Set[str]:
        if not path or not os.path.exists(path):
            return set()
        with open(path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())

    def _load_overrides(self, path: Optional[str]) -> Dict[str, List[ClassificationResult]]:
        if not path or not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        mapping = {}
        for main_cat, sub_cats in rules.items():
            for sub_cat, word_list in sub_cats.items():
                for word in word_list:
                    mapping.setdefault(word.lower(), []).append(
                        ClassificationResult(main_cat, sub_cat, 1.0, "override"))
        return mapping

    def _try_derivational_match(self, word: str) -> List[ClassificationResult]:
        for suffix, replacement in _DERIVATIONAL_PATTERNS:
            if word.endswith(suffix):
                base = word[:-len(suffix)] + replacement
                if base in self.word_to_cat:
                    results = []
                    for result in self.word_to_cat[base]:
                        results.append(ClassificationResult(
                            result.main_category, result.sub_category,
                            0.8, "fuzzy"))
                    return results
        return []

    def classify(self, word: str) -> List[ClassificationResult]:
        results = []

        # 1. User overrides (highest priority)
        if word in self.overrides:
            results.extend(self.overrides[word])

        # 2. Stopword check
        if word in self.stopwords:
            results.append(ClassificationResult("过滤词", "停用词", 1.0, "stopword"))
            return results

        # 3. Dictionary exact match
        if word in self.word_to_cat:
            results.extend(self.word_to_cat[word])

        # 4. Derivational suffix matching (fuzzy)
        if not any(r.source == "dictionary" for r in results):
            fuzzy = self._try_derivational_match(word)
            results.extend(fuzzy)

        # 5. Suffix rules (always append, confidence 0.6)
        if word.endswith('ly'):
            results.append(ClassificationResult("抽象类", "关系连接", 0.6, "suffix"))
        if word.endswith(('ing', 'ed', 'en')):
            results.append(ClassificationResult("主观类", "主观动作", 0.6, "suffix"))
        if word.endswith(('tion', 'sion', 'ment', 'ance', 'ence')):
            results.append(ClassificationResult("抽象类", "基础概念", 0.6, "suffix"))
        if word.endswith(('ous', 'ive', 'ful', 'less')):
            results.append(ClassificationResult("客观类", "属性特征", 0.6, "suffix"))

        # 6. POS fallback (if nothing found)
        if not results:
            results.extend(pos_fallback_category(word))

        # Deduplicate by (main, sub) keeping highest confidence
        seen = {}
        for r in results:
            key = (r.main_category, r.sub_category)
            if key not in seen or r.confidence > seen[key].confidence:
                seen[key] = r

        return list(seen.values())
