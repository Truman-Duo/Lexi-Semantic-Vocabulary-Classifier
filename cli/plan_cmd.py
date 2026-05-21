"""Plan subcommand."""

import argparse, os, sys


def handle_plan(ctrl, argv):
    parser = argparse.ArgumentParser(description="Lexi: 学习计划管理")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show")
    create_p = sub.add_parser("create")
    create_p.add_argument("input")
    create_p.add_argument("--cefr", default="B2", choices=["A1","A2","B1","B2","C1","C2"])
    create_p.add_argument("--daily", type=int, default=20)
    args = parser.parse_args(argv)

    from lexi.planner import PlanGenerator
    if args.cmd == "create":
        if not os.path.exists(args.input): print(f"文件不存在: {args.input}", file=sys.stderr); sys.exit(1)
        from lexi.story import _load_word_infos_from_json
        from lexi.learned import LearnedDB
        pg = PlanGenerator()
        pg.create_plan(_load_word_infos_from_json(args.input), LearnedDB(), args.cefr, args.daily)
        p = pg.get_progress()
        print(f"计划已创建: {p['total_days']} 天, {p['total_words']} 词, 目标 CEFR {args.cefr}")
    else:
        pg = PlanGenerator()
        today = pg.get_today()
        if not today: print("暂无计划"); return
        print(f"今日 ({today.date}) 计划: {len(today.words)} 词")
        for w in today.words[:20]: print(f"  {w}")
        if len(today.words) > 20: print(f"  ... 等 {len(today.words)} 词")
