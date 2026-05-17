#!/usr/bin/env python3
import argparse
import sys
from lexi.pipeline import run_pipeline


def build_parser():
    parser = argparse.ArgumentParser(
        description="Lexi: 离线多标签英文词汇意群分类工具")
    parser.add_argument(
        "input", nargs="?",
        help="输入文本文件路径（留空则显示帮助）")
    parser.add_argument(
        "--categories", default="data/categories_full.json",
        help="分类规则 JSON 文件 (默认: data/categories_full.json)")
    parser.add_argument(
        "--stopwords", default="data/stopwords.txt",
        help="停用词表路径")
    parser.add_argument(
        "--overrides", default=None,
        help="用户自定义分类覆盖 JSON 文件")
    parser.add_argument(
        "--output-md", default="output.md",
        help="输出 Markdown 文件 (默认: output.md)")
    parser.add_argument(
        "--output-json", default="output.json",
        help="输出 JSON 文件 (默认: output.json)")
    parser.add_argument(
        "--output-csv", default=None,
        help="输出 CSV 文件（含词频/CEFR/置信度）")
    parser.add_argument(
        "--output-html", default=None,
        help="输出交互式 HTML 浏览器")
    parser.add_argument(
        "--output-anki", default=None,
        help="输出 Anki 牌组 (.apkg)")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.input:
        parser.print_help()
        print()
        print("=" * 60)
        print("  使用示例:")
        print("    python cli.py test.txt")
        print("    python cli.py test.txt --output-csv out.csv")
        print("    python cli.py test.txt --output-html out.html --output-anki deck.apkg")
        print("    python cli.py test.txt --overrides my_overrides.json")
        print("=" * 60)
        sys.exit(1)

    try:
        run_pipeline(
            input_file=args.input,
            categories_json=args.categories,
            stopwords_txt=args.stopwords,
            overrides_json=args.overrides,
            output_md=args.output_md,
            output_json=args.output_json,
            output_csv=args.output_csv,
            output_html=args.output_html,
            output_anki=args.output_anki,
        )
    except FileNotFoundError as e:
        print(f"文件不存在: {e}", file=sys.stderr)
        sys.exit(1)
    except ImportError as e:
        print(f"缺少依赖: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"处理出错: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
