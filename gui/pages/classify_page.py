"""词汇分类页面."""

import os
import tkinter.filedialog

import flet as ft

from ..widgets import mk_field, mk_card, mk_form_row, mk_filled_btn, mk_dropdown, C


def build_classify_page(app, page: ft.Page) -> ft.Column:
    output_dir = [app.output_dir or os.path.dirname(os.path.abspath(__file__)) or "."]

    input_var = mk_field("")
    cat_var = mk_field(os.path.join(output_dir[0], "data", "categories_full.json"))
    stop_var = mk_field(os.path.join(output_dir[0], "data", "stopwords.txt"))
    over_var = mk_field("")
    outdir_var = mk_field(output_dir[0], readonly=False)

    def _browse_file(field):
        p = tkinter.filedialog.askopenfilename(title="选择文件")
        if p: field.value = p; field.update()

    def _browse_dir(field):
        p = tkinter.filedialog.askdirectory(title="选择输出目录")
        if p: field.value = p; output_dir[0] = p; app.output_path = p; field.update()

    format_dd = mk_dropdown("全部格式", [
        "全部格式", "仅 Markdown", "仅 JSON", "仅 CSV",
        "仅 HTML", "仅导入到背诵器（不导出文件）"
    ])

    progress_bar = ft.ProgressBar(value=0, bgcolor=C["bg_input"], color=C["accent"], bar_height=4)
    progress_pct = ft.Text("0%", size=12, color=C["text_dim"])
    status_text = ft.Text("就绪", size=12, color=C["text_body"])
    console = ft.ListView(spacing=2, padding=10, auto_scroll=True, height=160)

    log_container = ft.Container(visible=False,
        content=ft.Container(content=console, bgcolor=C["bg_base"],
                             border=ft.Border.all(1, C["border"]),
                             border_radius=4, padding=10, height=160))
    log_toggle = ft.Text("▽ 查看详细日志", size=11, color=C["text_dim"])
    _log_expanded = [False]

    def _toggle_log(_):
        _log_expanded[0] = not _log_expanded[0]
        log_container.visible = _log_expanded[0]
        log_toggle.value = "▲ 收起详细日志" if _log_expanded[0] else "▽ 查看详细日志"
        page.update()

    log_toggle_row = ft.Row([log_toggle], alignment=ft.MainAxisAlignment.END)
    log_toggle_row.on_click = _toggle_log

    def _log(msg, tag=""):
        color_map = {"hl": C["accent"], "dim": C["text_dim"], "ok": C["green"]}
        c = color_map.get(tag, C["text_muted"])
        console.controls.append(ft.Text(msg, size=12, color=c, font_family="monospace"))
        page.update()

    def _set_progress(pct):
        progress_bar.value = pct
        progress_pct.value = f"{int(pct*100)}%"
        page.update()

    def _set_status(m):
        status_text.value = m
        page.update()

    app.on_log = _log
    app.on_progress = _set_progress
    app.on_status = _set_status
    app.on_classify_done = lambda jp: app.on_nav(1)

    run_btn = mk_filled_btn("▶  开始分类", lambda _: _run(), C["accent"], "#ffffff", 15)

    def _run():
        f = format_dd.value
        if f == "仅导入到背诵器（不导出文件）":
            app.opt_md = app.opt_json = app.opt_csv = app.opt_html = app.opt_anki = False
        else:
            app.opt_md = f in ("全部格式", "仅 Markdown")
            app.opt_json = f in ("全部格式", "仅 JSON")
            app.opt_csv = f in ("全部格式", "仅 CSV")
            app.opt_html = f in ("全部格式", "仅 HTML")
            app.opt_anki = False

        app.input_file = input_var.value
        app.categories_path = cat_var.value or "data/categories_full.json"
        app.stopwords_path = stop_var.value or "data/stopwords.txt"
        app.overrides_path = over_var.value or None
        app.output_path = outdir_var.value or "."

        if not app.input_file:
            _log("请选择输入文件", "ok")
            return
        if not os.path.exists(app.input_file):
            _log(f"文件不存在: {app.input_file}", "ok")
            return
        app.last_base = os.path.splitext(os.path.basename(app.input_file))[0]
        console.controls.clear()
        run_btn.disabled = True
        _log_expanded[0] = True
        log_container.visible = True
        log_toggle.value = "▲ 收起详细日志"
        _log("Lexi 词汇分类工具 v3.0", "dim")
        _log("─" * 36, "dim")
        page.update()
        app.run_classify()
        run_btn.disabled = False
        page.update()

    return ft.Column(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(
            content=ft.Row([ft.Text("词汇分类", size=15, weight=ft.FontWeight.W_600, color=C["text_primary"]),
                           ft.Text("v3.3", size=11, color=C["text_dim"])],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(24, 16, 24, 16), bgcolor=C["bg_panel"],
            border=ft.Border.only(bottom=ft.BorderSide(1, C["border"]))),
        ft.Container(content=ft.Column([
            mk_card("输入设置", ft.Column([
                mk_form_row("输入文件", input_var, lambda _: _browse_file(input_var)),
                mk_form_row("分类词库", cat_var, lambda _: _browse_file(cat_var)),
                mk_form_row("停用词表", stop_var, lambda _: _browse_file(stop_var)),
                mk_form_row("覆盖规则", over_var, lambda _: _browse_file(over_var)),
                mk_form_row("输出目录", outdir_var, lambda _: _browse_dir(outdir_var)),
            ], spacing=8)),
            mk_card("输出格式", ft.Row([
                ft.Text("导出:", size=12, color=C["text_dim"]), format_dd
            ], spacing=8)),
            ft.Container(content=run_btn, padding=ft.Padding(0, 4, 0, 4)),
            mk_card("进度", ft.Column([
                ft.Row([progress_bar, progress_pct], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                status_text,
                log_toggle_row,
                log_container,
            ], spacing=6)),
        ], spacing=14), padding=ft.Padding(24, 20, 24, 24), expand=True),
    ])
