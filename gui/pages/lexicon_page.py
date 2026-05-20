"""我的词库页面."""

import flet as ft
from ..widgets import C


def build_lexicon_page(app, page: ft.Page) -> ft.Column:
    stats = app.learned_db.get_stats()
    stat_row = ft.Row([
        _stat_card(str(stats["total"]), "总计", C),
        _stat_card(str(stats["mastered"]), "已掌握", C),
        _stat_card(str(stats["learning"]), "学习中", C),
        _stat_card(str(stats["new"]), "未学", C),
    ], spacing=12)

    status_filter = ft.Dropdown(value="全部",
        options=[ft.dropdown.Option(o) for o in ["全部", "未学", "学习中", "已掌握"]],
        bgcolor=C["bg_input"], border_color=C["border"], border_radius=4,
        dense=True, text_size=13, color=C["text_body"])
    word_list = ft.ListView(spacing=4, expand=True)

    def _refresh(filt="全部"):
        words = app.learned_db.get_all(None if filt == "全部" else
            {"未学": "new", "学习中": "learning", "已掌握": "mastered"}.get(filt))
        word_list.controls.clear()
        if not words:
            word_list.controls.append(ft.Text("暂无词汇。请先运行词汇分类。", size=13, color=C["text_muted"]))
        else:
            for ws in words[:200]:
                color = {"new": C["text_muted"], "learning": C["accent"], "mastered": C["green"]}.get(ws.status)
                label = {"new": "未学", "learning": "学习中", "mastered": "已掌握"}.get(ws.status)
                word_list.controls.append(ft.Row([
                    ft.Text(ws.word, size=13, color=C["text_body"], width=150),
                    ft.Text(label, size=11, color=color),
                    ft.Text(f"复习{ws.review_count}次" if ws.review_count else "", size=11, color=C["text_dim"]),
                ], spacing=12))
        page.update()

    status_filter.on_select = lambda e: _refresh(e.control.value)
    _refresh()

    return ft.Column(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(content=ft.Row([ft.Text("我的词库", size=15, weight=ft.FontWeight.W_600, color=C["text_primary"]),
                                     ft.Text("v3.0", size=11, color=C["text_dim"])],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                     padding=ft.Padding(24, 16, 24, 16), bgcolor=C["bg_panel"],
                     border=ft.Border.only(bottom=ft.BorderSide(1, C["border"]))),
        ft.Container(content=ft.Column([
            stat_row, ft.Text("", size=8),
            ft.Row([ft.Text("筛选:", size=12, color=C["text_dim"]), status_filter], spacing=8),
            ft.Text("", size=8),
            word_list,
        ], spacing=4), padding=ft.Padding(24, 20, 24, 24), expand=True),
    ])


def _stat_card(count: str, label: str, C) -> ft.Container:
    return ft.Container(
        content=ft.Column([ft.Text(count, size=22, weight=ft.FontWeight.W_700, color=C["accent"]),
                          ft.Text(label, size=11, color=C["text_dim"])],
                         horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        padding=ft.Padding(16, 12, 16, 12), bgcolor=C["bg_card"],
        border=ft.Border.all(1, C["border"]), border_radius=6)
