"""Classify subcommand."""

import argparse
import sys
from lexi.controller import LexiController, OutputOptions


def build_parser():
    parser = argparse.ArgumentParser(description="Lexi: 离线多标签英文词汇意群分类工具")
    parser.add_argument("input", nargs="?", help="输入文本文件路径（留空则显示帮助）")
    parser.add_argument("--categories", default="data/categories_full.json")
    parser.add_argument("--stopwords", default="data/stopwords.txt")
    parser.add_argument("--overrides", default=None)
    parser.add_argument("--output-md", default="output.md")
    parser.add_argument("--output-json", default="output.json")
    parser.add_argument("--output-csv", default=None)
    parser.add_argument("--output-html", default=None)
    parser.add_argument("--output-anki", default=None)
    return parser


def run_classify(argv):
    parser = build_parser()
    args = parser.parse_args(argv[1:])

    if not args.input:
        parser.print_help()
        print()
        print("=" * 60)
        print("  使用示例:")
        print("    python cli.py test.txt")
        print("    python cli.py test.txt --output-csv out.csv")
        print("    python cli.py test.txt --output-html out.html --output-anki deck.apkg")
        print()
        print("  AI 短文生成:")
        print("    python cli.py config --api-key sk-...")
        print("    python cli.py story output.json --count 20")
        print()
        print("  风格模板管理:")
        print("    python cli.py style add \"TOEFL\" passage.txt")
        print("    python cli.py style list")
        print("=" * 60)
        sys.exit(1)

    ctrl = LexiController()
    outputs = OutputOptions(
        markdown=bool(args.output_md), json=bool(args.output_json),
        csv=bool(args.output_csv), html=bool(args.output_html), anki=bool(args.output_anki))
    try:
        result = ctrl.classify(
            input_file=args.input, categories_path=args.categories,
            stopwords_path=args.stopwords, overrides_path=args.overrides,
            outputs=outputs, output_dir=".")
        print(f"分类完成！共 {result.total_words} 个单词")
        for fmt, path in sorted(result.output_files.items()):
            print(f"  {fmt}: {path}")
    except FileNotFoundError as e:
        print(f"文件不存在: {e}", file=sys.stderr); sys.exit(1)
    except ImportError as e:
        print(f"缺少依赖: {e}", file=sys.stderr); sys.exit(1)
    except Exception as e:
        print(f"处理出错: {e}", file=sys.stderr); sys.exit(1)
