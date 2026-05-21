#!/usr/bin/env python3
"""Lexi GUI — Flet entry point. Page assembly and navigation only."""

import os
import sys

import flet as ft

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lexi.gui_app import LexiApp
from gui.theme import C, FONT_FAMILY, MONO_FAMILY
from gui.pages.profile_page import build_profile_page
from gui.pages.vocabulary_page import build_vocabulary_page
from gui.pages.reading_page import build_reading_page


def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = C["bg_base"]
    page.fonts = {"body": FONT_FAMILY, "mono": MONO_FAMILY}
    page.theme = ft.Theme(font_family="body")
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

    profile_page = build_profile_page(app, page)
    vocab_page = build_vocabulary_page(app, page)
    reading_page = build_reading_page(app, page)

    PAGES = [profile_page, vocab_page, reading_page]
    PAGE_TITLES = ["个人", "词库", "阅读"]
    for i, p in enumerate(PAGES):
        p.visible = (i == 0)

    def _nav_to(idx):
        for i, p in enumerate(PAGES):
            p.visible = (i == idx)
        page.update()

    app.on_nav = _nav_to

    def _show_api_dialog():
        cfg = app.ctrl.config
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

        def _save(_):
            app.save_api_config(api_key.value, api_url.value, model_name.value)
            app.on_log(f"[API] 配置已保存 ({api_url.value}, {model_name.value})", "dim")
            page.pop_dialog()
            page.update()

        page.show_dialog(ft.AlertDialog(
            title=ft.Text("API 配置", color=C["text_primary"]),
            content=ft.Column([api_url, api_key, model_name], spacing=12, width=380),
            actions=[ft.TextButton("取消", on_click=lambda _: _close_dlg()),
                     ft.FilledButton("保存", on_click=_save,
                                     style=ft.ButtonStyle(bgcolor=C["green"], color="#ffffff"))],
            bgcolor=C["bg_card"]))

    def _show_style_info():
        try:
            names = app.ctrl.styles.style_names()
        except Exception:
            names = []
        if names:
            body = ft.Column([ft.Text(f"• {n}", size=13, color=C["text_body"]) for n in names], spacing=4)
        else:
            body = ft.Text("暂无风格模板\n\n使用 CLI 添加: python cli.py style add <name> <file>",
                           size=13, color=C["text_muted"])
        page.show_dialog(ft.AlertDialog(
            title=ft.Text("风格模板", color=C["text_primary"]),
            content=ft.Column([body, ft.Text("", size=8),
                ft.Text("CLI 管理: python cli.py style add/list/delete", size=11, color=C["text_dim"])],
                spacing=6, width=300),
            actions=[ft.TextButton("关闭", on_click=lambda _: _close_dlg())],
            bgcolor=C["bg_card"]))

    def _show_settings():
        page.show_dialog(ft.AlertDialog(
            title=ft.Text("设置", color=C["text_primary"]),
            content=ft.Column([
                ft.TextButton("API 配置...", on_click=lambda _: (_close_dlg(), _show_api_dialog())),
            ], spacing=4, width=220),
            actions=[ft.TextButton("关闭", on_click=lambda _: _close_dlg())],
            bgcolor=C["bg_card"]))

    def _close_dlg():
        page.pop_dialog()
        page.update()

    sidebar = ft.NavigationRail(
        selected_index=0, label_type=ft.NavigationRailLabelType.ALL,
        min_width=80, min_extended_width=140,
        bgcolor=C["bg_panel"], indicator_color=C["accent"],
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.PERSON_OUTLINED, selected_icon=ft.Icons.PERSON, label="个人"),
            ft.NavigationRailDestination(icon=ft.Icons.MENU_BOOK_OUTLINED, selected_icon=ft.Icons.MENU_BOOK, label="词库"),
            ft.NavigationRailDestination(icon=ft.Icons.AUTO_STORIES_OUTLINED, selected_icon=ft.Icons.AUTO_STORIES, label="阅读"),
            ft.NavigationRailDestination(icon=ft.Icons.HEADPHONES_OUTLINED, selected_icon=ft.Icons.HEADPHONES, label="听力"),
            ft.NavigationRailDestination(icon=ft.Icons.EDIT_OUTLINED, selected_icon=ft.Icons.EDIT, label="写作"),
            ft.NavigationRailDestination(icon=ft.Icons.CHAT_OUTLINED, selected_icon=ft.Icons.CHAT, label="对话"),
            ft.NavigationRailDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="设置"),
        ])

    FUTURE_LABELS = {3: "听力", 4: "写作", 5: "对话"}

    def _on_nav(e):
        idx = e.control.selected_index
        _dbg(f"🖱 NAV: {idx} → {PAGE_TITLES[idx] if idx < 3 else FUTURE_LABELS.get(idx, '设置')}")
        if idx == 6:
            _show_settings()
            return
        if idx >= 3:
            page.show_dialog(ft.AlertDialog(
                title=ft.Text(FUTURE_LABELS.get(idx, "功能"), color=C["text_primary"]),
                content=ft.Text("即将上线", size=13, color=C["text_muted"]),
                actions=[ft.TextButton("好的", on_click=lambda _: _close_dlg())],
                bgcolor=C["bg_card"]))
            return
        for i, p in enumerate(PAGES):
            p.visible = (i == idx)
        page.update()

    sidebar.on_change = _on_nav

    page.add(ft.Row([sidebar, ft.VerticalDivider(width=1, color=C["border"]),
                     ft.Stack(PAGES, expand=True)], expand=True, spacing=0))


if __name__ == "__main__":
    ft.run(main)
