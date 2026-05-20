"""学习计划页面."""

import flet as ft
from ..widgets import mk_dropdown, C


def build_plan_page(app, page: ft.Page) -> ft.Column:
    plan_cefr = mk_dropdown("B2", ["A1", "A2", "B1", "B2", "C1", "C2"])
    plan_daily = mk_dropdown("20", ["10", "20", "30", "50"])
    plan_content = ft.ListView(spacing=6, expand=True)

    def _build():
        from lexi.planner import PlanGenerator
        pg = PlanGenerator()
        plan_content.controls.clear()
        if pg.plan.days:
            p = pg.get_progress()
            today = pg.get_today()
            plan_content.controls.append(ft.ProgressBar(value=p["pct"]/100, bgcolor=C["bg_input"], color=C["accent"], bar_height=6))
            plan_content.controls.append(ft.Text(
                f"目标 CEFR {pg.plan.target_cefr} | {p['completed_days']}/{p['total_days']} 天 | {p['total_words']} 词",
                size=12, color=C["text_dim"]))
            plan_content.controls.append(ft.Text("", size=4))
            if today:
                plan_content.controls.append(ft.Text("今日计划", size=14, weight=ft.FontWeight.W_600, color=C["text_primary"]))
                for w in today.words[:50]:
                    plan_content.controls.append(ft.Text(f"• {w}", size=13, color=C["text_body"]))
                plan_content.controls.append(ft.FilledButton("标记完成", on_click=lambda _: _done(pg, today.date),
                    style=ft.ButtonStyle(bgcolor=C["green"], color="#fff", shape=ft.RoundedRectangleBorder(radius=4))))
            else:
                plan_content.controls.append(ft.Text("所有计划已完成！", size=13, color=C["green"]))
            plan_content.controls.append(ft.Text("", size=12))
            plan_content.controls.append(ft.Text("全部日程", size=12, weight=ft.FontWeight.W_600, color=C["text_dim"]))
            for d in pg.plan.days:
                mark = "✓" if d.completed else "○"
                color = C["green"] if d.completed else C["text_muted"]
                plan_content.controls.append(ft.Text(f"  {mark} {d.date} — {len(d.words)} 词", size=12, color=color))
        else:
            plan_content.controls.append(ft.Text("暂无学习计划", size=14, color=C["text_muted"]))
            plan_content.controls.append(ft.Text("", size=8))
            plan_content.controls.append(ft.Text("创建计划需要先运行词汇分类，然后选择目标 CEFR 等级和每日词数。", size=12, color=C["text_dim"]))
            plan_content.controls.append(ft.Text("", size=8))
            plan_content.controls.append(ft.Row([plan_cefr, plan_daily,
                ft.FilledButton("创建计划", on_click=lambda _: _create(),
                    style=ft.ButtonStyle(bgcolor=C["accent"], color="#fff", shape=ft.RoundedRectangleBorder(radius=4)))], spacing=10))
        page.update()

    def _create():
        if not app.last_output_json:
            app.on_log("请先运行分类", "ok")
            return
        from lexi.story import _load_word_infos_from_json
        from lexi.planner import PlanGenerator
        word_infos = _load_word_infos_from_json(app.last_output_json)
        pg = PlanGenerator()
        pg.create_plan(word_infos, app.learned_db, plan_cefr.value, int(plan_daily.value))
        _build()

    def _done(pg, date_str):
        pg.mark_completed(date_str)
        _build()

    _build()

    return ft.Column(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(content=ft.Row([ft.Text("学习计划", size=15, weight=ft.FontWeight.W_600, color=C["text_primary"]),
                                     ft.Text("v3.0", size=11, color=C["text_dim"])],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                     padding=ft.Padding(24, 16, 24, 16), bgcolor=C["bg_panel"],
                     border=ft.Border.only(bottom=ft.BorderSide(1, C["border"]))),
        ft.Container(content=plan_content, padding=ft.Padding(24, 20, 24, 24), expand=True),
    ])
