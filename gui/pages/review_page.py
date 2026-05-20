"""每日复习页面."""

import flet as ft
from ..widgets import C


def build_review_page(app, page: ft.Page) -> ft.Column:
    due_list = ft.ListView(spacing=6, expand=True)

    def _rate(word, rating):
        app.learned_db.mark_reviewed(word, rating)
        _refresh()

    def _refresh():
        due = app.learned_db.get_due(limit=30)
        due_list.controls.clear()
        due_list.controls.append(ft.Text(f"今日到期: {len(due)} 词", size=14, weight=ft.FontWeight.W_600, color=C["text_primary"]))
        due_list.controls.append(ft.Text("", size=4))
        if not due:
            due_list.controls.append(ft.Text("全部完成！没有待复习的词汇。", size=13, color=C["green"]))
        else:
            for ws in due:
                w = ws.word
                due_list.controls.append(ft.Container(content=ft.Row([
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
        page.update()

    _refresh()

    return ft.Column(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(content=ft.Row([ft.Text("每日复习", size=15, weight=ft.FontWeight.W_600, color=C["text_primary"]),
                                     ft.Text("v3.0", size=11, color=C["text_dim"])],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                     padding=ft.Padding(24, 16, 24, 16), bgcolor=C["bg_panel"],
                     border=ft.Border.only(bottom=ft.BorderSide(1, C["border"]))),
        ft.Container(content=due_list, padding=ft.Padding(24, 20, 24, 24), expand=True),
    ])
