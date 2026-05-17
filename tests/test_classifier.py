import os
from lexi.cleaner import clean_text_stream
from lexi.models import WordInfo, ClassificationResult
from lexi.classifier import Classifier


def test_exact_dictionary_match(small_categories_json, small_stopwords_txt, mock_nltk):
    clf = Classifier(small_categories_json, small_stopwords_txt)
    results = clf.classify("dog")
    assert any(r.main_category == "客观类" and r.sub_category == "具体事物" and r.confidence == 1.0 for r in results)


def test_derivational_fuzzy_match(small_categories_json, small_stopwords_txt, mock_nltk):
    clf = Classifier(small_categories_json, small_stopwords_txt)
    results = clf.classify("happiness")
    assert any(r.source == "fuzzy" and r.confidence == 0.8 for r in results)


def test_suffix_rules(small_categories_json, small_stopwords_txt, mock_nltk):
    clf = Classifier(small_categories_json, small_stopwords_txt)
    results = clf.classify("quickly")
    assert len(results) > 0
    assert any(r.source == "suffix" for r in results)


def test_pos_fallback(small_categories_json, small_stopwords_txt, mock_nltk):
    clf = Classifier(small_categories_json, small_stopwords_txt)
    results = clf.classify("xyznonexistentword")
    assert len(results) > 0
    assert any(r.source == "pos_fallback" for r in results)


def test_stopword_classification(small_categories_json, small_stopwords_txt, mock_nltk):
    clf = Classifier(small_categories_json, small_stopwords_txt)
    results = clf.classify("the")
    assert any(r.main_category == "过滤词" and r.sub_category == "停用词" for r in results)


def test_overrides_take_priority(small_categories_json, small_stopwords_txt, small_overrides_json, mock_nltk):
    clf = Classifier(small_categories_json, small_stopwords_txt, small_overrides_json)
    results = clf.classify("joy")
    assert any(r.source == "override" and r.main_category == "主观类" and r.sub_category == "情绪感受" for r in results)


def test_single_character_word(small_categories_json, small_stopwords_txt, mock_nltk):
    clf = Classifier(small_categories_json, small_stopwords_txt)
    results = clf.classify("x")
    assert len(results) > 0


def test_deduplication(small_categories_json, small_stopwords_txt, mock_nltk):
    clf = Classifier(small_categories_json, small_stopwords_txt)
    results = clf.classify("quickly")
    keys = [(r.main_category, r.sub_category) for r in results]
    assert len(keys) == len(set(keys))
