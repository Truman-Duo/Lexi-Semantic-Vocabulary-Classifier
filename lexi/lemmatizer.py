import re
import lemminflect
from typing import List, Set

def lemmatize_words(words: List[str]) -> List[str]:
    lemmas: Set[str] = set()
    for w in words:
        if not re.match(r'^[a-z_]{2,}$', w):
            continue
        # 包含下划线的短语不进行词形还原
        if '_' in w:
            lemmas.add(w)
            continue
        try:
            results = lemminflect.getAllLemmas(w)
            if results:
                for pos_list in results.values():
                    for lemma in pos_list:
                        if re.match(r'^[a-z]{2,}$', lemma):
                            lemmas.add(lemma)
            else:
                lemmas.add(w)
        except Exception:
            lemmas.add(w)
    return list(lemmas)