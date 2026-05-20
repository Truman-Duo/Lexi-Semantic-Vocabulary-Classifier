"""背诵器 Tab — SM-2 间隔复习 + 学习计划进度."""

import flet as ft
from ..widgets import C


def build_reciter_tab(app, page: ft.Page) -> ft.Column:
    """SM-2 review + plan progress, merged into one tab."""

    def _refresh():
        due = app.learned_db.get_due(limit=30)
        from lexi.planner import PlanGenerator
        pg = PlanGenerator()
        p = pg.get_progress()

        lv = ft.Column(spacing=6)

        # ── Plan progress ──
        if pg.plan.days:
            lv.controls.append(ft.ProgressBar(value=p["pct"]/100, bgcolor=C["bg_input"], color=C["accent"], bar_height=4))
            lv.controls.append(ft.Text(
                f"目标 CEFR {pg.plan.target_cefr} | {p['completed_days']}/{p['total_days']} 天 | {p['total_words']} 词",
                size=12, color=C["text_dim"]))
            lv.controls.append(ft.Text("", size=4))

        # ── SM-2 review ──
        lv.controls.append(ft.Text(f"今日背诵: {len(due)} 词", size=14, weight=ft.FontWeight.W_600, color=C["text_primary"]))
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

        # ── Schedule ──
        if pg.plan.days:
            lv.controls.append(ft.Text("", size=12))
            lv.controls.append(ft.Text("全部日程", size=12, weight=ft.FontWeight.W_600, color=C["text_dim"]))
            for d in pg.plan.days:
                mark = "✓" if d.completed else "○"
                color = C["green"] if d.completed else C["text_muted"]
                lv.controls.append(ft.Text(f"  {mark} {d.date} — {len(d.words)} 词", size=12, color=color))

        tab_content.controls = [lv]
        page.update()

    def _rate(word, rating):
        app.learned_db.mark_reviewed(word, rating)
        _refresh()

    tab_content = ft.Column()
    _refresh()
    return tab_content
