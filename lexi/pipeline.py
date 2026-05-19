import json
import sys
import os
from collections import defaultdict
from typing import Dict, List, Optional, Callable

from .cleaner import clean_text_stream
from .lemmatizer import lemmatize_words
from .classifier import Classifier
from .sorter import sort_by_frequency, zipf_to_cefr, get_zipf
from .models import WordInfo, ClassificationResult, CategoryMap
from .pipeline_outputs import build_category_map, generate_markdown, generate_json, generate_csv, generate_html, generate_anki


def run_pipeline(
    input_file: str,
    categories_json: str = "data/categories.json",
    stopwords_txt: str = "data/stopwords.txt",
    output_md: str = "output.md",
    output_json: str = "output.json",
    output_csv: Optional[str] = None,
    output_html: Optional[str] = None,
    output_anki: Optional[str] = None,
    overrides_json: Optional[str] = None,
    progress_callback: Optional[Callable] = None,
    status_callback: Optional[Callable] = None,
):
    _status = status_callback or (lambda msg: print(msg))
    _progress = progress_callback or (lambda pct: None)

    # Step 1
    _status("Step 1: 流式清洗文本...")
    raw_words = list(clean_text_stream(input_file))
    _status(f"  提取原始单词数: {len(raw_words)}")
    _progress(0.15)

    # Step 2
    _status("Step 2: 词形还原...")
    lemmatized = lemmatize_words(raw_words)
    _status(f"  还原后唯一词数: {len(lemmatized)}")
    _progress(0.25)

    # Step 3
    _status("Step 3: 加载分类器...")
    classifier = Classifier(categories_json, stopwords_txt, overrides_json)
    _progress(0.30)

    # Step 4
    _status("Step 4: 分类...")
    word_infos: Dict[str, WordInfo] = {}
    total = len(lemmatized)
    for i, word in enumerate(lemmatized):
        categories = classifier.classify(word)
        if categories:
            zipf = get_zipf(word)
            word_infos[word] = WordInfo(
                word=word,
                classifications=categories,
                zipf_frequency=zipf,
                cefr_level=zipf_to_cefr(zipf),
            )
        if i % 500 == 0 and total > 1000:
            _progress(0.30 + 0.35 * (i / total))
    _progress(0.65)

    # Build category map
    classified = build_category_map(word_infos)

    # Step 5
    _status("Step 5: 词频排序...")
    for main_cat in list(classified.keys()):
        for sub_cat in list(classified[main_cat].keys()):
            word_list = classified[main_cat][sub_cat]
            word_list.sort(key=lambda wi: wi.zipf_frequency, reverse=True)
            if not word_list:
                del classified[main_cat][sub_cat]
        if not classified[main_cat]:
            del classified[main_cat]
    _progress(0.80)

    # Step 6
    _status("Step 6: 生成输出文件...")
    if output_md:
        generate_markdown(classified, output_md)
    if output_json:
        generate_json(classified, output_json, word_infos)

    if output_csv:
        generate_csv(classified, word_infos, output_csv)
    if output_html:
        generate_html(classified, word_infos, output_html)
    if output_anki:
        generate_anki(classified, word_infos, output_anki)

    _progress(1.0)
    _status("完成")

