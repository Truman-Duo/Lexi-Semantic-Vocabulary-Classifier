import json
import os
from typing import Dict, List, Tuple, Set
import nltk
from nltk.corpus import wordnet as wn

try:
    nltk.data.find('taggers/averaged_perceptron_tagger_eng')
except LookupError:
    nltk.download('averaged_perceptron_tagger_eng')
except:
    nltk.download('averaged_perceptron_tagger')

def get_wordnet_pos(nltk_tag: str) -> str:
    if nltk_tag.startswith('J'):
        return 'ADJ'
    elif nltk_tag.startswith('V'):
        return 'VERB'
    elif nltk_tag.startswith('N'):
        return 'NOUN'
    elif nltk_tag.startswith('R'):
        return 'ADV'
    else:
        return None

def pos_fallback_category(word: str) -> List[Tuple[str, str]]:
    pos_tag = nltk.pos_tag([word])[0][1]
    pos = get_wordnet_pos(pos_tag)
    if pos == 'ADJ':
        return [("客观类", "属性特征")]
    elif pos == 'ADV':
        return [("抽象类", "关系连接")]
    elif pos == 'VERB':
        return [("主观类", "主观动作")]
    elif pos == 'NOUN':
        if word.endswith(('tion', 'sion', 'ment', 'ance', 'ence', 'ity', 'ness', 'ism', 'logy', 'sis')):
            return [("抽象类", "基础概念")]
        if word in {'idea', 'concept', 'theory', 'law', 'system', 'method', 'process', 'result', 'reason', 'cause', 'effect', 'condition', 'relation', 'fact', 'truth', 'meaning', 'sense', 'value', 'quality', 'quantity', 'time', 'space', 'energy', 'force', 'power', 'ability', 'capacity', 'opportunity', 'chance', 'way', 'means'}:
            return [("抽象类", "基础概念")]
        return [("客观类", "具体事物")]
    else:
        return [("抽象类", "关系连接")]

class Classifier:
    def __init__(self, categories_path: str, stopwords_path: str = None):
        self.word_to_cat = self._load_categories(categories_path)
        self.stopwords = self._load_stopwords(stopwords_path)

    def _load_categories(self, path: str) -> Dict[str, List[Tuple[str, str]]]:
        with open(path, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        mapping = {}
        for main_cat, sub_cats in rules.items():
            for sub_cat, word_list in sub_cats.items():
                for word in word_list:
                    mapping.setdefault(word, []).append((main_cat, sub_cat))
        return mapping

    def _load_stopwords(self, path: str) -> Set[str]:
        if not path or not os.path.exists(path):
            return set()
        with open(path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())

    def classify(self, word: str) -> List[Tuple[str, str]]:
        categories = []

        if word in self.stopwords:
            return [("过滤词", "停用词")]

        if word in self.word_to_cat:
            categories.extend(self.word_to_cat[word])

        if word.endswith('ly'):
            categories.append(("抽象类", "关系连接"))
        if word.endswith(('ing', 'ed', 'en')):
            categories.append(("主观类", "主观动作"))
        if word.endswith(('tion', 'sion', 'ment', 'ance', 'ence')):
            categories.append(("抽象类", "基础概念"))
        if word.endswith(('ous', 'ive', 'ful', 'less')):
            categories.append(("客观类", "属性特征"))

        if not categories:
            categories.extend(pos_fallback_category(word))

        return list(set(categories))