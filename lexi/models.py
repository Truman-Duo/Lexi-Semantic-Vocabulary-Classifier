from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ClassificationResult:
    main_category: str
    sub_category: str
    confidence: float = 1.0
    source: str = "dictionary"  # dictionary | fuzzy | suffix | pos_fallback | override | stopword | collocation

    def __hash__(self):
        return hash((self.main_category, self.sub_category))


@dataclass
class WordInfo:
    word: str
    classifications: List[ClassificationResult] = field(default_factory=list)
    zipf_frequency: float = 0.0
    cefr_level: str = ""
    etymology: str = ""

    def primary_category(self) -> str:
        if not self.classifications:
            return ""
        return max(self.classifications, key=lambda c: c.confidence).main_category

    def primary_sub_category(self) -> str:
        if not self.classifications:
            return ""
        return max(self.classifications, key=lambda c: c.confidence).sub_category


CategoryMap = Dict[str, Dict[str, List[WordInfo]]]
"""Nested dict: main_category -> sub_category -> sorted WordInfo list"""
