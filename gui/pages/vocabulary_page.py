"""词库容器页面 — 4 个 Tabs: 导入分类 + 词库查看 + 背诵器 + AI 练习."""

import flet as ft
from ..widgets import C, mk_dropdown


def build_vocabulary_page(app, page: ft.Page) -> ft.Column:
    tab_labels = ["导入分类", "背诵器"]
    tab_contents = [
        _build_classify(app, page),
        _build_reciter(app, page),
    ]
    selected = [0]
    tab_buttons = []
    tab_stack = ft.Stack()

    def _export_csv(_=None):
        import tkinter.filedialog
        p = tkinter.filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if p:
            app.learned_db.export_csv(p)
            app.on_log(f"词库已导出: {p}", "ok")

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
        ft.Container(content=ft.Row([ft.Text("词库", size=15, weight=ft.FontWeight.W_600, color=C["text_primary"]),
                                     ft.Row([ft.Text("v3.3", size=11, color=C["text_dim"]),
                                             ft.OutlinedButton(content="导出CSV", on_click=_export_csv,
                                                style=ft.ButtonStyle(color=C["text_muted"], side=ft.BorderSide(1, C["border"]),
                                                                     shape=ft.RoundedRectangleBorder(radius=4), text_style=ft.TextStyle(size=11)))], spacing=8)],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                     padding=ft.Padding(24, 16, 24, 16), bgcolor=C["bg_panel"],
                     border=ft.Border.only(bottom=ft.BorderSide(1, C["border"]))),
        ft.Container(content=ft.Row(tab_buttons, spacing=4), padding=ft.Padding(24, 12, 24, 0)),
        ft.Container(content=tab_stack, padding=ft.Padding(24, 12, 24, 0), expand=True),
    ])


def _build_classify(app, page) -> ft.Column:
    from ..pages.classify_page import build_classify_page
    col = build_classify_page(app, page)
    col.controls = col.controls[1:]
    return ft.Column(controls=col.controls, spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)


def _build_reciter(app, page) -> ft.Column:
    from ..pages.reciter_tab import build_reciter_tab
    return ft.Column(controls=[
        ft.Container(content=build_reciter_tab(app, page), padding=ft.Padding(0, 8, 0, 0)),
    ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)


def _build_exercise(app, page) -> ft.Column:
    from ..pages.exercise_page import build_exercise_page
    col = build_exercise_page(app, page)
    col.controls = col.controls[1:]
    return ft.Column(controls=col.controls, spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
