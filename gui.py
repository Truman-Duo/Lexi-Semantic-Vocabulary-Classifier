#!/usr/bin/env python3
"""Lexi GUI — Flet view layer. All logic lives in lexi.gui_app.LexiApp."""

import os
import sys

import flet as ft

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lexi.gui_app import LexiApp

C = {
    "bg_base": "#1a1b1e", "bg_panel": "#212327", "bg_card": "#282a2f",
    "bg_input": "#1e1f23", "border": "#33353b",
    "text_primary": "#e4e5e8", "text_body": "#c5c6ca",
    "text_muted": "#8b8d94", "text_dim": "#5f6168",
    "accent": "#4a90d9", "green": "#5a9e6f",
}

STRATEGY_LABELS = ["各类别均衡", "高频优先", "随机选取", "按子类比例"]
STRATEGY_KEYS = ["balanced", "top_frequency", "random", "stratified"]
DENSITY_LABELS = ["短篇 (3次/词)", "中篇 (4次/词)", "长篇 (5次/词)"]
DENSITY_KEYS = ["short", "medium", "long"]
COUNT_OPTIONS = ["10", "15", "20", "25", "30", "40", "50"]


def main(page: ft.Page):
    # ── Page setup ──
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = C["bg_base"]
    page.padding = 0
    page.window.width = 860
    page.window.height = 800
    page.window.min_width = 700
    page.window.min_height = 600
    page.title = "Lexi v3.0"

    _DEBUG = getattr(sys, "_lexi_debug", False)

    def _dbg(msg):
        if _DEBUG:
            import datetime
            ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{ts}] {msg}")

    app = LexiApp()

    # ── Widget factories ─────────────────────────────────────

    def _mk_field(val, readonly=True):
        return ft.TextField(value=val, read_only=readonly, bgcolor=C["bg_input"],
                            border_color=C["border"], border_radius=4, dense=True,
                            text_size=13, color=C["text_body"])

    def _mk_dropdown(value, options):
        return ft.Dropdown(
            value=value, options=[ft.dropdown.Option(o) for o in options],
            bgcolor=C["bg_input"], border_color=C["border"], border_radius=4,
            dense=True, text_size=13, color=C["text_body"],
        )

    def _mk_chip(label, active):
        def toggle(e):
            d = e.control.data
            d["active"] = not d["active"]
            e.control.bgcolor = C["accent"] if d["active"] else C["bg_input"]
            e.control.border = ft.Border.all(1, C["accent"] if d["active"] else C["border"])
            e.control.content.color = C["text_primary"] if d["active"] else C["text_muted"]
            e.control.update()
            _sync_format_flags()

        return ft.Container(
            content=ft.Text(label, size=12, weight=ft.FontWeight.W_500,
                            color=C["text_primary"] if active else C["text_muted"]),
            padding=ft.Padding(6, 14, 6, 14), border_radius=14,
            bgcolor=C["accent"] if active else C["bg_input"],
            border=ft.Border.all(1, C["accent"] if active else C["border"]),
            data={"active": active, "label": label}, on_click=toggle,
        )

    def _mk_btn(label, on_click, bg, fg, size=13):
        return ft.FilledButton(
            content=label, on_click=on_click,
            style=ft.ButtonStyle(bgcolor=bg, color=fg,
                                 shape=ft.RoundedRectangleBorder(radius=4),
                                 padding=ft.Padding(20, 12, 20, 12) if size > 13 else ft.Padding(12, 8, 12, 8),
                                 text_style=ft.TextStyle(size=size, weight=ft.FontWeight.W_600 if size > 13 else ft.FontWeight.W_500)),
        )

    def _mk_outline_btn(label, on_click, fg):
        return ft.OutlinedButton(
            content=label, on_click=on_click,
            style=ft.ButtonStyle(color=fg, side=ft.BorderSide(1, fg),
                                 shape=ft.RoundedRectangleBorder(radius=4),
                                 text_style=ft.TextStyle(size=12)),
        )

    def _mk_card(title, body):
        return ft.Container(
            content=ft.Column([ft.Text(title, size=12, weight=ft.FontWeight.W_600, color=C["text_dim"]), body], spacing=8),
            padding=ft.Padding(20, 16, 20, 16), bgcolor=C["bg_card"],
            border=ft.Border.all(1, C["border"]), border_radius=6,
        )

    def _mk_form_row(label, field, is_dir=False):
        def browse(_):
            _dbg(f"浏览: {'目录' if is_dir else '文件'} 对话框打开...")
            import tkinter.filedialog
            if is_dir:
                p = tkinter.filedialog.askdirectory(title="选择输出目录")
            else:
                p = tkinter.filedialog.askopenfilename(title="选择文件")
            if p:
                _dbg(f"浏览: 选择了 {p}")
                field.value = p
                field.update()
                if is_dir:
                    app.output_path = p
            else:
                _dbg("浏览: 取消")

        return ft.Row([
            ft.Text(label, width=70, size=13, color=C["text_muted"]),
            field,
            ft.OutlinedButton(content="浏览", on_click=browse,
                              style=ft.ButtonStyle(color=C["text_muted"], side=ft.BorderSide(1, C["border"]),
                                                   shape=ft.RoundedRectangleBorder(radius=4),
                                                   text_style=ft.TextStyle(size=12))),
        ], spacing=10)

    # ── Widgets ──────────────────────────────────────────────

    input_var = _mk_field("")
    cat_var = _mk_field(os.path.join(app.output_dir, "data", "categories_full.json"))
    stop_var = _mk_field(os.path.join(app.output_dir, "data", "stopwords.txt"))
    over_var = _mk_field("")
    outdir_var = _mk_field(app.output_dir, readonly=False)

    chips = [
        _mk_chip("Markdown", True), _mk_chip("JSON", True),
        _mk_chip("CSV", True), _mk_chip("HTML浏览器", True), _mk_chip("Anki牌组", False),
    ]

    story_count = _mk_dropdown("20", COUNT_OPTIONS)
    story_strategy = _mk_dropdown("各类别均衡", STRATEGY_LABELS)
    story_density = _mk_dropdown("中篇 (4次/词)", DENSITY_LABELS)
    story_style = _mk_dropdown("无", ["无"])
    story_words = ft.TextField(
        value="", hint_text="逗号分隔，留空则自动选择",
        bgcolor=C["bg_input"], border_color=C["border"], border_radius=4, dense=True,
        text_size=13, color=C["text_body"], hint_style=ft.TextStyle(color=C["text_dim"], size=12),
    )

    progress_bar = ft.ProgressBar(value=0, bgcolor=C["bg_input"], color=C["accent"], bar_height=4)
    progress_pct = ft.Text("0%", size=12, color=C["text_dim"])
    status_text = ft.Text("就绪", size=12, color=C["text_body"])
    console = ft.ListView(expand=True, spacing=2, padding=10, auto_scroll=True)

    run_btn = _mk_btn("▶  开始分类", lambda _: _on_run(), C["accent"], "#ffffff", 15)
    story_btn = _mk_outline_btn("生成短文", lambda _: _on_story(), C["green"])
    story_btn.disabled = True
    open_output_btn = _mk_outline_btn("打开输出文件夹", lambda _: _open_output(), C["text_muted"])
    open_output_btn.disabled = True
    open_story_btn = _mk_outline_btn("打开短文文件", lambda _: _open_story(), C["text_muted"])
    open_story_btn.disabled = True

    story_ctrls = [story_count, story_strategy, story_density, story_style, story_words, story_btn]

    # ── Sync helpers ─────────────────────────────────────────

    def _sync_format_flags():
        for ch in chips:
            d = ch.data
            setattr(app, {
                "Markdown": "opt_md", "JSON": "opt_json", "CSV": "opt_csv",
                "HTML浏览器": "opt_html", "Anki牌组": "opt_anki",
            }.get(d["label"], ""), d["active"])

    def _sync_inputs():
        app.input_file = input_var.value
        app.categories_path = cat_var.value or "data/categories_full.json"
        app.stopwords_path = stop_var.value or "data/stopwords.txt"
        app.overrides_path = over_var.value or None
        app.output_path = outdir_var.value or "."

    def _sync_story_params():
        app.story_count = int(story_count.value)
        app.story_strategy = STRATEGY_KEYS[STRATEGY_LABELS.index(story_strategy.value)]
        app.story_length = DENSITY_KEYS[DENSITY_LABELS.index(story_density.value)]
        sn = story_style.value
        app.story_style = None if sn == "无" or not sn else sn
        app.story_words = story_words.value

    # ── Wire app callbacks ───────────────────────────────────

    def _log(msg, tag=""):
        if _DEBUG:
            print(f"[dbg] {msg}")
        color_map = {"hl": C["accent"], "dim": C["text_dim"], "ok": C["green"]}
        c = color_map.get(tag, C["text_muted"])
        console.controls.append(ft.Text(msg, size=12, color=c, font_family="monospace"))
        page.update()

    def _progress(pct):
        progress_bar.value = pct
        progress_pct.value = f"{int(pct*100)}%"
        page.update()

    def _status(m):
        status_text.value = m
        page.update()

    def _toggle_story(on):
        story_section.visible = on
        story_btn.disabled = not on
        for c in story_ctrls[:5]:
            try:
                c.disabled = not on
            except Exception:
                pass
        page.update()

    def _on_classify_done(jp):
        names = app.ctrl.styles.style_names()
        story_style.options = [ft.dropdown.Option("无")] + [ft.dropdown.Option(n) for n in names]
        story_style.value = "无"
        _toggle_story(True)
        _ui_done()

    def _on_story_result(result):
        t = len(result.words_used) + len(result.words_missed)
        _log(f"模型: {result.model}  |  目标: {t}词  |  已用: {len(result.words_used)}词  |  短文: {result.word_count}词", "dim")
        if result.words_missed:
            _log(f"未使用: {', '.join(result.words_missed)}", "dim")
        _log("", "dim")
        for line in result.passage.split("\n"):
            _log(line, "dim")
        _log("─" * 36, "dim")
        _log(f"短文已保存: {app.last_story_md}", "ok")
        open_story_btn.disabled = False
        _ui_done()

    def _ui_done():
        run_btn.disabled = False
        open_output_btn.disabled = False
        page.update()

    app.on_log = _log
    app.on_progress = _progress
    app.on_status = _status
    app.on_story_toggle = _toggle_story
    app.on_classify_done = _on_classify_done
    app.on_story_result = _on_story_result
    app.on_classify_error = lambda m: (_log(f"错误: {m}", "ok"), _ui_done())
    app.on_story_error = lambda m: (_log(f"错误: {m}", "ok"), _ui_done())

    # ── Button handlers ──────────────────────────────────────

    def _on_run():
        _dbg("→ 开始分类")
        _sync_inputs()
        _dbg(f"  输入文件: {app.input_file}")
        _dbg(f"  输出目录: {app.output_path}")
        _sync_format_flags()
        _dbg(f"  格式: md={app.opt_md} json={app.opt_json} csv={app.opt_csv} html={app.opt_html} anki={app.opt_anki}")
        console.controls.clear()
        _toggle_story(False)
        open_output_btn.disabled = True
        open_story_btn.disabled = True
        run_btn.disabled = True
        page.update()
        app.run_classify()
        _dbg("← 分类线程已启动")

    def _on_story():
        _sync_story_params()
        _dbg(f"→ 生成短文: count={app.story_count} strategy={app.story_strategy} length={app.story_length} style={app.story_style} words={app.story_words[:50]}")
        open_story_btn.disabled = True
        run_btn.disabled = True
        page.update()
        app.run_story()
        _dbg("← 短文线程已启动")

    def _open_output():
        if os.path.isdir(app.output_path):
            os.startfile(app.output_path)

    def _open_story():
        if app.last_story_md and os.path.exists(app.last_story_md):
            os.startfile(app.last_story_md)

    # ── API Dialog ───────────────────────────────────────────

    def _show_api_dialog(_=None):
        _dbg("→ 打开 API 配置弹窗...")
        try:
            cfg = app.ctrl.config
            _dbg(f"  当前: url={cfg.api_base_url} model={cfg.model} key={'***' if cfg.api_key else '(空)'}")
            api_url = ft.TextField(value=cfg.api_base_url, label="API Base URL",
                                   bgcolor=C["bg_input"], border_color=C["border"],
                                   border_radius=4, dense=True, text_size=13, color=C["text_body"])
            api_key = ft.TextField(value=cfg.api_key, label="API 密钥", password=True,
                                   can_reveal_password=True, bgcolor=C["bg_input"],
                                   border_color=C["border"], border_radius=4, dense=True,
                                   text_size=13, color=C["text_body"])
            model_name = ft.TextField(value=cfg.model, label="模型名称",
                                      bgcolor=C["bg_input"], border_color=C["border"],
                                      border_radius=4, dense=True, text_size=13, color=C["text_body"])

            def save_dlg(_):
                app.save_api_config(api_key.value, api_url.value, model_name.value)
                _log(f"[API] 配置已保存 ({api_url.value}, {model_name.value})", "dim")
                _close_dlg()

            dlg = ft.AlertDialog(
                title=ft.Text("API 配置", color=C["text_primary"]),
                content=ft.Column([api_url, api_key, model_name], spacing=12, width=380),
                actions=[
                    ft.TextButton("取消", on_click=lambda _: _close_dlg()),
                    ft.FilledButton("保存", on_click=save_dlg, style=ft.ButtonStyle(bgcolor=C["green"], color="#ffffff")),
                ],
                bgcolor=C["bg_card"],
            )
            page.show_dialog(dlg)
            _dbg("← API 配置弹窗已打开")
        except Exception as ex:
            _dbg(f"✗ API 配置弹窗异常: {ex}")
            import traceback
            traceback.print_exc()

    def _close_dlg():
        page.pop_dialog()
        page.update()

    def _show_style_info():
        _dbg("→ 打开风格模板弹窗...")
        try:
            names = app.ctrl.styles.style_names()
            _dbg(f"  风格列表: {names}")
        except Exception as ex:
            _dbg(f"  获取风格列表异常: {ex}")
            names = []
        if names:
            body = ft.Column([ft.Text(f"• {n}", size=13, color=C["text_body"]) for n in names], spacing=4)
        else:
            body = ft.Text("暂无风格模板\n\n使用 CLI 添加: python cli.py style add <name> <file>", size=13, color=C["text_muted"])
        try:
            dlg = ft.AlertDialog(
                title=ft.Text("风格模板", color=C["text_primary"]),
                content=ft.Column([body,
                    ft.Text("", size=8),
                    ft.Text("CLI 管理: python cli.py style add/list/delete", size=11, color=C["text_dim"]),
                ], spacing=6, width=300),
                actions=[ft.TextButton("关闭", on_click=lambda _: _close_dlg())],
                bgcolor=C["bg_card"],
            )
            page.show_dialog(dlg)
            _dbg("← 风格模板弹窗已打开")
        except Exception as ex:
            _dbg(f"✗ 风格模板弹窗异常: {ex}")
            import traceback
            traceback.print_exc()

    # ── Sidebar ──────────────────────────────────────────────

    sidebar = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=80, min_extended_width=180,
        bgcolor=C["bg_panel"], indicator_color=C["accent"],
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.CATEGORY_OUTLINED, selected_icon=ft.Icons.CATEGORY, label="词汇分类"),
            ft.NavigationRailDestination(icon=ft.Icons.EDIT_NOTE_OUTLINED, selected_icon=ft.Icons.EDIT_NOTE, label="AI 短文生成"),
            ft.NavigationRailDestination(icon=ft.Icons.QUIZ_OUTLINED, selected_icon=ft.Icons.QUIZ, label="AI 练习"),
            ft.NavigationRailDestination(icon=ft.Icons.MENU_BOOK_OUTLINED, selected_icon=ft.Icons.MENU_BOOK, label="我的词库"),
            ft.NavigationRailDestination(icon=ft.Icons.CALENDAR_TODAY_OUTLINED, selected_icon=ft.Icons.CALENDAR_TODAY, label="每日复习"),
            ft.NavigationRailDestination(icon=ft.Icons.TRENDING_UP_OUTLINED, selected_icon=ft.Icons.TRENDING_UP, label="学习计划"),
            ft.NavigationRailDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="API 配置"),
            ft.NavigationRailDestination(icon=ft.Icons.STYLE_OUTLINED, selected_icon=ft.Icons.STYLE, label="风格模板"),
        ],
        on_change=lambda e: _on_nav(e),
    )

    def _on_nav(e):
        idx = e.control.selected_index
        if idx == 3:
            _show_lexicon()
        elif idx == 4:
            _show_review()
        elif idx == 5:
            _show_plan()
        elif idx == 1:
            _show_page(0)
            if story_section.visible:
                main_col.scroll_to(offset=-1, duration=300)
        elif idx == 0:
            _show_page(0)
        elif idx == 6:
            _show_api_dialog()
        elif idx == 7:
            _show_style_info()
        elif idx == 2:
            _show_exercise()
        e.control.selected_index = 0
        page.update()

    def _show_page(n):
        main_page.visible = (n == 0)
        lexicon_page.visible = (n == 1)
        review_page.visible = (n == 2)
        exercise_page.visible = (n == 3)
        plan_page.visible = (n == 4)
        titles = ["词汇分类", "我的词库", "每日复习", "AI 练习", "学习计划"]
        header_title.value = titles[n] if n < len(titles) else ""
        page.update()

    def _show_lexicon():
        _build_lexicon()
        _show_page(1)

    def _show_review():
        _build_review()
        _show_page(2)

    # ── Story section ────────────────────────────────────────

    story_section = ft.Column([
        _mk_card("AI 短文生成", ft.Column([
            ft.Row([
                ft.Column([ft.Text("词汇数量", size=11, color=C["text_dim"]), story_count], spacing=3),
                ft.Column([ft.Text("选择策略", size=11, color=C["text_dim"]), story_strategy], spacing=3),
                ft.Column([ft.Text("重复密度", size=11, color=C["text_dim"]), story_density], spacing=3),
                ft.Column([ft.Text("风格模板", size=11, color=C["text_dim"]), story_style], spacing=3),
            ], spacing=10),
            ft.Row([story_words, story_btn], spacing=10),
        ], spacing=12)),
    ], visible=False, key="story")

    # ── Main layout ──────────────────────────────────────────

    main_col = ft.Column(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
    main_col.controls = [
        ft.Container(
            content=ft.Row([
                ft.Text("词汇分类", size=15, weight=ft.FontWeight.W_600, color=C["text_primary"]),
                ft.Text("v3.0", size=11, color=C["text_dim"]),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(24, 16, 24, 16), bgcolor=C["bg_panel"],
            border=ft.Border.only(bottom=ft.BorderSide(1, C["border"])),
        ),
        ft.Container(
            content=ft.Column([
                _mk_card("输入设置", ft.Column([
                    _mk_form_row("输入文件", input_var),
                    _mk_form_row("分类词库", cat_var),
                    _mk_form_row("停用词表", stop_var),
                    _mk_form_row("覆盖规则", over_var),
                    _mk_form_row("输出目录", outdir_var, is_dir=True),
                ], spacing=8)),
                _mk_card("输出格式", ft.Row(chips, spacing=6, wrap=True)),
                ft.Container(content=run_btn, padding=ft.Padding(0, 4, 0, 4)),
                _mk_card("进度", ft.Column([
                    ft.Row([progress_bar, progress_pct], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    status_text,
                ], spacing=6)),
                story_section,
                _mk_card("输出日志", ft.Container(content=console, bgcolor=C["bg_base"],
                                                   border=ft.Border.all(1, C["border"]),
                                                   border_radius=4, padding=10, height=160)),
            ], spacing=14),
            padding=ft.Padding(24, 20, 24, 24), expand=True,
        ),
        ft.Container(
            content=ft.Row([
                ft.Row([ft.Container(width=6, height=6, border_radius=3, bgcolor=C["green"]),
                        ft.Text("就绪", size=12, color=C["text_dim"])], spacing=6),
                ft.Row([open_output_btn, open_story_btn], spacing=8),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(24, 10, 24, 10), bgcolor=C["bg_panel"],
            border=ft.Border.only(top=ft.BorderSide(1, C["border"])),
        ),
    ]

    # ── Page containers ──────────────────────────────────────
    header_title = ft.Text("词汇分类", size=15, weight=ft.FontWeight.W_600, color=C["text_primary"])
    main_col.controls[0].content.controls[0] = header_title

    main_page = ft.Column(spacing=0, expand=True)
    main_page.controls = main_col.controls

    lexicon_page = ft.Column(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
    lexicon_page.visible = False
    review_page = ft.Column(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
    review_page.visible = False

    def _build_lexicon():
        stats = app.learned_db.get_stats()
        lv = ft.Column(spacing=8)
        lv.controls.append(ft.Row([
            _lexicon_stat("总计", stats["total"]), _lexicon_stat("已掌握", stats["mastered"]),
            _lexicon_stat("学习中", stats["learning"]), _lexicon_stat("未学", stats["new"])], spacing=12))
        lv.controls.append(ft.Text("", size=4))
        status_filter = ft.Dropdown(value="全部",
            options=[ft.dropdown.Option(o) for o in ["全部", "未学", "学习中", "已掌握"]],
            bgcolor=C["bg_input"], border_color=C["border"], border_radius=4,
            dense=True, text_size=13, color=C["text_body"])
        status_filter.on_select = lambda e: _refresh_lexicon(e.control.value)
        lv.controls.append(ft.Row([ft.Text("筛选:", size=12, color=C["text_dim"]), status_filter], spacing=8))
        lv.controls.append(ft.Text("", size=4))
        lv.controls.append(_lexicon_list("全部"))
        lexicon_page.controls = [
            ft.Container(content=ft.Row([header_title, ft.Text("v3.0", size=11, color=C["text_dim"])],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding(24, 16, 24, 16), bgcolor=C["bg_panel"],
                border=ft.Border.only(bottom=ft.BorderSide(1, C["border"]))),
            ft.Container(content=lv, padding=ft.Padding(24, 20, 24, 24), expand=True),
        ]

    def _lexicon_stat(label, count):
        return ft.Container(content=ft.Column([
            ft.Text(str(count), size=22, weight=ft.FontWeight.W_700, color=C["accent"]),
            ft.Text(label, size=11, color=C["text_dim"])],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            padding=ft.Padding(16, 12, 16, 12), bgcolor=C["bg_card"],
            border=ft.Border.all(1, C["border"]), border_radius=6)

    def _lexicon_list(filter_status):
        words = app.learned_db.get_all(None if filter_status == "全部" else
            {"未学": "new", "学习中": "learning", "已掌握": "mastered"}.get(filter_status))
        if not words:
            return ft.Text("暂无词汇。请先运行词汇分类。", size=13, color=C["text_muted"])
        items = []
        for ws in words[:200]:
            color = {"new": C["text_muted"], "learning": C["accent"], "mastered": C["green"]}.get(ws.status)
            label = {"new": "未学", "learning": "学习中", "mastered": "已掌握"}.get(ws.status)
            items.append(ft.Row([ft.Text(ws.word, size=13, color=C["text_body"], width=150),
                ft.Text(label, size=11, color=color),
                ft.Text(f"复习{ws.review_count}次" if ws.review_count else "", size=11, color=C["text_dim"])], spacing=12))
        return ft.Column(items, spacing=4)

    def _refresh_lexicon(filter_status):
        lv = lexicon_page.controls[1].content
        lv.controls = lv.controls[:4] + [_lexicon_list(filter_status)]
        page.update()

    def _build_review():
        due = app.learned_db.get_due(limit=30)
        lv = ft.Column(spacing=8)
        lv.controls.append(ft.Text(f"今日到期: {len(due)} 词", size=14, weight=ft.FontWeight.W_600, color=C["text_primary"]))
        lv.controls.append(ft.Text("", size=4))
        if not due:
            lv.controls.append(ft.Text("全部完成！没有待复习的词汇。", size=13, color=C["green"]))
        else:
            for ws in due:
                w = ws.word
                lv.controls.append(ft.Container(content=ft.Row([
                    ft.Text(w, size=15, weight=ft.FontWeight.W_500, color=C["text_primary"], width=140),
                    ft.Text(f"间隔{ws.interval}天" if ws.interval else "新词", size=11, color=C["text_dim"], width=55),
                    ft.ElevatedButton("忘了", on_click=lambda _, w=w: _rate(w, "again"), height=30,
                        style=ft.ButtonStyle(bgcolor="#5a3a3a", color="#fff", text_style=ft.TextStyle(size=10))),
                    ft.ElevatedButton("困难", on_click=lambda _, w=w: _rate(w, "hard"), height=30,
                        style=ft.ButtonStyle(bgcolor="#5a4a2a", color="#fff", text_style=ft.TextStyle(size=10))),
                    ft.FilledButton("正常", on_click=lambda _, w=w: _rate(w, "good"), height=30,
                        style=ft.ButtonStyle(bgcolor=C["accent"], color="#fff", text_style=ft.TextStyle(size=10))),
                    ft.FilledButton("简单", on_click=lambda _, w=w: _rate(w, "easy"), height=30,
                        style=ft.ButtonStyle(bgcolor=C["green"], color="#fff", text_style=ft.TextStyle(size=10))),
                ], spacing=6), padding=ft.Padding(8, 6, 8, 6), bgcolor=C["bg_card"],
                    border=ft.Border.all(1, C["border"]), border_radius=6))
        review_page.controls = [
            ft.Container(content=ft.Row([ft.Text("每日复习", size=15, weight=ft.FontWeight.W_600, color=C["text_primary"]),
                           ft.Text("v3.0", size=11, color=C["text_dim"])],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding(24, 16, 24, 16), bgcolor=C["bg_panel"],
                border=ft.Border.only(bottom=ft.BorderSide(1, C["border"]))),
            ft.Container(content=lv, padding=ft.Padding(24, 20, 24, 24), expand=True),
        ]
        page.update()

    def _rate(word, rating):
        app.learned_db.mark_reviewed(word, rating)
        _dbg(f"复习: {word} → {rating}")
        _build_review()

    def _show_exercise():
        _show_page(3)

    # ── Exercise page ────────────────────────────────────────
    exercise_page = ft.Column(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
    exercise_page.visible = False
    exercise_type = ft.Dropdown(value="cloze",
        options=[ft.dropdown.Option("cloze", "完形填空"), ft.dropdown.Option("choice", "选择题"),
                 ft.dropdown.Option("definition", "释义匹配")],
        bgcolor=C["bg_input"], border_color=C["border"], border_radius=4, dense=True, text_size=13, color=C["text_body"])
    exercise_count = ft.Dropdown(value="5",
        options=[ft.dropdown.Option(str(v)) for v in [5, 10, 15, 20]],
        bgcolor=C["bg_input"], border_color=C["border"], border_radius=4, dense=True, text_size=13, color=C["text_body"])
    exercise_result = ft.ListView(spacing=4, expand=True)
    exercise_btn = ft.FilledButton(content="生成练习", on_click=lambda _: _gen_exercise(),
        style=ft.ButtonStyle(bgcolor=C["accent"], color="#fff", shape=ft.RoundedRectangleBorder(radius=4)))
    ex_show_answer = ft.TextButton("显示答案", on_click=lambda _: _toggle_answers(),
                                   style=ft.ButtonStyle(color=C["text_muted"]))

    _ex_answers_visible = [False]

    def _toggle_answers():
        _ex_answers_visible[0] = not _ex_answers_visible[0]
        _build_exercise_page()

    def _gen_exercise():
        if not app.last_output_json:
            _log("请先运行分类", "ok")
            return
        from lexi.story import _load_word_infos_from_json
        from lexi.exercises import ExerciseGenerator
        word_infos = _load_word_infos_from_json(app.last_output_json)
        from lexi.story import StoryGenerator
        sg = StoryGenerator(app.ctrl.config)
        words = sg.select_words(word_infos, count=min(int(exercise_count.value), 20), strategy="balanced")
        eg = ExerciseGenerator(app.ctrl.config)
        t = exercise_type.value
        if t == "cloze":
            result = eg.generate_cloze(words, word_infos, count=int(exercise_count.value))
        elif t == "choice":
            result = eg.generate_choice(words, word_infos, count=int(exercise_count.value))
        else:
            result = eg.generate_definitions(words, word_infos)
        exercise_result.controls.clear()
        for i, item in enumerate(result.items, 1):
            if result.type == "cloze":
                ans = f" **{item.correct}**" if _ex_answers_visible[0] else ""
                exercise_result.controls.append(ft.Text(f"{i}. {item.sentence}{ans}", size=13, color=C["text_body"]))
            elif result.type == "choice":
                exercise_result.controls.append(ft.Text(f"{i}. {item.sentence}", size=13, color=C["text_body"]))
                for j, opt in enumerate(item.options):
                    is_correct = opt == item.correct
                    prefix = f"   {chr(65+j)}. "
                    if _ex_answers_visible[0] and is_correct:
                        exercise_result.controls.append(ft.Text(f"{prefix}{opt} ✓", size=12, color=C["green"]))
                    else:
                        exercise_result.controls.append(ft.Text(f"{prefix}{opt}", size=12, color=C["text_muted"]))
                exercise_result.controls.append(ft.Text("", size=4))
            else:
                defn = item.definition
                word = f" **{item.word}**" if _ex_answers_visible[0] else " ______"
                exercise_result.controls.append(ft.Text(f"{i}. {defn} →{word}", size=13, color=C["text_body"]))
        ex_show_answer.visible = True
        page.update()

    exercise_page.controls = [
        ft.Container(content=ft.Row([header_title, ft.Text("v3.0", size=11, color=C["text_dim"])],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(24, 16, 24, 16), bgcolor=C["bg_panel"],
            border=ft.Border.only(bottom=ft.BorderSide(1, C["border"]))),
        ft.Container(content=ft.Column([
            ft.Row([ft.Text("题型:", size=12, color=C["text_dim"]), exercise_type,
                    ft.Text("数量:", size=12, color=C["text_dim"]), exercise_count,
                    exercise_btn], spacing=10),
            ft.Text("", size=8),
            ft.Row([ex_show_answer]),
            exercise_result,
        ], spacing=4), padding=ft.Padding(24, 20, 24, 24), expand=True),
    ]
    ex_show_answer.visible = False

    def _show_exercise():
        _show_page(3)

    def _show_plan():
        _build_plan()
        _show_page(4)

    # ── Plan page ────────────────────────────────────────────
    plan_page = ft.Column(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
    plan_page.visible = False
    plan_cefr = ft.Dropdown(value="B2", options=[ft.dropdown.Option(o) for o in ["A1","A2","B1","B2","C1","C2"]],
                            bgcolor=C["bg_input"], border_color=C["border"], border_radius=4, dense=True,
                            text_size=13, color=C["text_body"])
    plan_daily = ft.Dropdown(value="20", options=[ft.dropdown.Option(v) for v in ["10","20","30","50"]],
                             bgcolor=C["bg_input"], border_color=C["border"], border_radius=4, dense=True,
                             text_size=13, color=C["text_body"])
    plan_content = ft.ListView(spacing=6, expand=True)

    def _build_plan():
        from lexi.planner import PlanGenerator
        pg = PlanGenerator()
        plan_content.controls.clear()
        if pg.plan.days:
            p = pg.get_progress()
            today = pg.get_today()
            plan_content.controls.append(
                ft.ProgressBar(value=p["pct"]/100, bgcolor=C["bg_input"], color=C["accent"], bar_height=6))
            plan_content.controls.append(ft.Text(
                f"目标 CEFR {pg.plan.target_cefr} | {p['completed_days']}/{p['total_days']} 天 | {p['total_words']} 词",
                size=12, color=C["text_dim"]))
            plan_content.controls.append(ft.Text("", size=4))
            if today:
                plan_content.controls.append(ft.Text("今日计划", size=14, weight=ft.FontWeight.W_600, color=C["text_primary"]))
                for w in today.words[:50]:
                    plan_content.controls.append(ft.Text(f"• {w}", size=13, color=C["text_body"]))
                btn_done = ft.FilledButton("标记完成", on_click=lambda _: _complete_today(pg, today.date),
                    style=ft.ButtonStyle(bgcolor=C["green"], color="#fff", shape=ft.RoundedRectangleBorder(radius=4)))
                plan_content.controls.append(btn_done)
            else:
                plan_content.controls.append(ft.Text("所有计划已完成！", size=13, color=C["green"]))
            plan_content.controls.append(ft.Text("", size=12))
            plan_content.controls.append(ft.Text("全部日程", size=12, weight=ft.FontWeight.W_600, color=C["text_dim"]))
            for d in pg.plan.days:
                mark = "✓" if d.completed else "○"
                color = C["green"] if d.completed else C["text_muted"]
                plan_content.controls.append(ft.Text(f"  {mark} {d.date} — {len(d.words)} 词", size=12, color=color))
        else:
            plan_content.controls.append(ft.Text("暂无学习计划", size=14, color=C["text_muted"]))
            plan_content.controls.append(ft.Text("", size=8))
            plan_content.controls.append(ft.Text("创建计划需要先运行词汇分类，然后选择目标 CEFR 等级和每日词数。", size=12, color=C["text_dim"]))
            plan_content.controls.append(ft.Text("", size=8))
            btn_create = ft.FilledButton("创建计划", on_click=lambda _: _create_plan(),
                style=ft.ButtonStyle(bgcolor=C["accent"], color="#fff", shape=ft.RoundedRectangleBorder(radius=4)))
            plan_content.controls.append(ft.Row([plan_cefr, plan_daily, btn_create], spacing=10))
        plan_page.controls = [
            ft.Container(content=ft.Row([header_title, ft.Text("v3.0", size=11, color=C["text_dim"])],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding(24, 16, 24, 16), bgcolor=C["bg_panel"],
                border=ft.Border.only(bottom=ft.BorderSide(1, C["border"]))),
            ft.Container(content=plan_content, padding=ft.Padding(24, 20, 24, 24), expand=True),
        ]
        page.update()

    def _create_plan():
        if not app.last_output_json:
            _log("请先运行分类", "ok")
            return
        from lexi.story import _load_word_infos_from_json
        from lexi.planner import PlanGenerator
        word_infos = _load_word_infos_from_json(app.last_output_json)
        pg = PlanGenerator()
        pg.create_plan(word_infos, app.learned_db, plan_cefr.value, int(plan_daily.value))
        _build_plan()

    def _complete_today(pg, date_str):
        pg.mark_completed(date_str)
        _build_plan()

    page.add(ft.Row([sidebar, ft.VerticalDivider(width=1, color=C["border"]),
                     ft.Stack([main_page, lexicon_page, review_page, exercise_page, plan_page], expand=True)],
                    expand=True, spacing=0))


if __name__ == "__main__":
    ft.app(target=main)
