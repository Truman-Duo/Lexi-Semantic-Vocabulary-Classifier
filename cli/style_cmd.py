"""Style subcommand."""

import argparse, os, sys


def handle_style(ctrl, argv):
    parser = argparse.ArgumentParser(description="Lexi: 风格模板管理")
    sub = parser.add_subparsers(dest="command", required=True)
    add_p = sub.add_parser("add"); add_p.add_argument("name"); add_p.add_argument("file")
    add_p.add_argument("--description", default=""); add_p.add_argument("--source", default="")
    sub.add_parser("list")
    show_p = sub.add_parser("show"); show_p.add_argument("name")
    del_p = sub.add_parser("delete"); del_p.add_argument("name")
    analyze_p = sub.add_parser("analyze"); analyze_p.add_argument("name")
    args = parser.parse_args(argv)

    if args.command == "add":
        if not os.path.exists(args.file):
            print(f"文件不存在: {args.file}", file=sys.stderr); sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f: body = f.read()
        ctrl.styles.add_style(args.name, body, args.description, args.source)
        print(f"风格 '{args.name}' 已添加")
    elif args.command == "list":
        styles = ctrl.styles.list_styles()
        if not styles: print("(无风格模板)"); return
        print(f"{'Name':<20} {'Description':<30} {'Source':<20}")
        print("-" * 70)
        for s in styles:
            d = s.description[:28]+".." if len(s.description)>30 else s.description
            src = s.source[:18]+".." if len(s.source)>20 else s.source
            print(f"{s.name:<20} {d:<30} {src:<20}")
    elif args.command == "show":
        try:
            s = ctrl.styles.get_style(args.name)
            print(f"Name: {s.name}\nDescription: {s.description}\nSource: {s.source}\n")
            _print_profile(s.profile)
            print(f"\n--- body ({len(s.body)} chars) ---\n{s.body}")
        except FileNotFoundError as e: print(e, file=sys.stderr); sys.exit(1)
    elif args.command == "delete":
        try: ctrl.styles.delete_style(args.name); print(f"风格 '{args.name}' 已删除")
        except FileNotFoundError as e: print(e, file=sys.stderr); sys.exit(1)
    elif args.command == "analyze":
        try: s = ctrl.styles.analyze_style(args.name); print(f"风格 '{s.name}' 已重新分析："); _print_profile(s.profile)
        except FileNotFoundError as e: print(e, file=sys.stderr); sys.exit(1)


def _print_profile(profile):
    if profile.avg_sentence_length <= 0: print("(未分析)"); return
    print("风格量化特征:")
    print(f"  平均词长:           {profile.avg_word_length:.1f} 字符")
    print(f"  型例比 (TTR):       {profile.type_token_ratio:.2f}")
    if profile.cefr_distribution:
        cefr_str = ", ".join(f"{lvl}:{pct*100:.0f}%" for lvl, pct in sorted(profile.cefr_distribution.items()))
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
