#!/usr/bin/env python3
import argparse
import os
import sys
from lexi.controller import LexiController, OutputOptions


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


def build_story_parser():
    parser = argparse.ArgumentParser(
        description="Lexi: AI 短文生成 - 基于已分类词汇生成故事")
    parser.add_argument(
        "input", help="已分类的 JSON 文件路径（pipeline 输出）")
    parser.add_argument(
        "--output", default="story.md",
        help="输出 Markdown 文件路径 (默认: story.md)")
    parser.add_argument(
        "--count", type=int, default=20,
        help="目标词汇数量 (10-50, 默认 20)")
    parser.add_argument(
        "--words",
        help="手动指定词汇列表，逗号分隔 (优先级高于 --count)")
    parser.add_argument(
        "--strategy",
        choices=["balanced", "top_frequency", "random", "stratified"],
        default="balanced",
        help="词汇选择策略 (默认: balanced)")
    parser.add_argument(
        "--length",
        choices=["short", "medium", "long"],
        default="medium",
        help="短文长度 (默认: medium, 约 250 词)")
    parser.add_argument(
        "--language",
        choices=["en", "zh"],
        default="en",
        help="提示语语言 (默认: en)")
    parser.add_argument(
        "--style",
        help="风格模板名称（使用 python cli.py style list 查看可用风格）")
    parser.add_argument(
        "--api-config",
        help="API 配置文件路径 (默认: ~/.lexi/config.json)")
    parser.add_argument(
        "--api-key",
        help="API 密钥 (覆盖配置文件)")
    parser.add_argument(
        "--api-base-url",
        help="API 基础 URL (覆盖配置文件)")
    parser.add_argument(
        "--model",
        help="模型名称 (覆盖配置文件)")
    return parser


def build_config_parser():
    parser = argparse.ArgumentParser(
        description="Lexi: 配置 AI API 设置")
    parser.add_argument(
        "--api-key", help="设置 API 密钥")
    parser.add_argument(
        "--api-base-url",
        help="设置 API 基础 URL (默认: https://api.openai.com/v1)")
    parser.add_argument(
        "--model", help="设置模型名称 (默认: gpt-4o-mini)")
    parser.add_argument(
        "--show", action="store_true",
        help="显示当前配置（隐藏密钥）")
    parser.add_argument(
        "--api-config",
        help="配置文件路径 (默认: ~/.lexi/config.json)")
    return parser


def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ("story", "config", "style", "exercise", "plan"):
        subcommand = sys.argv[1]
        ctrl = LexiController()
        if subcommand == "story":
            _handle_story_command(ctrl, sys.argv[2:])
        elif subcommand == "config":
            _handle_config_command(ctrl, sys.argv[2:])
        elif subcommand == "style":
            _handle_style_command(ctrl, sys.argv[2:])
        elif subcommand == "exercise":
            _handle_exercise_command(ctrl, sys.argv[2:])
        elif subcommand == "plan":
            _handle_plan_command(ctrl, sys.argv[2:])
    else:
        _run_classify()


def _run_classify():
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
        print()
        print("  AI 短文生成:")
        print("    python cli.py config --api-key sk-...     (配置 API)")
        print("    python cli.py story output.json --count 20")
        print("    python cli.py story output.json --words \"abandon,beneficial,...\"")
        print("    python cli.py story output.json --style \"TOEFL\"")
        print()
        print("  风格模板管理:")
        print("    python cli.py style add \"TOEFL\" passage.txt")
        print("    python cli.py style list")
        print("=" * 60)
        sys.exit(1)

    ctrl = LexiController()
    outputs = OutputOptions(
        markdown=bool(args.output_md),
        json=bool(args.output_json),
        csv=bool(args.output_csv),
        html=bool(args.output_html),
        anki=bool(args.output_anki),
    )
    try:
        result = ctrl.classify(
            input_file=args.input,
            categories_path=args.categories,
            stopwords_path=args.stopwords,
            overrides_path=args.overrides,
            outputs=outputs,
            output_dir=".",
        )
        print(f"分类完成！共 {result.total_words} 个单词")
        for fmt, path in sorted(result.output_files.items()):
            print(f"  {fmt}: {path}")
    except FileNotFoundError as e:
        print(f"文件不存在: {e}", file=sys.stderr)
        sys.exit(1)
    except ImportError as e:
        print(f"缺少依赖: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"处理出错: {e}", file=sys.stderr)
        sys.exit(1)


def _handle_story_command(ctrl, argv):
    parser = build_story_parser()
    args = parser.parse_args(argv)
    _validate_story_args(args)

    if args.api_key:
        ctrl.config.api_key = args.api_key
    if args.api_base_url:
        ctrl.config.api_base_url = args.api_base_url
    if args.model:
        ctrl.config.model = args.model
    if args.api_config:
        ctrl.load_config(args.api_config)

    try:
        word_list = None
        if args.words:
            word_list = [w.strip() for w in args.words.split(",") if w.strip()]
        result = ctrl.generate_story(
            input_json=args.input,
            output_dir=os.path.dirname(os.path.abspath(args.output)) or ".",
            word_list=word_list,
            count=args.count,
            strategy=args.strategy,
            length=args.length,
            language=args.language,
            style=args.style,
        )
        story_path = os.path.join(
            os.path.dirname(os.path.abspath(args.output)) or ".",
            os.path.splitext(os.path.basename(args.input))[0] + "_story.md",
        )
        print(f"短文已生成: {story_path}")
        print(f"  模型: {result.model}")
        total = len(result.words_used) + len(result.words_missed)
        print(f"  已使用: {len(result.words_used)}/{total}")
        if result.words_missed:
            print(f"  未使用: {', '.join(result.words_missed)}")
        print(f"  短文词数: {result.word_count}")
    except FileNotFoundError as e:
        print(f"文件不存在: {e}", file=sys.stderr)
        sys.exit(1)
    except ImportError as e:
        print(f"缺少依赖: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"配置错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"生成出错: {e}", file=sys.stderr)
        sys.exit(1)


def _handle_config_command(ctrl, argv):
    parser = build_config_parser()
    args = parser.parse_args(argv)

    if args.api_config:
        ctrl.load_config(args.api_config)

    if args.show:
        config = ctrl.config
        print(f"API Base URL: {config.api_base_url}")
        print(f"模型: {config.model}")
        if config.api_key:
            print(f"API 密钥: {config.api_key[:8]}...")
        else:
            print("API 密钥: (未设置)")
        return

    changed = False
    if args.api_key:
        ctrl.config.api_key = args.api_key
        changed = True
    if args.api_base_url:
        ctrl.config.api_base_url = args.api_base_url
        changed = True
    if args.model:
        ctrl.config.model = args.model
        changed = True

    if changed:
        saved_path = ctrl.save_config(args.api_config)
        print(f"配置已保存: {saved_path}")
    else:
        _config_interactive(ctrl)


def _config_interactive(ctrl):
    config = ctrl.config
    print("Lexi API 配置（按回车保留当前值）")
    api_key = input(f"API 密钥 [{_mask_key(config.api_key)}]: ").strip()
    if api_key:
        config.api_key = api_key
    api_base = input(f"API Base URL [{config.api_base_url}]: ").strip()
    if api_base:
        config.api_base_url = api_base
    model = input(f"模型 [{config.model}]: ").strip()
    if model:
        config.model = model
    saved_path = ctrl.save_config()
    print(f"配置已保存: {saved_path}")


def _handle_style_command(ctrl, argv):
    parser = argparse.ArgumentParser(description="Lexi: 风格模板管理")
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", help="从参考文本文件添加风格模板")
    add_p.add_argument("name", help="风格名称")
    add_p.add_argument("file", help="参考文本文件路径")
    add_p.add_argument("--description", default="", help="风格描述")
    add_p.add_argument("--source", default="", help="来源（如 'TOEFL iBT Reading'）")

    sub.add_parser("list", help="列出所有风格模板")

    show_p = sub.add_parser("show", help="显示风格模板内容")
    show_p.add_argument("name", help="风格名称")

    del_p = sub.add_parser("delete", help="删除风格模板")
    del_p.add_argument("name", help="风格名称")

    analyze_p = sub.add_parser("analyze", help="重新分析已有风格模板的量化特征")
    analyze_p.add_argument("name", help="风格名称")

    args = parser.parse_args(argv)

    if args.command == "add":
        if not os.path.exists(args.file):
            print(f"文件不存在: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            body = f.read()
        ctrl.styles.add_style(args.name, body, args.description, args.source)
        print(f"风格 '{args.name}' 已添加")

    elif args.command == "list":
        styles = ctrl.styles.list_styles()
        if not styles:
            print("(无风格模板)")
            return
        print(f"{'Name':<20} {'Description':<30} {'Source':<20}")
        print("-" * 70)
        for s in styles:
            desc = s.description[:28] + ".." if len(s.description) > 30 else s.description
            src = s.source[:18] + ".." if len(s.source) > 20 else s.source
            print(f"{s.name:<20} {desc:<30} {src:<20}")

    elif args.command == "show":
        try:
            s = ctrl.styles.get_style(args.name)
            print(f"Name:        {s.name}")
            print(f"Description: {s.description}")
            print(f"Source:      {s.source}")
            print()
            _print_profile(s.profile)
            print(f"\n--- body ({len(s.body)} chars) ---")
            print(s.body)
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    elif args.command == "delete":
        try:
            ctrl.styles.delete_style(args.name)
            print(f"风格 '{args.name}' 已删除")
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    elif args.command == "analyze":
        try:
            s = ctrl.styles.analyze_style(args.name)
            print(f"风格 '{s.name}' 已重新分析：")
            _print_profile(s.profile)
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            sys.exit(1)


def _validate_story_args(args):
    if not os.path.exists(args.input):
        print(f"文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)
    if args.count is not None and (args.count < 10 or args.count > 50):
        print(f"--count 必须在 10-50 之间，当前: {args.count}", file=sys.stderr)
        sys.exit(1)


def _mask_key(key: str) -> str:
    if not key:
        return "(未设置)"
    return key[:8] + "..." if len(key) > 8 else "***"


def _print_profile(profile):
    if profile.avg_sentence_length <= 0:
        print("(未分析)")
        return
    print("风格量化特征:")
    print(f"  平均词长:           {profile.avg_word_length:.1f} 字符")
    print(f"  型例比 (TTR):       {profile.type_token_ratio:.2f}")
    if profile.cefr_distribution:
        cefr_str = ", ".join(
            f"{lvl}:{pct*100:.0f}%" for lvl, pct in sorted(profile.cefr_distribution.items())
        )
        print(f"  CEFR 分布:          {cefr_str}")
    print(f"  平均句长:           {profile.avg_sentence_length:.1f} 词")
    print(f"  句长方差 (σ):       {profile.sentence_length_std:.1f}")
    print(f"  被动语态比例:       {profile.passive_voice_ratio*100:.0f}%")
    print(f"  Flesch 阅读易度:    {profile.flesch_reading_ease:.1f}")
    print(f"  Flesch-Kincaid 年级:{profile.flesch_kincaid_grade:.1f}")
    print(f"  名物化比例:         {profile.nominalization_ratio*100:.0f}%")
    print(f"  修饰词密度:         {profile.modifier_density:.2f}")
    print(f"  实词密度:           {profile.lexical_density:.2f}")
    print(f"  从属连词比 (/句):   {profile.subordination_ratio:.1f}")
    print(f"  并列连词比 (/句):   {profile.coordination_ratio:.1f}")
    print(f"  过渡词密度 (/100词):{profile.transition_density:.1f}")
    print(f"  代词密度:           {profile.pronoun_density*100:.0f}%")


def _handle_exercise_command(ctrl, argv):
    parser = argparse.ArgumentParser(description="Lexi: AI 练习生成")
    parser.add_argument("input", help="已分类的 JSON 文件路径")
    parser.add_argument("--type", choices=["cloze", "choice", "definition"], default="cloze",
                        help="练习类型 (默认: cloze)")
    parser.add_argument("--count", type=int, default=10, help="题目数量 (默认: 10)")
    parser.add_argument("--words", help="手动指定词汇，逗号分隔")
    parser.add_argument("--output", default="exercise.md", help="输出 Markdown 文件")
    args = parser.parse_args(argv)

    if not os.path.exists(args.input):
        print(f"文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    from lexi.story import _load_word_infos_from_json
    from lexi.exercises import ExerciseGenerator

    word_infos = _load_word_infos_from_json(args.input)
    if not word_infos:
        print("未找到分类词汇，请先运行分类", file=sys.stderr)
        sys.exit(1)

    if args.words:
        words = [w.strip() for w in args.words.split(",") if w.strip()]
    else:
        from lexi.story import StoryGenerator
        gen = StoryGenerator(ctrl.config)
        words = gen.select_words(word_infos, count=min(args.count, 20), strategy="balanced")

    ex_gen = ExerciseGenerator(ctrl.config)
    if args.type == "cloze":
        result = ex_gen.generate_cloze(words, word_infos, count=args.count)
    elif args.type == "choice":
        result = ex_gen.generate_choice(words, word_infos, count=args.count)
    else:
        result = ex_gen.generate_definitions(words, word_infos)

    lines = [f"# {result.prompt}\n"]
    for i, item in enumerate(result.items, 1):
        if result.type == "cloze":
            lines.append(f"{i}. {item.sentence}")
            lines.append(f"   答案: **{item.correct}**\n")
        elif result.type == "choice":
            lines.append(f"{i}. {item.sentence}")
            for j, opt in enumerate(item.options):
                mark = " ✓" if opt == item.correct else ""
                lines.append(f"   {chr(65+j)}. {opt}{mark}")
            lines.append("")
        elif result.type == "definition":
            lines.append(f"{i}. {item.definition}")
            lines.append(f"   答案: **{item.word}**\n")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"练习已生成: {args.output} ({len(result.items)} 题)")


def _handle_plan_command(ctrl, argv):
    parser = argparse.ArgumentParser(description="Lexi: 学习计划管理")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show", help="查看今日计划")
    create_p = sub.add_parser("create", help="创建学习计划")
    create_p.add_argument("input", help="已分类的 JSON 文件路径")
    create_p.add_argument("--cefr", default="B2", choices=["A1","A2","B1","B2","C1","C2"], help="目标等级")
    create_p.add_argument("--daily", type=int, default=20, help="每日词数")
    args = parser.parse_args(argv)

    from lexi.planner import PlanGenerator

    if args.cmd == "create":
        if not os.path.exists(args.input):
            print(f"文件不存在: {args.input}", file=sys.stderr)
            sys.exit(1)
        from lexi.story import _load_word_infos_from_json
        from lexi.learned import LearnedDB
        word_infos = _load_word_infos_from_json(args.input)
        pg = PlanGenerator()
        db = LearnedDB()
        plan = pg.create_plan(word_infos, db, target_cefr=args.cefr, daily_count=args.daily)
        p = pg.get_progress()
        print(f"计划已创建: {p['total_days']} 天, {p['total_words']} 词, 目标 CEFR {args.cefr}")
    else:
        pg = PlanGenerator()
        today = pg.get_today()
        if not today:
            print("暂无计划。创建: python cli.py plan create output.json --cefr B2")
            return
        print(f"今日 ({today.date}) 计划: {len(today.words)} 词")
        for w in today.words[:20]:
            print(f"  {w}")
        if len(today.words) > 20:
            print(f"  ... 等 {len(today.words)} 词")


if __name__ == "__main__":
    main()
