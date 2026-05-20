"""阅读容器页面 — 短文生成 + 阅读器占位."""

import flet as ft
from ..widgets import C


def build_reading_page(app, page: ft.Page) -> ft.Column:
    from ..pages.story_page import build_story_page
    story_col = build_story_page(app, page)
    story_col.controls = story_col.controls[1:]

    tab_labels = ["短文生成", "阅读器"]
    tab_contents = [
        ft.Column(controls=story_col.controls, spacing=0, expand=True, scroll=ft.ScrollMode.AUTO),
        ft.Container(content=ft.Text("即将上线", size=14, color=C["text_muted"]),
                     padding=ft.Padding(0, 40, 0, 0), alignment=ft.alignment.Alignment(0, -1)),
    ]
    selected = [0]
    tab_buttons = []
    tab_stack = ft.Stack()

    def _switch(idx):
        selected[0] = idx
        for i, btn in enumerate(tab_buttons):
            btn.style = ft.ButtonStyle(
                color=C["accent"] if i == idx else C["text_muted"],
                text_style=ft.TextStyle(size=12, weight=ft.FontWeight.W_600 if i == idx else ft.FontWeight.W_400))
            btn.update()
        for i, c in enumerate(tab_contents):
            c.visible = (i == idx)
            c.update()
        page.update()

    for i, label in enumerate(tab_labels):
        idx = i
        btn = ft.TextButton(label, on_click=lambda _, i=idx: _switch(i),
                            style=ft.ButtonStyle(color=C["accent"] if i == 0 else C["text_muted"],
                                text_style=ft.TextStyle(size=12, weight=ft.FontWeight.W_600 if i == 0 else ft.FontWeight.W_400)))
        tab_buttons.append(btn)
        tab_contents[i].visible = (i == 0)

    tab_stack.controls = tab_contents

    return ft.Column(spacing=0, expand=True, controls=[
        ft.Container(content=ft.Row([ft.Text("阅读", size=15, weight=ft.FontWeight.W_600, color=C["text_primary"]),
                                     ft.Text("v3.3", size=11, color=C["text_dim"])],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                     padding=ft.Padding(24, 16, 24, 16), bgcolor=C["bg_panel"],
                     border=ft.Border.only(bottom=ft.BorderSide(1, C["border"]))),
        ft.Container(content=ft.Row(tab_buttons, spacing=4), padding=ft.Padding(24, 12, 24, 0)),
        ft.Container(content=tab_stack, padding=ft.Padding(24, 12, 24, 0), expand=True),
    ])
