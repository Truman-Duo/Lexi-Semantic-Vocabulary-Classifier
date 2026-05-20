"""个人仪表盘页面."""

import flet as ft
from ..widgets import C


def build_profile_page(app, page: ft.Page) -> ft.Column:
    db = app.learned_db
    stats = db.get_stats()
    active_days = len(set(ws.last_reviewed for ws in db.words.values() if ws.last_reviewed))

    return ft.Column(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(content=ft.Row([ft.Text("个人", size=15, weight=ft.FontWeight.W_600, color=C["text_primary"]),
                                     ft.Text("v3.3", size=11, color=C["text_dim"])],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                     padding=ft.Padding(24, 16, 24, 16), bgcolor=C["bg_panel"],
                     border=ft.Border.only(bottom=ft.BorderSide(1, C["border"]))),
        ft.Container(content=ft.Column([
            ft.Row([_stat_card("学习天数", str(active_days), C),
                    _stat_card("词汇总量", str(stats["total"]), C),
                    _stat_card("已掌握", str(stats["mastered"]), C)], spacing=12),
            ft.Text("", size=12),
            ft.Row([_stat_card("学习中", str(stats["learning"]), C),
                    _stat_card("未学", str(stats["new"]), C),
                    _stat_card("今日到期", str(stats.get("due_today", 0)), C)], spacing=12),
        ], spacing=4), padding=ft.Padding(24, 20, 24, 24), expand=True),
    ])


def _stat_card(label: str, value: str, C) -> ft.Container:
    return ft.Container(
        content=ft.Column([ft.Text(value, size=28, weight=ft.FontWeight.W_700, color=C["accent"]),
                          ft.Text(label, size=12, color=C["text_dim"])],
                         horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
        padding=ft.Padding(20, 16, 20, 16), bgcolor=C["bg_card"],
        border=ft.Border.all(1, C["border"]), border_radius=6, expand=True)
