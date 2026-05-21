"""Exercise subcommand."""

import argparse, os, sys


def handle_exercise(ctrl, argv):
    parser = argparse.ArgumentParser(description="Lexi: AI 练习生成")
    parser.add_argument("input", help="已分类的 JSON 文件路径")
    parser.add_argument("--type", choices=["cloze","choice","definition"], default="cloze")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--words", help="手动指定词汇，逗号分隔")
    parser.add_argument("--output", default="exercise.md")
    args = parser.parse_args(argv)
    if not os.path.exists(args.input):
        print(f"文件不存在: {args.input}", file=sys.stderr); sys.exit(1)
    from lexi.story import _load_word_infos_from_json
    from lexi.exercises import ExerciseGenerator
    word_infos = _load_word_infos_from_json(args.input)
    if not word_infos: print("未找到分类词汇", file=sys.stderr); sys.exit(1)
    if args.words:
        words = [w.strip() for w in args.words.split(",") if w.strip()]
    else:
        from lexi.story import StoryGenerator
        words = StoryGenerator(ctrl.config).select_words(word_infos, count=min(args.count, 20))
    eg = ExerciseGenerator(ctrl.config)
    t = args.type
    result = eg.generate_cloze(words, word_infos, count=args.count) if t == "cloze" else \
             eg.generate_choice(words, word_infos, count=args.count) if t == "choice" else \
             eg.generate_definitions(words, word_infos)
    lines = [f"# {result.prompt}\n"]
    for i, item in enumerate(result.items, 1):
        if result.type == "cloze":
            lines.append(f"{i}. {item.sentence}\n   答案: **{item.correct}**\n")
        elif result.type == "choice":
            lines.append(f"{i}. {item.sentence}")
            for j, opt in enumerate(item.options):
                lines.append(f"   {chr(65+j)}. {opt}{' ✓' if opt==item.correct else ''}")
            lines.append("")
        elif result.type == "definition":
            lines.append(f"{i}. {item.definition}\n   答案: **{item.word}**\n")
    with open(args.output, "w", encoding="utf-8") as f: f.write("\n".join(lines) + "\n")
    print(f"练习已生成: {args.output} ({len(result.items)} 题)")
