"""Story subcommand."""

import argparse, os, sys


def build_parser():
    parser = argparse.ArgumentParser(description="Lexi: AI 短文生成")
    parser.add_argument("input", help="已分类的 JSON 文件路径")
    parser.add_argument("--output", default="story.md")
    parser.add_argument("--count", type=int, default=20, help="目标词汇数量 (10-50)")
    parser.add_argument("--words", help="手动指定词汇列表，逗号分隔")
    parser.add_argument("--strategy", choices=["balanced","top_frequency","random","stratified"], default="balanced")
    parser.add_argument("--length", choices=["short","medium","long"], default="medium")
    parser.add_argument("--language", choices=["en","zh"], default="en")
    parser.add_argument("--style", help="风格模板名称")
    parser.add_argument("--api-config", help="API 配置文件路径")
    parser.add_argument("--api-key", help="API 密钥")
    parser.add_argument("--api-base-url", help="API 基础 URL")
    parser.add_argument("--model", help="模型名称")
    return parser


def handle_story(ctrl, argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not os.path.exists(args.input):
        print(f"文件不存在: {args.input}", file=sys.stderr); sys.exit(1)
    if args.api_key: ctrl.config.api_key = args.api_key
    if args.api_base_url: ctrl.config.api_base_url = args.api_base_url
    if args.model: ctrl.config.model = args.model
    if args.api_config: ctrl.load_config(args.api_config)
    try:
        wl = [w.strip() for w in args.words.split(",") if w.strip()] if args.words else None
        result = ctrl.generate_story(input_json=args.input,
            output_dir=os.path.dirname(os.path.abspath(args.output)) or ".",
            word_list=wl, count=args.count, strategy=args.strategy,
            length=args.length, language=args.language, style=args.style)
        sp = os.path.join(os.path.dirname(os.path.abspath(args.output)) or ".",
                          os.path.splitext(os.path.basename(args.input))[0] + "_story.md")
        print(f"短文已生成: {sp}")
        print(f"  模型: {result.model}")
        total = len(result.words_used) + len(result.words_missed)
        print(f"  已使用: {len(result.words_used)}/{total}")
        if result.words_missed: print(f"  未使用: {', '.join(result.words_missed)}")
        print(f"  短文词数: {result.word_count}")
    except FileNotFoundError as e: print(f"文件不存在: {e}", file=sys.stderr); sys.exit(1)
    except ImportError as e: print(f"缺少依赖: {e}", file=sys.stderr); sys.exit(1)
    except ValueError as e: print(f"配置错误: {e}", file=sys.stderr); sys.exit(1)
    except Exception as e: print(f"生成出错: {e}", file=sys.stderr); sys.exit(1)
