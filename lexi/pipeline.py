import sys
from collections import defaultdict
from .cleaner import clean_text_stream
from .lemmatizer import lemmatize_words
from .classifier import Classifier
from .sorter import sort_by_frequency


def run_pipeline(
    input_file: str,
    categories_json: str = "data/categories.json",
    stopwords_txt: str = "data/stopwords.txt",
    output_md: str = "output.md",
    output_json: str = "output.json"
):
    print("Step 1: 流式清洗文本...")
    raw_words = list(clean_text_stream(input_file))
    print(f"  提取原始单词数: {len(raw_words)}")

    print("Step 2: 词形还原...")
    lemmatized = lemmatize_words(raw_words)
    print(f"  还原后唯一词数: {len(lemmatized)}")

    print("Step 3: 加载分类器...")
    classifier = Classifier(categories_json, stopwords_txt)

    print("Step 4: 分类...")
    classified = defaultdict(lambda: defaultdict(set))

    for word in lemmatized:
        categories = classifier.classify(word)
        for main_cat, sub_cat in categories:
            classified[main_cat][sub_cat].add(word)

    print("Step 5: 词频排序（每个子类内部）...")
    for main_cat in list(classified.keys()):
        for sub_cat in list(classified[main_cat].keys()):
            words = list(classified[main_cat][sub_cat])
            classified[main_cat][sub_cat] = sort_by_frequency(words)
            if not classified[main_cat][sub_cat]:
                del classified[main_cat][sub_cat]
        if not classified[main_cat]:
            del classified[main_cat]

    print("Step 6: 生成输出文件...")
    _generate_markdown(classified, output_md)
    _generate_json(classified, output_json)

    print(f"完成！Markdown: {output_md}, JSON: {output_json}")


def _generate_markdown(classified, output_md):
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write("# 词汇分类笔记\n\n")
        for main_cat, sub_cats in classified.items():
            f.write(f"# {main_cat}\n\n")
            for sub_cat, words in sub_cats.items():
                f.write(f"## {sub_cat}\n")
                for idx, w in enumerate(words, 1):
                    f.write(f"{idx}. {w}\n")
                f.write("\n")


def _generate_json(classified, output_json):
    import json
    all_unique_words = set()
    for sub_cats in classified.values():
        for words in sub_cats.values():
            all_unique_words.update(words)
    result = {
        "total_words": len(all_unique_words),
        "categories": classified
    }
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)