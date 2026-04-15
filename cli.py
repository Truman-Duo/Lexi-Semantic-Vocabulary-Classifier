#!/usr/bin/env python3
import argparse
import sys
from lexi.pipeline import run_pipeline

def main():
    parser = argparse.ArgumentParser(description="Lexi: 大规模英文词汇意群分类工具")
    parser.add_argument("input", help="输入文本文件路径")
    parser.add_argument("--categories", default="data/categories.json", help="分类规则JSON文件")
    parser.add_argument("--stopwords", default="data/stopwords.txt", help="停用词表（可选）")
    parser.add_argument("--output-md", default="output.md", help="输出Markdown文件")
    parser.add_argument("--output-json", default="output.json", help="输出JSON文件")
    args = parser.parse_args()

    try:
        run_pipeline(
            input_file=args.input,
            categories_json=args.categories,
            stopwords_txt=args.stopwords,
            output_md=args.output_md,
            output_json=args.output_json
        )
    except FileNotFoundError as e:
        print(f"文件不存在: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"处理出错: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()