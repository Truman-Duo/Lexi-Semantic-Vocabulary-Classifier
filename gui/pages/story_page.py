"""AI 短文生成页面."""

import os
import tkinter.filedialog

import flet as ft

from ..widgets import mk_card, mk_dropdown, mk_outline_btn, C

STRATEGY_MAP = {"各类别均衡": "balanced", "高频优先": "top_frequency",
                "随机选取": "random", "按子类比例": "stratified"}
DENSITY_MAP = {"短篇 (3次/词)": "short", "中篇 (4次/词)": "medium", "长篇 (5次/词)": "long"}


def build_story_page(app, page: ft.Page) -> ft.Column:
    story_count = mk_dropdown("20", ["10", "15", "20", "25", "30", "40", "50"])
    story_strategy = mk_dropdown("各类别均衡", list(STRATEGY_MAP.keys()))
    story_density = mk_dropdown("中篇 (4次/词)", list(DENSITY_MAP.keys()))
    story_style = mk_dropdown("无", ["无"])
    story_words = ft.TextField(value="", hint_text="逗号分隔，留空则自动选择",
                               bgcolor=C["bg_input"], border_color=C["border"],
                               border_radius=4, dense=True, text_size=13, color=C["text_body"],
                               hint_style=ft.TextStyle(color=C["text_dim"], size=12))

    story_btn = mk_outline_btn("生成短文", lambda _: _run_story(), C["green"])
    import_json_btn = mk_outline_btn("导入分类JSON", lambda _: _import_json(), C["text_muted"])
    story_style_btn = ft.TextButton("管理风格", style=ft.ButtonStyle(color=C["text_muted"], text_style=ft.TextStyle(size=11)))

    def _import_json():
        p = tkinter.filedialog.askopenfilename(title="选择已分类的 JSON 文件",
                                                filetypes=[("JSON files", "*.json")])
        if p and os.path.exists(p):
            app.last_output_json = p
            app.last_base = os.path.splitext(os.path.basename(p))[0]
            _refresh_styles()

    def _refresh_styles():
        names = app.ctrl.styles.style_names()
        story_style.options = [ft.dropdown.Option("无")] + [ft.dropdown.Option(n) for n in names]
        story_style.value = "无"
        story_style.update()

    def _import_wordlist(_=None):
        p = tkinter.filedialog.askopenfilename(title="选择词表文件",
                                                filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if p:
            with open(p, "r", encoding="utf-8") as f:
                words = [line.strip() for line in f if line.strip()]
            story_words.value = ", ".join(words)
            story_words.update()

    def _run_story():
        w = story_words.value.strip()
        wl = [x.strip() for x in w.split(",") if x.strip()] if w else None
        if not app.story_words.strip():
            app.story_words = story_words.value
        out = app.output_path or "."
        sn = story_style.value
        if sn == "无" or not sn:
            sn = None
        app.story_count = int(story_count.value)
        app.story_strategy = STRATEGY_MAP.get(story_strategy.value, "balanced")
        app.story_length = DENSITY_MAP.get(story_density.value, "medium")
        app.story_style = sn
        app.story_words = story_words.value
        app.run_story()
        page.update()

    return ft.Column(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(content=ft.Row([ft.Text("AI 短文生成", size=15, weight=ft.FontWeight.W_600, color=C["text_primary"]),
                                     ft.Text("v3.0", size=11, color=C["text_dim"])],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                     padding=ft.Padding(24, 16, 24, 16), bgcolor=C["bg_panel"],
                     border=ft.Border.only(bottom=ft.BorderSide(1, C["border"]))),
        ft.Container(content=ft.Column([
            mk_card("AI 短文生成", ft.Column([
                ft.Row([
                    ft.Column([ft.Text("词汇数量", size=11, color=C["text_dim"]), story_count], spacing=3),
                    ft.Column([ft.Text("选择策略", size=11, color=C["text_dim"]), story_strategy], spacing=3),
                    ft.Column([ft.Text("重复密度", size=11, color=C["text_dim"]), story_density], spacing=3),
                    ft.Column([ft.Text("风格模板", size=11, color=C["text_dim"]), story_style], spacing=3),
                ], spacing=10),
                ft.Row([story_words, story_btn], spacing=10),
                ft.Row([import_json_btn, mk_outline_btn("导入词表", _import_wordlist, C["text_muted"]), story_style_btn], spacing=8),
            ], spacing=10)),
        ], spacing=14), padding=ft.Padding(24, 20, 24, 24), expand=True),
    ])
