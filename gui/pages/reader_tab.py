"""阅读器 Tab — AI 生成长文（500-1500词），融入目标词汇."""

import flet as ft
from ..widgets import C, mk_dropdown
from lexi.story import StoryGenerator, _load_word_infos_from_json


def build_reader_tab(app, page: ft.Page) -> ft.Column:
    reader_count = mk_dropdown("15", ["10", "15", "20", "30", "50"])
    reader_length = mk_dropdown("中篇 (~500词)", ["短篇 (~300词)", "中篇 (~500词)", "长篇 (~1000词)", "超长 (~1500词)"])
    reader_passage = ft.ListView(spacing=4, expand=True)
    reader_status = ft.Text("", size=12, color=C["text_dim"])

    def _generate(_):
        if not app.last_output_json:
            app.on_log("请先导入分类JSON或运行分类", "ok")
            return
        reader_status.value = "生成中..."
        page.update()
        word_infos = _load_word_infos_from_json(app.last_output_json)
        sg = StoryGenerator(app.ctrl.config)
        words = sg.select_words(word_infos, count=min(int(reader_count.value), 30), strategy="balanced")
        length_map = {"短篇 (~300词)": "short", "中篇 (~500词)": "medium",
                      "长篇 (~1000词)": "long", "超长 (~1500词)": "long"}
        result = sg.generate_story(words=words, word_infos=word_infos,
                                   length=length_map.get(reader_length.value, "medium"), language="zh")
        reader_passage.controls.clear()
        for line in result.passage.split("\n"):
            reader_passage.controls.append(ft.Text(line, size=14, color=C["text_body"]))
        reader_status.value = f"模型: {result.model} | 目标词: {len(words)} | 已用: {len(result.words_used)}"
        page.update()

    return ft.Column(spacing=0, expand=True, controls=[
        ft.Row([
            ft.Text("阅读器", size=14, weight=ft.FontWeight.W_600, color=C["text_primary"]),
            ft.Text("即将上线更多功能", size=11, color=C["text_dim"]),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Text("", size=8),
        ft.Row([reader_count, reader_length,
                ft.FilledButton("生成文章", on_click=_generate,
                                style=ft.ButtonStyle(bgcolor=C["accent"], color="#fff", shape=ft.RoundedRectangleBorder(radius=4)))], spacing=10),
        reader_status,
        ft.Text("", size=8),
        reader_passage,
    ])
