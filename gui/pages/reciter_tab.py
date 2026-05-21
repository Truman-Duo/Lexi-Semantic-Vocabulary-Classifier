"""背诵器 Tab — 多视图：主菜单 → 背诵/AI练习 Session."""

import random
import time
import flet as ft
from ..widgets import C, mk_dropdown
from lexi.reciter import ReciterEngine
from lexi.wordbook import WordBookManager

CARD_MODES = {"自测": 1, "词义选择": 2, "中文选词": 3, "智能模式": 4}


def build_reciter_tab(app, page: ft.Page) -> ft.Column:
    engine = ReciterEngine(app.learned_db)
    wbm = WordBookManager()
    active_book = ["全部词汇"]
    tab_content = ft.Column()

    # ═══════════ View 0: Main Menu ═══════════
    def _dash_row():
        s = app.learned_db.get_stats()
        return ft.Row([
            _dash("词汇总量", s["total"]), _dash("已掌握", s["mastered"]),
            _dash("学习中", s["learning"]), _dash("今日到期", s.get("due_today", 0)),
        ], spacing=12)

    def _dash(label, count):
        return ft.Container(
            content=ft.Column([ft.Text(str(count), size=18, weight=ft.FontWeight.W_700, color=C["accent"]),
                              ft.Text(label, size=10, color=C["text_dim"])],
                             horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            padding=ft.Padding(10, 6, 10, 6), bgcolor=C["bg_card"],
            border=ft.Border.all(1, C["border"]), border_radius=6, expand=True)

    # Wordbook selector
    book_dd = ft.Dropdown(value="全部词汇",
        options=[ft.dropdown.Option("全部词汇")],
        bgcolor=C["bg_input"], border_color=C["border"], border_radius=4,
        dense=True, text_size=13, color=C["text_body"], width=180,
        on_select=lambda e: _on_book_change())
    book_info = ft.Text("", size=11, color=C["text_dim"])

    def _refresh_book():
        books = wbm.list_books()
        book_dd.options = [ft.dropdown.Option("全部词汇")] + [ft.dropdown.Option(b) for b in books]
        book_dd.value = active_book[0]
        count = len(app.learned_db.words) if active_book[0] == "全部词汇" else (
            len(wbm.load_book(active_book[0]).words) if active_book[0] in books else 0)
        book_info.value = f"{count} 词"

    def _on_book_change():
        active_book[0] = book_dd.value
        _refresh_book()

    _refresh_book()

    # Settings
    count_field = ft.TextField(value="20", keyboard_type=ft.KeyboardType.NUMBER,
        bgcolor=C["bg_input"], border_color=C["border"], border_radius=4,
        dense=True, text_size=13, color=C["text_body"], width=70)
    strategy_dd = ft.Dropdown(value="复习优先",
        options=[ft.dropdown.Option(o) for o in ["复习优先", "新词优先", "混合出词", "智能出词"]],
        bgcolor=C["bg_input"], border_color=C["border"], border_radius=4,
        dense=True, text_size=13, color=C["text_body"], width=120)
    mode_dd = ft.Dropdown(value="自测",
        options=[ft.dropdown.Option(o) for o in CARD_MODES],
        bgcolor=C["bg_input"], border_color=C["border"], border_radius=4,
        dense=True, text_size=13, color=C["text_body"], width=100)

    # AI Exercise entry
    ex_type_dd = mk_dropdown("cloze", ["cloze", "choice", "definition"])
    ex_count_dd = mk_dropdown("5", ["5", "10", "15", "20"])

    # Wordbook list
    book_list = ft.ListView(spacing=2, height=160)
    selected_book = [None]

    def _build_book_list():
        book_list.controls.clear()
        books = wbm.list_books()
        if not books:
            book_list.controls.append(ft.Text("暂无词本", size=12, color=C["text_dim"]))
            return
        for name in books:
            wb = wbm.load_book(name)
            is_sel = selected_book[0] == name
            book_list.controls.append(ft.Container(
                content=ft.Row([
                    ft.Text(f"📗 {name}", size=13, color=C["text_body"], width=180),
                    ft.Text(f"{len(wb.words)} 词", size=11, color=C["text_dim"], width=60),
                    ft.Text(wb.created, size=11, color=C["text_dim"]),
                ], spacing=8),
                padding=ft.Padding(8, 6, 8, 6),
                bgcolor=C["accent"] if is_sel else C["bg_card"],
                border_radius=4,
                on_click=lambda _, n=name: _select_book(n),
                data=name))

    def _select_book(name):
        selected_book[0] = name
        _build_book_list()
        page.update()

    def _view_book_detail(name):
        try:
            wb = wbm.load_book(name)
            words = wb.words[:100]
        except Exception:
            words = ["(空)"]
        body = ft.Text("\n".join(words), size=11, color=C["text_body"])
        page.show_dialog(ft.AlertDialog(
            title=ft.Text(f"{name} ({len(wb.words) if isinstance(wb, object) else 0} 词)", color=C["text_primary"]),
            content=ft.Column([body], scroll=ft.ScrollMode.AUTO, height=300, width=280),
            actions=[ft.TextButton("关闭", on_click=lambda _: _close_dlg())],
            bgcolor=C["bg_card"]))

    def _new_book(_):
        name_field = ft.TextField(value="", label="词本名称", bgcolor=C["bg_input"],
            border_color=C["border"], border_radius=4, dense=True, text_size=13, color=C["text_body"], width=200)
        status_dd = ft.Dropdown(value="全部",
            options=[ft.dropdown.Option(o) for o in ["全部", "未学", "学习中", "已掌握"]],
            bgcolor=C["bg_input"], border_color=C["border"], border_radius=4,
            dense=True, text_size=13, color=C["text_body"], width=120)

        def _create(_):
            n = name_field.value.strip()
            if not n: return
            s = None if status_dd.value == "全部" else {"未学":"new","学习中":"learning","已掌握":"mastered"}[status_dd.value]
            wbm.create_from_filter(app.learned_db, n, status=s)
            _refresh_book(); _build_book_list()
            page.pop_dialog(); page.update()

        page.show_dialog(ft.AlertDialog(
            title=ft.Text("新建词本", color=C["text_primary"]),
            content=ft.Column([name_field, ft.Text("", size=8),
                ft.Row([ft.Text("状态筛选:", size=12, color=C["text_dim"]), status_dd])], spacing=4, width=280),
            actions=[ft.TextButton("取消", on_click=lambda _: _close_dlg()),
                     ft.FilledButton("创建", on_click=_create, style=ft.ButtonStyle(bgcolor=C["accent"], color="#fff"))],
            bgcolor=C["bg_card"]))

    def _delete_selected(_):
        if selected_book[0]:
            wbm.delete_book(selected_book[0])
            selected_book[0] = None
            active_book[0] = "全部词汇"
            _refresh_book(); _build_book_list()
            page.update()

    def _close_dlg():
        page.pop_dialog(); page.update()

    _build_book_list()

    v0 = ft.Column([
        ft.Row([ft.Text("当前词本:", size=12, color=C["text_dim"]), book_dd, book_info], spacing=8),
        ft.Text("", size=4),
        _dash_row(),
        ft.Text("", size=10),
        ft.Text("背诵设置", size=14, weight=ft.FontWeight.W_600, color=C["text_primary"]),
        ft.Text("", size=4),
        ft.Row([ft.Text("数量:", size=12, color=C["text_dim"]), count_field,
                ft.Text("策略:", size=12, color=C["text_dim"]), strategy_dd,
                ft.Text("模式:", size=12, color=C["text_dim"]), mode_dd,
                ft.FilledButton("开始背诵", on_click=lambda _: _start_session(),
                    style=ft.ButtonStyle(bgcolor=C["accent"], color="#fff", shape=ft.RoundedRectangleBorder(radius=4)))], spacing=8),
        ft.Text("", size=10),
        ft.Text("AI 练习", size=14, weight=ft.FontWeight.W_600, color=C["text_primary"]),
        ft.Text("", size=4),
        ft.Row([ft.Text("题型:", size=11, color=C["text_dim"]), ex_type_dd,
                ft.Text("数量:", size=11, color=C["text_dim"]), ex_count_dd,
                ft.FilledButton("进入练习", on_click=lambda _: (_show_exercise(), _gen_exercise(None)),
                    style=ft.ButtonStyle(bgcolor=C["accent"], color="#fff", shape=ft.RoundedRectangleBorder(radius=4)))], spacing=8),
        ft.Text("", size=10),
        ft.Text("词本管理", size=14, weight=ft.FontWeight.W_600, color=C["text_primary"]),
        ft.Row([
            ft.TextButton("新建词本", on_click=_new_book, style=ft.ButtonStyle(color=C["text_muted"], text_style=ft.TextStyle(size=11))),
            ft.TextButton("删除选中", on_click=_delete_selected, style=ft.ButtonStyle(color=C["text_muted"], text_style=ft.TextStyle(size=11))),
        ], spacing=8),
        ft.Text("", size=2),
        book_list,
    ], spacing=2)

    # ═══════════ View 1: Reciter Session ═══════════
    session_words = []
    session_index = [0]
    session_start_time = [0.0]
    session_card_mode = [1]
    card_start_time = [0.0]

    card_main = ft.Text("", size=36, weight=ft.FontWeight.W_700, color=C["text_primary"], text_align=ft.TextAlign.CENTER)
    card_sub = ft.Text("", size=14, color=C["text_dim"], text_align=ft.TextAlign.CENTER)
    card_progress = ft.Text("", size=12, color=C["text_dim"])

    def _start_session():
        cnt = int(count_field.value) if count_field.value.isdigit() else 20
        cnt = max(10, min(1000, cnt))
        pool = None
        if active_book[0] != "全部词汇":
            try: pool = wbm.load_book(active_book[0]).words
            except: pass
        session_words.clear()
        session_words.extend(engine.select_words(cnt, strategy_dd.value, pool))
        if not session_words:
            return
        session_index[0] = 0
        session_start_time[0] = time.time()
        engine.session_events.clear()
        session_card_mode[0] = CARD_MODES.get(mode_dd.value, 1)
        _show_view("reciter")
        _show_card()

    def _show_card():
        if session_index[0] >= len(session_words):
            _show_results()
            return
        ws = session_words[session_index[0]]
        ct = session_card_mode[0]
        if ct == 4: ct = random.choice([1, 2, 3])
        if ct == 1:
            card_main.value = ws.word; card_sub.value = ""
        elif ct == 2:
            card_main.value = ws.word
            card_sub.value = ws.chinese_meaning or "选择对应中文"
        elif ct == 3:
            card_main.value = ws.chinese_meaning or "中文释义"
            card_sub.value = ws.word
        card_progress.value = f"{session_index[0] + 1} / {len(session_words)}"
        card_start_time[0] = time.time()

    def _rate(rating):
        if session_index[0] >= len(session_words): return
        ws = session_words[session_index[0]]
        rt_ms = int((time.time() - card_start_time[0]) * 1000)
        engine.log_and_update(ws.word, rating, rt_ms)
        app.stats.record_action()
        session_index[0] += 1
        _show_card()
        page.update()

    result_text = ft.Text("", size=14, color=C["text_body"])

    def _show_results():
        stats = engine.session_stats()
        elapsed = int(time.time() - session_start_time[0])
        m, s = divmod(elapsed, 60)
        pct = lambda k: f"{stats[k]*100//max(1,stats['total'])}%"
        result_text.value = (
            f"总词数: {stats['total']}\n认识: {stats['认识']} ({pct('认识')})\n"
            f"模糊: {stats['模糊']} ({pct('模糊')})\n不认识: {stats['不认识']} ({pct('不认识')})\n"
            f"平均反应时: {stats['avg_rt_ms']}ms\n本次学习: {m}分{s}秒")
        _show_view("result")

    v1 = ft.Column([
        ft.Container(content=card_main, alignment=ft.alignment.Alignment(0, 0), expand=True,
                     padding=ft.Padding(0, 30, 0, 4)),
        ft.Container(content=card_sub, alignment=ft.alignment.Alignment(0, 0), padding=ft.Padding(0, 0, 0, 16)),
        ft.Container(content=card_progress, alignment=ft.alignment.Alignment(0, 0)),
        ft.Text("", size=16),
        ft.Row([
            ft.ElevatedButton("不认识", on_click=lambda _: _rate("不认识"), height=44,
                style=ft.ButtonStyle(bgcolor="#5a3a3a", color="#fff", text_style=ft.TextStyle(size=14))),
            ft.ElevatedButton("模糊", on_click=lambda _: _rate("模糊"), height=44,
                style=ft.ButtonStyle(bgcolor="#5a4a2a", color="#fff", text_style=ft.TextStyle(size=14))),
            ft.FilledButton("认识", on_click=lambda _: _rate("认识"), height=44,
                style=ft.ButtonStyle(bgcolor=C["green"], color="#fff", text_style=ft.TextStyle(size=14))),
        ], spacing=16, alignment=ft.MainAxisAlignment.CENTER),
    ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    v1_result = ft.Column([
        ft.Text("本次背诵完成", size=18, weight=ft.FontWeight.W_600, color=C["text_primary"]),
        ft.Text("", size=12), result_text, ft.Text("", size=16),
        ft.Row([
            ft.FilledButton("再来一轮", on_click=lambda _: _start_session(),
                style=ft.ButtonStyle(bgcolor=C["accent"], color="#fff", shape=ft.RoundedRectangleBorder(radius=4))),
            ft.OutlinedButton("返回主菜单", on_click=lambda _: _show_view("menu"),
                style=ft.ButtonStyle(color=C["text_muted"], side=ft.BorderSide(1, C["border"]))),
        ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
    ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # ═══════════ View 2: AI Practice Session ═══════════
    ex_result = ft.ListView(spacing=4, expand=True)
    ex_answers_visible = [False]
    _ex_cache = [None]  # cache last exercise data for answer toggle

    def _show_exercise():
        _show_view("exercise")

    def _gen_exercise(_):
        if not app.last_output_json:
            app.on_log("请先运行分类或导入JSON", "ok")
            return
        from lexi.story import _load_word_infos_from_json, StoryGenerator
        from lexi.exercises import ExerciseGenerator
        word_infos = _load_word_infos_from_json(app.last_output_json)
        sg = StoryGenerator(app.ctrl.config)
        words = sg.select_words(word_infos, count=min(int(ex_count_dd.value), 20), strategy="balanced")
        eg = ExerciseGenerator(app.ctrl.config)
        t = ex_type_dd.value
        result = eg.generate_cloze(words, word_infos, count=int(ex_count_dd.value)) if t == "cloze" else \
                 eg.generate_choice(words, word_infos, count=int(ex_count_dd.value)) if t == "choice" else \
                 eg.generate_definitions(words, word_infos)
        _ex_cache[0] = (result, t)
        _render_exercise(result, t)
        page.update()

    def _render_exercise(result, t):
        ex_result.controls.clear()
        for i, item in enumerate(result.items, 1):
            if t == "cloze":
                ans = f" **{item.correct}**" if ex_answers_visible[0] else ""
                ex_result.controls.append(ft.Text(f"{i}. {item.sentence}{ans}", size=13, color=C["text_body"]))
            elif t == "choice":
                ex_result.controls.append(ft.Text(f"{i}. {item.sentence}", size=13, color=C["text_body"]))
                for j, opt in enumerate(item.options):
                    is_correct = opt == item.correct
                    c = C["green"] if ex_answers_visible[0] and is_correct else C["text_muted"]
                    suffix = " ✓" if ex_answers_visible[0] and is_correct else ""
                    ex_result.controls.append(ft.Text(f"   {chr(65+j)}. {opt}{suffix}", size=12, color=c))
            else:
                w = f" **{item.word}**" if ex_answers_visible[0] else " ______"
                ex_result.controls.append(ft.Text(f"{i}. {item.definition} →{w}", size=13, color=C["text_body"]))

    def _toggle_ex_answers(_):
        ex_answers_visible[0] = not ex_answers_visible[0]
        if _ex_cache[0]:
            _render_exercise(*_ex_cache[0])
            page.update()

    v2 = ft.Column([
        ft.Text("AI 练习", size=18, weight=ft.FontWeight.W_600, color=C["text_primary"]),
        ft.Text("", size=8),
        ex_result,
        ft.Text("", size=12),
        ft.OutlinedButton("返回主菜单", on_click=lambda _: _show_view("menu"),
            style=ft.ButtonStyle(color=C["text_muted"], side=ft.BorderSide(1, C["border"]))),
    ], spacing=4)

    # ═══════════ View switching ═══════════
    views = {"menu": v0, "reciter": v1, "result": v1_result, "exercise": v2}

    def _show_view(name):
        tab_content.controls = [ft.Container(
            content=views[name], padding=ft.Padding(0, 8, 0, 0))]
        page.update()

    _show_view("menu")
    return tab_content
