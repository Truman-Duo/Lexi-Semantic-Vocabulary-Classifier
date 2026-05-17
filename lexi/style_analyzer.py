import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


NOMINALIZATION_SUFFIXES = {
    "tion", "sion", "ment", "ance", "ence", "ity", "ness", "al", "age", "ure",
}

SUBORDINATING_CONJUNCTIONS = {
    "although", "though", "because", "since", "while", "whereas",
    "if", "when", "whenever", "unless", "until", "after", "before",
    "that", "which", "who", "whom", "whose", "where", "whereby",
    "whereas", "whereupon", "as", "once", "than", "whether",
    "so that", "in order that", "provided that",
}

COORDINATING_CONJUNCTIONS = {
    "and", "but", "or", "nor", "for", "so", "yet",
}

TRANSITION_WORDS = {
    "however", "therefore", "moreover", "furthermore", "consequently",
    "nevertheless", "nonetheless", "thus", "hence", "accordingly",
    "meanwhile", "subsequently", "additionally", "alternatively",
    "instead", "otherwise", "likewise", "similarly", "indeed",
    "in contrast", "on the other hand", "for example", "for instance",
    "in addition", "in fact", "as a result", "in conclusion",
}

PERSONAL_PRONOUNS = {
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them",
    "my", "your", "his", "her", "its", "our", "their",
    "mine", "yours", "hers", "ours", "theirs",
    "myself", "yourself", "himself", "herself", "itself",
    "ourselves", "yourselves", "themselves",
}

CONTENT_POS = {"NN", "NNS", "NNP", "NNPS", "VB", "VBD", "VBG", "VBN", "VBP", "VBZ",
               "JJ", "JJR", "JJS", "RB", "RBR", "RBS", "WRB"}


@dataclass
class StyleProfile:
    avg_word_length: float = 0.0
    type_token_ratio: float = 0.0
    cefr_distribution: Dict[str, float] = field(default_factory=dict)

    avg_sentence_length: float = 0.0
    sentence_length_std: float = 0.0
    passive_voice_ratio: float = 0.0

    flesch_reading_ease: float = 0.0
    flesch_kincaid_grade: float = 0.0

    nominalization_ratio: float = 0.0
    modifier_density: float = 0.0
    lexical_density: float = 0.0
    subordination_ratio: float = 0.0
    coordination_ratio: float = 0.0
    transition_density: float = 0.0
    pronoun_density: float = 0.0

    def dominant_cefr(self) -> str:
        if not self.cefr_distribution:
            return "mixed"
        sorted_levels = sorted(
            self.cefr_distribution.items(), key=lambda x: x[1], reverse=True
        )
        top = sorted_levels[0]
        if top[1] < 0.25 and len(sorted_levels) >= 2:
            return f"{sorted_levels[0][0]}-{sorted_levels[1][0]}"
        return top[0]

    def to_frontmatter(self) -> Dict[str, str]:
        fm = {
            "avg_word_length": str(round(self.avg_word_length, 1)),
            "type_token_ratio": str(round(self.type_token_ratio, 2)),
            "avg_sentence_length": str(round(self.avg_sentence_length, 1)),
            "sentence_length_std": str(round(self.sentence_length_std, 1)),
            "passive_voice_ratio": str(round(self.passive_voice_ratio, 2)),
            "flesch_reading_ease": str(round(self.flesch_reading_ease, 1)),
            "flesch_kincaid_grade": str(round(self.flesch_kincaid_grade, 1)),
            "nominalization_ratio": str(round(self.nominalization_ratio, 2)),
            "modifier_density": str(round(self.modifier_density, 2)),
            "lexical_density": str(round(self.lexical_density, 2)),
            "subordination_ratio": str(round(self.subordination_ratio, 2)),
            "coordination_ratio": str(round(self.coordination_ratio, 2)),
            "transition_density": str(round(self.transition_density, 2)),
            "pronoun_density": str(round(self.pronoun_density, 2)),
        }
        for level, pct in self.cefr_distribution.items():
            fm[f"cefr_{level}"] = str(round(pct, 2))
        return fm

    @classmethod
    def from_frontmatter(cls, fm: Dict[str, str]) -> "StyleProfile":
        def _f(key: str) -> float:
            try:
                return float(fm.get(key, 0))
            except (ValueError, TypeError):
                return 0.0

        profile = cls(
            avg_word_length=_f("avg_word_length"),
            type_token_ratio=_f("type_token_ratio"),
            avg_sentence_length=_f("avg_sentence_length"),
            sentence_length_std=_f("sentence_length_std"),
            passive_voice_ratio=_f("passive_voice_ratio"),
            flesch_reading_ease=_f("flesch_reading_ease"),
            flesch_kincaid_grade=_f("flesch_kincaid_grade"),
            nominalization_ratio=_f("nominalization_ratio"),
            modifier_density=_f("modifier_density"),
            lexical_density=_f("lexical_density"),
            subordination_ratio=_f("subordination_ratio"),
            coordination_ratio=_f("coordination_ratio"),
            transition_density=_f("transition_density"),
            pronoun_density=_f("pronoun_density"),
        )
        for key, val in fm.items():
            if key.startswith("cefr_"):
                try:
                    profile.cefr_distribution[key[5:]] = float(val)
                except (ValueError, TypeError):
                    pass
        return profile


class StyleAnalyzer:
    VOWELS = set("aeiou")
    BE_FORMS = {"am", "is", "are", "was", "were", "be", "been", "being"}

    def analyze(self, text: str) -> StyleProfile:
        text = text.strip()
        if not text:
            return StyleProfile()

        words = self._tokenize_words(text)
        sentences = self._split_sentences(text)
        tagged = self._get_pos_tags(text)
        sentence_count = len(sentences)

        return StyleProfile(
            avg_word_length=self._avg_word_length(words),
            type_token_ratio=self._type_token_ratio(words),
            cefr_distribution=self._cefr_distribution(words),
            avg_sentence_length=self._avg_sentence_length(sentences),
            sentence_length_std=self._sentence_length_std(sentences),
            passive_voice_ratio=self._passive_voice_ratio(tagged),
            flesch_reading_ease=self._flesch_reading_ease(words, sentences),
            flesch_kincaid_grade=self._flesch_kincaid_grade(words, sentences),
            nominalization_ratio=self._nominalization_ratio(words),
            modifier_density=self._modifier_density(tagged),
            lexical_density=self._lexical_density(tagged, len(words)),
            subordination_ratio=self._subordination_ratio(tagged, sentence_count),
            coordination_ratio=self._coordination_ratio(tagged, sentence_count),
            transition_density=self._transition_density(words),
            pronoun_density=self._pronoun_density(tagged, len(words)),
        )

    def _tokenize_words(self, text: str) -> List[str]:
        return re.findall(r"[a-zA-Z]+", text.lower())

    def _split_sentences(self, text: str) -> List[List[str]]:
        raw = re.split(r"[.!?]+", text)
        sentences = []
        for part in raw:
            words = self._tokenize_words(part)
            if len(words) >= 2:
                sentences.append(words)
        return sentences

    def _get_pos_tags(self, text: str) -> Optional[List[Tuple[str, str]]]:
        try:
            import nltk
            tokens = nltk.word_tokenize(text)
            return nltk.pos_tag(tokens)
        except Exception:
            return None

    def _avg_word_length(self, words: List[str]) -> float:
        if not words:
            return 0.0
        return sum(len(w) for w in words) / len(words)

    def _type_token_ratio(self, words: List[str]) -> float:
        if not words:
            return 0.0
        return len(set(words)) / len(words)

    def _cefr_distribution(self, words: List[str]) -> Dict[str, float]:
        try:
            from lexi.sorter import get_zipf, zipf_to_cefr
        except ImportError:
            return {}
        if not words:
            return {}
        counter = Counter()
        for w in set(words):
            try:
                zipf = get_zipf(w)
                level = zipf_to_cefr(zipf)
                counter[level] += 1
            except Exception:
                pass
        total = sum(counter.values())
        if total == 0:
            return {}
        return {level: count / total for level, count in sorted(counter.items())}

    def _avg_sentence_length(self, sentences: List[List[str]]) -> float:
        if not sentences:
            return 0.0
        return sum(len(s) for s in sentences) / len(sentences)

    def _sentence_length_std(self, sentences: List[List[str]]) -> float:
        if len(sentences) < 2:
            return 0.0
        lengths = [len(s) for s in sentences]
        mean = sum(lengths) / len(lengths)
        variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
        return math.sqrt(variance)

    def _passive_voice_ratio(self, tagged: Optional[List[Tuple[str, str]]]) -> float:
        if not tagged:
            return 0.0
        verb_count = 0
        passive_count = 0
        i = 0
        while i < len(tagged):
            word, tag = tagged[i]
            word_lower = word.lower()
            if tag.startswith("VB"):
                verb_count += 1
                if word_lower in self.BE_FORMS and i + 1 < len(tagged):
                    next_word, next_tag = tagged[i + 1]
                    if next_tag == "VBN":
                        passive_count += 1
                        i += 1
            i += 1
        if verb_count == 0:
            return 0.0
        return passive_count / verb_count

    def _nominalization_ratio(self, words: List[str]) -> float:
        if not words:
            return 0.0
        count = 0
        for w in words:
            for suffix in NOMINALIZATION_SUFFIXES:
                if w.endswith(suffix) and len(w) > len(suffix) + 1:
                    count += 1
                    break
        return count / len(words)

    def _modifier_density(self, tagged: Optional[List[Tuple[str, str]]]) -> float:
        if not tagged:
            return 0.0
        modifiers = 0
        content_words = 0
        for _, tag in tagged:
            if tag.startswith("JJ") or tag.startswith("RB"):
                modifiers += 1
            if tag in CONTENT_POS:
                content_words += 1
        if content_words == 0:
            return 0.0
        return modifiers / content_words

    def _lexical_density(self, tagged: Optional[List[Tuple[str, str]]], total: int) -> float:
        if not tagged or total == 0:
            return 0.0
        content = sum(1 for _, tag in tagged if tag in CONTENT_POS)
        return content / total

    def _subordination_ratio(
        self, tagged: Optional[List[Tuple[str, str]]], sentence_count: int
    ) -> float:
        if not tagged or sentence_count == 0:
            return 0.0
        count = sum(1 for w, _ in tagged if w.lower() in SUBORDINATING_CONJUNCTIONS)
        return count / sentence_count

    def _coordination_ratio(
        self, tagged: Optional[List[Tuple[str, str]]], sentence_count: int
    ) -> float:
        if not tagged or sentence_count == 0:
            return 0.0
        count = sum(1 for w, _ in tagged if w.lower() in COORDINATING_CONJUNCTIONS)
        return count / sentence_count

    def _transition_density(self, words: List[str]) -> float:
        if not words:
            return 0.0
        text_lower = " ".join(words)
        count = 0
        for tw in TRANSITION_WORDS:
            count += text_lower.count(tw)
        return count / len(words) * 100

    def _pronoun_density(self, tagged: Optional[List[Tuple[str, str]]], total: int) -> float:
        if not tagged or total == 0:
            return 0.0
        count = sum(1 for w, _ in tagged if w.lower() in PERSONAL_PRONOUNS)
        return count / total

    def _count_syllables(self, word: str) -> int:
        word = word.lower().strip()
        if not word:
            return 0
        if len(word) <= 3:
            return 1

        count = 0
        prev_vowel = False
        for i, ch in enumerate(word):
            is_vowel = ch in self.VOWELS
            if ch == "y" and i == len(word) - 1:
                is_vowel = True
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel

        if word.endswith("e"):
            if word.endswith("le") and len(word) > 2 and word[-3] not in self.VOWELS:
                pass
            else:
                count -= 1

        return max(1, count)

    def _flesch_reading_ease(self, words: List[str], sentences: List[List[str]]) -> float:
        if not words or not sentences:
            return 0.0
        total_words = len(words)
        total_sentences = len(sentences)
        total_syllables = sum(self._count_syllables(w) for w in words)
        return (
            206.835
            - 1.015 * (total_words / total_sentences)
            - 84.6 * (total_syllables / total_words)
        )

    def _flesch_kincaid_grade(self, words: List[str], sentences: List[List[str]]) -> float:
        if not words or not sentences:
            return 0.0
        total_words = len(words)
        total_sentences = len(sentences)
        total_syllables = sum(self._count_syllables(w) for w in words)
        return (
            0.39 * (total_words / total_sentences)
            + 11.8 * (total_syllables / total_words)
            - 15.59
        )
