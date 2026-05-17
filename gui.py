#!/usr/bin/env python3
"""Lexi GUI — CustomTkinter modern interface"""

import os
import sys
import threading
from tkinter import Menu, messagebox, filedialog

import customtkinter as ctk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lexi.controller import LexiController, OutputOptions

ctk.set_default_color_theme("blue")


class LexiGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Lexi 词汇分类工具 v2.4")
        self.root.geometry("760x820")
        self.root.minsize(640, 700)

        self.running = False
        self.output_dir = os.path.dirname(os.path.abspath(__file__)) or "."
        self.last_output_json = None
        self.last_base = ""
        self.last_story_md = None
        self.ctrl = LexiController()

        self._build_ui()

    def _build_ui(self):
        self._build_menu()
        self.main_frame = ctk.CTkScrollableFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self._build_input_section()
        self._build_output_section()
        self._build_run_button()
        self._build_progress_section()
        self._build_story_section()
        self._build_result_section()
        self._build_bottom_buttons()

    def _build_menu(self):
        menubar = Menu(self.root)
        settings_menu = Menu(menubar, tearoff=0)
        settings_menu.add_command(label="API 配置...", command=self._show_api_settings)
        theme_menu = Menu(settings_menu, tearoff=0)
        theme_menu.add_command(label="浅色", command=lambda: ctk.set_appearance_mode("light"))
        theme_menu.add_command(label="深色", command=lambda: ctk.set_appearance_mode("dark"))
        theme_menu.add_command(label="跟随系统", command=lambda: ctk.set_appearance_mode("system"))
        settings_menu.add_cascade(label="主题", menu=theme_menu)
        menubar.add_cascade(label="设置", menu=settings_menu)
        self.root.config(menu=menubar)

    def _build_input_section(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(frame, text="输入设置", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=12, pady=(10, 6))

        self.input_var = ctk.StringVar(value="")
        self.cat_var = ctk.StringVar(value=os.path.join(self.output_dir, "data", "categories_full.json"))
        self.stop_var = ctk.StringVar(value=os.path.join(self.output_dir, "data", "stopwords.txt"))
        self.over_var = ctk.StringVar(value="")
        self.outdir_var = ctk.StringVar(value=self.output_dir)

        def browse(var, title):
            path = filedialog.askopenfilename(title=title)
            if path:
                var.set(path)

        self._file_row(frame, "输入文件", self.input_var, lambda: browse(self.input_var, "选择输入文本"))
        self._file_row(frame, "分类词库", self.cat_var, lambda: browse(self.cat_var, "选择分类词库 JSON"))
        self._file_row(frame, "停用词表", self.stop_var, lambda: browse(self.stop_var, "选择停用词表"))
        self._file_row(frame, "覆盖规则", self.over_var, lambda: browse(self.over_var, "选择覆盖 JSON"))
        self._dir_row(frame, "输出目录", self.outdir_var)

    def _file_row(self, parent, label, var, cmd):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=2)
        ctk.CTkLabel(row, text=label, width=70, anchor="w").pack(side="left")
        ctk.CTkEntry(row, textvariable=var).pack(side="left", fill="x", expand=True, padx=(6, 6))
        ctk.CTkButton(row, text="浏览", width=60, command=cmd).pack(side="right")

    def _dir_row(self, parent, label, var):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=2)
        ctk.CTkLabel(row, text=label, width=70, anchor="w").pack(side="left")
        ctk.CTkEntry(row, textvariable=var).pack(side="left", fill="x", expand=True, padx=(6, 6))
        ctk.CTkButton(row, text="浏览", width=60, command=lambda: self._browse_outdir(var)).pack(side="right")

    def _browse_outdir(self, var):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            var.set(path)
            self.output_dir = path

    def _build_output_section(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(frame, text="输出格式", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=12, pady=(10, 6))

        chk_frame = ctk.CTkFrame(frame, fg_color="transparent")
        chk_frame.pack(padx=12, pady=(0, 8))
        self.opt_md = ctk.BooleanVar(value=True)
        self.opt_json = ctk.BooleanVar(value=True)
        self.opt_csv = ctk.BooleanVar(value=True)
        self.opt_html = ctk.BooleanVar(value=True)
        self.opt_anki = ctk.BooleanVar(value=False)

        opts = [
            (self.opt_md, "Markdown"), (self.opt_json, "JSON"),
            (self.opt_csv, "CSV"), (self.opt_html, "HTML浏览器"), (self.opt_anki, "Anki牌组"),
        ]
        for var, label in opts:
            ctk.CTkCheckBox(chk_frame, text=label, variable=var).pack(side="left", padx=8)

    def _build_run_button(self):
        self.run_btn = ctk.CTkButton(
            self.main_frame, text="▶  开始分类", command=self._run,
            font=ctk.CTkFont(size=15, weight="bold"), height=42,
            fg_color="#3498db", hover_color="#2980b9",
        )
        self.run_btn.pack(pady=(4, 8))

    def _build_progress_section(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(frame, text="进度", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=12, pady=(10, 6))

        self.progress = ctk.CTkProgressBar(frame)
        self.progress.pack(fill="x", padx=12, pady=(0, 4))
        self.progress.set(0)

        self.status_var = ctk.StringVar(value="就绪")
        ctk.CTkLabel(frame, textvariable=self.status_var, anchor="w",
                     font=ctk.CTkFont(size=11)).pack(fill="x", padx=12, pady=(0, 6))

    def _build_story_section(self):
        self.story_frame = ctk.CTkFrame(self.main_frame)
        self.story_frame.pack(fill="x", pady=(0, 8))

        header = ctk.CTkFrame(self.story_frame, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(header, text="AI 短文生成",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        ctrl = ctk.CTkFrame(self.story_frame, fg_color="transparent")
        ctrl.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkLabel(ctrl, text="词汇数量", font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, sticky="w", padx=(0, 6))
        self.story_count_var = ctk.StringVar(value="20")
        ctk.CTkOptionMenu(ctrl, values=["10", "15", "20", "25", "30", "40", "50"],
                          variable=self.story_count_var, width=70).grid(
            row=0, column=1, sticky="w", padx=(0, 12))

        ctk.CTkLabel(ctrl, text="策略", font=ctk.CTkFont(size=12)).grid(
            row=0, column=2, sticky="w", padx=(0, 6))
        self.story_strategy_var = ctk.StringVar(value="balanced")
        ctk.CTkOptionMenu(ctrl, values=["balanced", "top_frequency", "random", "stratified"],
                          variable=self.story_strategy_var, width=130).grid(
            row=0, column=3, sticky="w", padx=(0, 12))

        ctk.CTkLabel(ctrl, text="长度", font=ctk.CTkFont(size=12)).grid(
            row=0, column=4, sticky="w", padx=(0, 6))
        self.story_length_var = ctk.StringVar(value="medium")
        ctk.CTkOptionMenu(ctrl, values=["short", "medium", "long"],
                          variable=self.story_length_var, width=90).grid(
            row=0, column=5, sticky="w")

        ctk.CTkLabel(ctrl, text="风格", font=ctk.CTkFont(size=12)).grid(
            row=1, column=0, sticky="w", padx=(0, 6), pady=(8, 0))
        self.story_style_var = ctk.StringVar(value="(无)")
        self.story_style_combo = ctk.CTkComboBox(
            ctrl, values=["(无)"], variable=self.story_style_var, width=160)
        self.story_style_combo.grid(row=1, column=1, columnspan=2, sticky="w", pady=(8, 0))
        ctk.CTkButton(ctrl, text="刷新风格", width=80, command=self._refresh_styles,
                      font=ctk.CTkFont(size=11)).grid(
            row=1, column=3, sticky="w", pady=(8, 0), padx=(6, 0))

        ctk.CTkLabel(ctrl, text="指定词汇", font=ctk.CTkFont(size=12)).grid(
            row=2, column=0, sticky="w", padx=(0, 6), pady=(8, 0))
        self.story_words_var = ctk.StringVar(value="")
        ctk.CTkEntry(ctrl, textvariable=self.story_words_var,
                     placeholder_text="逗号分隔，留空则自动选择").grid(
            row=2, column=1, columnspan=4, sticky="ew", pady=(8, 0))

        self.story_btn = ctk.CTkButton(
            ctrl, text="生成短文", command=self._run_story, width=100,
            fg_color="#27ae60", hover_color="#219a52",
        )
        self.story_btn.grid(row=2, column=5, sticky="e", pady=(8, 0))

        ctrl.columnconfigure(1, weight=0)
        ctrl.columnconfigure(3, weight=1)

        self._toggle_story_ui(False)

    def _build_result_section(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True, pady=(0, 8))
        ctk.CTkLabel(frame, text="输出日志", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=12, pady=(10, 6))

        self.result_text = ctk.CTkTextbox(frame, font=("Consolas", 11), wrap="word")
        self.result_text.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        self.result_text.configure(state="disabled")

    def _build_bottom_buttons(self):
        row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        row.pack(fill="x", pady=(0, 4))
        self.open_btn = ctk.CTkButton(row, text="打开输出文件夹", command=self._open_output,
                                      state="disabled", width=140)
        self.open_btn.pack(side="left", padx=(0, 8))
        self.open_story_btn = ctk.CTkButton(row, text="打开短文文件", command=self._open_story,
                                            state="disabled", width=140)
        self.open_story_btn.pack(side="left")

    def _refresh_styles(self):
        names = self.ctrl.styles.style_names()
        values = ["(无)"] + names
        self.story_style_combo.configure(values=values)
        if self.story_style_var.get() not in values:
            self.story_style_var.set("(无)")

    def _log(self, msg):
        self.root.after(0, self._do_log, msg)

    def _do_log(self, msg):
        self.result_text.configure(state="normal")
        self.result_text.insert("end", msg + "\n")
        self.result_text.see("end")
        self.result_text.configure(state="disabled")

    def _set_status(self, msg):
        self.root.after(0, self._do_status, msg)

    def _do_status(self, msg):
        self.status_var.set(msg)

    def _set_progress(self, pct):
        self.root.after(0, self._do_progress, pct)

    def _do_progress(self, pct):
        self.progress.set(pct)

    def _toggle_ui(self, enabled):
        state = "normal" if enabled else "disabled"
        self.run_btn.configure(state=state)
        self.open_btn.configure(state="disabled")
        self.open_story_btn.configure(state="disabled")

    def _toggle_story_ui(self, enabled):
        state = "normal" if enabled else "disabled"
        self.story_btn.configure(state=state)
        ctrl_frame = self.story_frame.winfo_children()[1]
        for child in ctrl_frame.winfo_children():
            try:
                child.configure(state=state)
            except Exception:
                pass

    def _open_output(self):
        if os.path.isdir(self.output_dir):
            os.startfile(self.output_dir)

    def _open_story(self):
        if self.last_story_md and os.path.exists(self.last_story_md):
            os.startfile(self.last_story_md)

    def _show_api_settings(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("API 配置")
        dialog.geometry("420x320")
        dialog.resizable(False, False)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Lexi AI API 配置",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(16, 4))
        ctk.CTkLabel(dialog, text="支持 OpenAI 兼容接口（OpenAI / DeepSeek / Ollama 等）",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(pady=(0, 12))

        config = self.ctrl.config

        ctk.CTkLabel(dialog, text="API Base URL", anchor="w").pack(fill="x", padx=24)
        url_var = ctk.StringVar(value=config.api_base_url)
        ctk.CTkEntry(dialog, textvariable=url_var).pack(fill="x", padx=24, pady=(2, 10))

        ctk.CTkLabel(dialog, text="API 密钥", anchor="w").pack(fill="x", padx=24)
        key_var = ctk.StringVar(value=config.api_key)
        key_entry = ctk.CTkEntry(dialog, textvariable=key_var, show="*")
        key_entry.pack(fill="x", padx=24, pady=(2, 2))
        show_key_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(dialog, text="显示密钥", variable=show_key_var, font=ctk.CTkFont(size=11),
                        command=lambda: key_entry.configure(
                            show="" if show_key_var.get() else "*")).pack(anchor="w", padx=24)

        ctk.CTkLabel(dialog, text="模型", anchor="w").pack(fill="x", padx=24, pady=(10, 0))
        model_var = ctk.StringVar(value=config.model)
        ctk.CTkEntry(dialog, textvariable=model_var).pack(fill="x", padx=24, pady=(2, 10))

        def save():
            config.api_key = key_var.get()
            config.api_base_url = url_var.get()
            config.model = model_var.get()
            self.ctrl.save_config()
            self._log(f"[API] 配置已保存 ({config.api_base_url}, {config.model})")
            dialog.destroy()

        ctk.CTkButton(dialog, text="保存", command=save,
                      fg_color="#27ae60", hover_color="#219a52",
                      height=36).pack(pady=12)

    def _run(self):
        if self.running:
            return
        input_file = self.input_var.get()
        if not input_file:
            messagebox.showerror("错误", "请选择输入文件")
            return
        if not os.path.exists(input_file):
            messagebox.showerror("错误", f"输入文件不存在:\n{input_file}")
            return

        cat_file = self.cat_var.get() or "data/categories_full.json"
        stop_file = self.stop_var.get() or "data/stopwords.txt"
        over_file = self.over_var.get() or None
        outdir = self.outdir_var.get() or "."

        self.last_base = os.path.splitext(os.path.basename(input_file))[0]
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.configure(state="disabled")
        self._toggle_ui(False)
        self._toggle_story_ui(False)
        self.last_output_json = None
        self.last_story_md = None
        self.running = True
        self._log("Lexi 词汇分类工具 v2.4")
        self._log("=" * 40)

        def run():
            try:
                self.ctrl.classify(
                    input_file=input_file,
                    categories_path=cat_file,
                    stopwords_path=stop_file if os.path.exists(stop_file) else "data/stopwords.txt",
                    overrides_path=over_file if over_file and os.path.exists(over_file) else None,
                    outputs=OutputOptions(
                        markdown=self.opt_md.get(),
                        json=self.opt_json.get(),
                        csv=self.opt_csv.get(),
                        html=self.opt_html.get(),
                        anki=self.opt_anki.get(),
                    ),
                    output_dir=outdir,
                    base_name=self.last_base,
                    status_callback=lambda msg: self._set_status(msg.strip()),
                    progress_callback=self._set_progress,
                )
                self.root.after(0, self._on_success)
            except Exception as e:
                self.root.after(0, self._on_error, str(e))

        threading.Thread(target=run, daemon=True).start()

    def _on_success(self):
        self._log("=" * 40)
        self._log("处理完成！")
        self._toggle_ui(True)
        self.running = False
        self.open_btn.configure(state="normal")
        json_path = os.path.join(self.outdir_var.get() or ".", f"{self.last_base}_output.json")
        if os.path.exists(json_path):
            self.last_output_json = json_path
            self._refresh_styles()
            self._toggle_story_ui(True)
            self._log("")
            self._log("💡 已启用 AI 短文生成，选择参数后点击'生成短文'")

    def _on_error(self, msg):
        self._log(f"错误: {msg}")
        self._toggle_ui(True)
        self.running = False
        self.run_btn.configure(state="normal")
        messagebox.showerror("处理出错", msg)

    def _run_story(self):
        if self.running:
            return
        if not self.last_output_json:
            messagebox.showerror("错误", "请先运行分类")
            return

        words_entry = self.story_words_var.get().strip()
        word_list = [w.strip() for w in words_entry.split(",") if w.strip()] if words_entry else None
        outdir = self.outdir_var.get() or "."

        style_name = self.story_style_var.get()
        if style_name == "(无)" or not style_name:
            style_name = None

        self._toggle_ui(False)
        self._toggle_story_ui(False)
        self.running = True
        self._log("")
        self._log("-" * 40)
        self._log("AI 短文生成中...")

        def run():
            try:
                result = self.ctrl.generate_story(
                    input_json=self.last_output_json,
                    output_dir=outdir,
                    word_list=word_list,
                    count=int(self.story_count_var.get()),
                    strategy=self.story_strategy_var.get(),
                    length=self.story_length_var.get(),
                    language="zh",
                    style=style_name,
                    progress_callback=self._set_progress,
                    status_callback=lambda msg: self._set_status(msg.strip()),
                )
                story_md = os.path.join(outdir, f"{self.last_base}_story.md")
                self.root.after(0, self._on_story_success, result, story_md)
            except Exception as e:
                self.root.after(0, self._on_error, str(e))

        threading.Thread(target=run, daemon=True).start()

    def _on_story_success(self, result, story_md):
        total = len(result.words_used) + len(result.words_missed)
        self._log(f"模型: {result.model}")
        self._log(f"目标词汇: {total}  |  已使用: {len(result.words_used)}  |  短文词数: {result.word_count}")
        if result.words_missed:
            self._log(f"未使用: {', '.join(result.words_missed)}")
        self._log("")
        self._log(result.passage)
        self._log("-" * 40)
        self._log(f"短文已保存: {story_md}")
        self._toggle_ui(True)
        self._toggle_story_ui(True)
        self.running = False
        self.last_story_md = story_md
        self.open_story_btn.configure(state="normal")

    def run(self):
        self.root.mainloop()


def main():
    app = LexiGUI()
    app.run()


if __name__ == "__main__":
    main()
