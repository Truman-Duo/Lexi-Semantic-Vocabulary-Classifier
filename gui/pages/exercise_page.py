"""AI 练习页面."""

import flet as ft

from ..widgets import mk_card, mk_dropdown, C


def build_exercise_page(app, page: ft.Page) -> ft.Column:
    exercise_type = mk_dropdown("cloze", ["cloze", "choice", "definition"])
    exercise_count = mk_dropdown("5", ["5", "10", "15", "20"])
    exercise_result = ft.ListView(spacing=4, expand=True)
    ex_show_answer = ft.TextButton("显示答案", style=ft.ButtonStyle(color=C["text_muted"]))
    ex_show_answer.visible = False
    _ex_answers_visible = [False]

    def _toggle_answers(_):
        _ex_answers_visible[0] = not _ex_answers_visible[0]
        page.update()

    ex_show_answer.on_click = _toggle_answers

    def _gen_exercise(_):
        if not app.last_output_json:
            app.on_log("请先导入分类JSON或运行分类", "ok")
            return
        from lexi.story import _load_word_infos_from_json
        from lexi.exercises import ExerciseGenerator
        from lexi.story import StoryGenerator
        word_infos = _load_word_infos_from_json(app.last_output_json)
        sg = StoryGenerator(app.ctrl.config)
        words = sg.select_words(word_infos, count=min(int(exercise_count.value), 20), strategy="balanced")
        eg = ExerciseGenerator(app.ctrl.config)
        t = exercise_type.value
        if t == "cloze":
            result = eg.generate_cloze(words, word_infos, count=int(exercise_count.value))
        elif t == "choice":
            result = eg.generate_choice(words, word_infos, count=int(exercise_count.value))
        else:
            result = eg.generate_definitions(words, word_infos)
        exercise_result.controls.clear()
        for i, item in enumerate(result.items, 1):
            if result.type == "cloze":
                ans = f" **{item.correct}**" if _ex_answers_visible[0] else ""
                exercise_result.controls.append(ft.Text(f"{i}. {item.sentence}{ans}", size=13, color=C["text_body"]))
            elif result.type == "choice":
                exercise_result.controls.append(ft.Text(f"{i}. {item.sentence}", size=13, color=C["text_body"]))
                for j, opt in enumerate(item.options):
                    is_correct = opt == item.correct
                    prefix = f"   {chr(65+j)}. "
                    if _ex_answers_visible[0] and is_correct:
                        exercise_result.controls.append(ft.Text(f"{prefix}{opt} ✓", size=12, color=C["green"]))
                    else:
                        exercise_result.controls.append(ft.Text(f"{prefix}{opt}", size=12, color=C["text_muted"]))
                exercise_result.controls.append(ft.Text("", size=4))
            else:
                defn = item.definition
                word = f" **{item.word}**" if _ex_answers_visible[0] else " ______"
                exercise_result.controls.append(ft.Text(f"{i}. {defn} →{word}", size=13, color=C["text_body"]))
        ex_show_answer.visible = True
        page.update()

    return ft.Column(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(content=ft.Row([ft.Text("AI 练习", size=15, weight=ft.FontWeight.W_600, color=C["text_primary"]),
                                     ft.Text("v3.0", size=11, color=C["text_dim"])],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                     padding=ft.Padding(24, 16, 24, 16), bgcolor=C["bg_panel"],
                     border=ft.Border.only(bottom=ft.BorderSide(1, C["border"]))),
        ft.Container(content=ft.Column([
            ft.Row([ft.Text("题型:", size=12, color=C["text_dim"]), exercise_type,
                    ft.Text("数量:", size=12, color=C["text_dim"]), exercise_count,
                    ft.FilledButton(content="生成练习", on_click=_gen_exercise,
                                    style=ft.ButtonStyle(bgcolor=C["accent"], color="#fff",
                                                         shape=ft.RoundedRectangleBorder(radius=4)))], spacing=10),
            ft.Text("", size=8),
            ft.Row([ex_show_answer]),
            exercise_result,
        ], spacing=4), padding=ft.Padding(24, 20, 24, 24), expand=True),
    ])
