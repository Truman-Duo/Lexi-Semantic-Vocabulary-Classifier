#!/usr/bin/env python3
"""Lexi GUI — 基于 tkinter 的词汇分类工具图形界面"""

import os
import sys
import threading
from tkinter import (
    Tk, Frame, Label, LabelFrame, Entry, Button, Text, Menu,
    Checkbutton, BooleanVar, StringVar, IntVar,
    filedialog, messagebox, ttk, Toplevel,
)

# Ensure parent directory is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lexi.controller import LexiController, OutputOptions


class LexiGUI:
    def __init__(self):
        self.root = Tk()
        self.root.title("Lexi 词汇分类工具 v2.0")
        self.root.geometry("720x780")
        self.root.resizable(True, True)

        self.running = False
        self.output_dir = os.path.dirname(os.path.abspath(__file__)) or "."
        self.last_output_json = None
        self.last_base = ""
        self.ctrl = LexiController()

        self._build_ui()

    def _build_ui(self):
        # --- Menu Bar ---
        menubar = Menu(self.root)
        settings_menu = Menu(menubar, tearoff=0)
        settings_menu.add_command(label="API 配置...", command=self._show_api_settings)
        menubar.add_cascade(label="设置", menu=settings_menu)
        self.root.config(menu=menubar)

        # --- Input Section ---
        sec = LabelFrame(self.root, text=" 输入设置 ", padx=10, pady=8)
        sec.pack(fill="x", padx=12, pady=(12, 4))

        def file_row(parent, label, var, btn_text, btn_cmd):
            r = Frame(parent)
            r.pack(fill="x", pady=2)
            Label(r, text=label, width=10, anchor="w").pack(side="left")
            Entry(r, textvariable=var, state="readonly").pack(side="left", fill="x", expand=True, padx=(4, 4))
            Button(r, text=btn_text, command=btn_cmd, width=8).pack(side="right")

        self.input_var = StringVar(value="")
        self.cat_var = StringVar(value=os.path.join(self.output_dir, "data", "categories_full.json"))
        self.stop_var = StringVar(value=os.path.join(self.output_dir, "data", "stopwords.txt"))
        self.over_var = StringVar(value="")
        self.outdir_var = StringVar(value=self.output_dir)

        file_row(sec, "输入文件:", self.input_var, "浏览(I)", lambda: self._browse_file(self.input_var, "选择输入文本"))
        file_row(sec, "分类词库:", self.cat_var, "浏览(C)", lambda: self._browse_file(self.cat_var, "选择分类词库 JSON"))
        file_row(sec, "停用词表:", self.stop_var, "浏览(S)", lambda: self._browse_file(self.stop_var, "选择停用词表"))
        file_row(sec, "覆盖规则:", self.over_var, "浏览(O)", lambda: self._browse_file(self.over_var, "选择分类覆盖 JSON"))
        file_row(sec, "输出目录:", self.outdir_var, "浏览(T)", self._browse_outdir)

        # --- Output Format Section ---
        sec2 = LabelFrame(self.root, text=" 输出格式 ", padx=10, pady=6)
        sec2.pack(fill="x", padx=12, pady=4)

        self.opt_md = BooleanVar(value=True)
        self.opt_json = BooleanVar(value=True)
        self.opt_csv = BooleanVar(value=True)
        self.opt_html = BooleanVar(value=True)
        self.opt_anki = BooleanVar(value=False)

        chk_frame = Frame(sec2)
        chk_frame.pack()
        for i, (var, label) in enumerate([
            (self.opt_md, "Markdown"),
            (self.opt_json, "JSON"),
            (self.opt_csv, "CSV"),
            (self.opt_html, "HTML 浏览器"),
            (self.opt_anki, "Anki 牌组"),
        ]):
            Checkbutton(chk_frame, text=label, variable=var).grid(row=0, column=i, padx=8)

        # --- Run Button ---
        self.run_btn = Button(self.root, text="▶ 开始分类", command=self._run,
                              font=("", 12, "bold"), bg="#3498db", fg="white",
                              padx=20, pady=4, cursor="hand2")
        self.run_btn.pack(pady=8)

        # --- Progress Section ---
        sec3 = LabelFrame(self.root, text=" 进度 ", padx=10, pady=6)
        sec3.pack(fill="x", padx=12, pady=4)

        self.progress = ttk.Progressbar(sec3, mode="determinate")
        self.progress.pack(fill="x", pady=(4, 2))

        self.status_var = StringVar(value="就绪")
        Label(sec3, textvariable=self.status_var, anchor="w",
              fg="#555", font=("", 9)).pack(fill="x")

        # --- Results Section ---
        sec4 = LabelFrame(self.root, text=" 结果 ", padx=10, pady=6)
        sec4.pack(fill="both", expand=True, padx=12, pady=4)

        self.result_text = Text(sec4, height=6, state="disabled",
                                font=("Consolas", 9), wrap="word")
        self.result_text.pack(fill="both", expand=True)

        # --- Story Generation Section ---
        self.story_frame = LabelFrame(self.root, text=" AI 短文生成 ", padx=10, pady=6)
        self.story_frame.pack(fill="x", padx=12, pady=4)

        ctrl_frame = Frame(self.story_frame)
        ctrl_frame.pack(fill="x")

        Label(ctrl_frame, text="词汇数量:").grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.story_count_var = IntVar(value=20)
        ttk.Spinbox(ctrl_frame, from_=10, to=50, textvariable=self.story_count_var,
                    width=5).grid(row=0, column=1, sticky="w", padx=(0, 12))

        Label(ctrl_frame, text="策略:").grid(row=0, column=2, sticky="w", padx=(0, 4))
        self.story_strategy_var = StringVar(value="balanced")
        ttk.Combobox(ctrl_frame, textvariable=self.story_strategy_var,
                     values=["balanced", "top_frequency", "random", "stratified"],
                     state="readonly", width=14).grid(row=0, column=3, sticky="w", padx=(0, 12))

        Label(ctrl_frame, text="长度:").grid(row=0, column=4, sticky="w", padx=(0, 4))
        self.story_length_var = StringVar(value="medium")
        ttk.Combobox(ctrl_frame, textvariable=self.story_length_var,
                     values=["short", "medium", "long"],
                     state="readonly", width=8).grid(row=0, column=5, sticky="w")

        Label(ctrl_frame, text="指定词汇:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.story_words_var = StringVar(value="")
        Entry(ctrl_frame, textvariable=self.story_words_var).grid(
            row=1, column=1, columnspan=4, sticky="ew", pady=(6, 0), padx=(0, 4))

        self.story_btn = Button(ctrl_frame, text="生成短文", command=self._run_story,
                                bg="#27ae60", fg="white", padx=12, pady=2,
                                cursor="hand2")
        self.story_btn.grid(row=1, column=5, sticky="e", pady=(6, 0))

        Label(ctrl_frame, text="风格:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.story_style_var = StringVar(value="")
        self.story_style_combo = ttk.Combobox(
            ctrl_frame, textvariable=self.story_style_var,
            state="readonly", width=18,
        )
        self.story_style_combo.grid(row=2, column=1, columnspan=2, sticky="w", pady=(6, 0))
        self.refresh_styles_btn = Button(
            ctrl_frame, text="刷新风格", command=self._refresh_styles,
            font=("", 8),
        )
        self.refresh_styles_btn.grid(row=2, column=3, sticky="w", pady=(6, 0), padx=(4, 0))

        ctrl_frame.columnconfigure(1, weight=0)
        ctrl_frame.columnconfigure(3, weight=1)

        # Open output folder button
        btn_frame = Frame(self.root)
        btn_frame.pack(pady=(4, 10))
        self.open_btn = Button(btn_frame, text="打开输出文件夹",
                               command=self._open_output, state="disabled")
        self.open_btn.pack(side="left", padx=4)
        self.open_story_btn = Button(btn_frame, text="打开短文文件",
                                     command=self._open_story, state="disabled")
        self.open_story_btn.pack(side="left", padx=4)

        self._toggle_story_ui(False)
        self.last_story_md = None

    def _browse_file(self, var, title):
        path = filedialog.askopenfilename(title=title)
        if path:
            var.set(path)

    def _browse_outdir(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.outdir_var.set(path)
            self.output_dir = path

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
        self.progress["value"] = pct * 100

    def _toggle_ui(self, enabled):
        state = "normal" if enabled else "disabled"
        self.run_btn.configure(state=state)
        self.open_btn.configure(state="disabled")
        for child in self.root.winfo_children():
            if isinstance(child, LabelFrame):
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, Button) and grandchild not in (self.run_btn, self.story_btn):
                        grandchild.configure(state=state)

    def _toggle_story_ui(self, enabled):
        state = "normal" if enabled else "disabled"
        self.story_btn.configure(state=state)
        for child in self.story_frame.winfo_children():
            if isinstance(child, Frame):
                for grandchild in child.winfo_children():
                    try:
                        grandchild.configure(state=state)
                    except Exception:
                        pass

    def _open_output(self):
        path = self.output_dir
        if os.path.isdir(path):
            os.startfile(path)

    def _open_story(self):
        if self.last_story_md and os.path.exists(self.last_story_md):
            os.startfile(self.last_story_md)

    def _show_api_settings(self):
        dialog = Toplevel(self.root)
        dialog.title("API 配置")
        dialog.geometry("420x280")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        config = self.ctrl.config

        Label(dialog, text="Lexi AI API 配置", font=("", 11, "bold")).pack(pady=(12, 8))
        Label(dialog, text="支持 OpenAI 兼容接口（OpenAI / DeepSeek / Ollama 等）",
              fg="#888", font=("", 8)).pack()

        fields = Frame(dialog)
        fields.pack(pady=8, padx=20, fill="x")

        Label(fields, text="API Base URL:", anchor="w").pack(fill="x")
        url_var = StringVar(value=config.api_base_url)
        Entry(fields, textvariable=url_var).pack(fill="x", pady=(0, 8))

        Label(fields, text="API 密钥:", anchor="w").pack(fill="x")
        key_var = StringVar(value=config.api_key)
        key_entry = Entry(fields, textvariable=key_var, show="*")
        key_entry.pack(fill="x", pady=(0, 2))
        show_key_var = BooleanVar(value=False)
        Checkbutton(fields, text="显示密钥", variable=show_key_var,
                    command=lambda: key_entry.configure(
                        show="" if show_key_var.get() else "*")).pack(anchor="w")

        Label(fields, text="模型:", anchor="w").pack(fill="x", pady=(8, 0))
        model_var = StringVar(value=config.model)
        Entry(fields, textvariable=model_var).pack(fill="x", pady=(0, 8))

        def save():
            config.api_key = key_var.get()
            config.api_base_url = url_var.get()
            config.model = model_var.get()
            self.ctrl.save_config()
            self._log(f"[API] 配置已保存 ({config.api_base_url}, {config.model})")
            dialog.destroy()

        Button(dialog, text="保存", command=save,
               bg="#27ae60", fg="white", padx=20, pady=4).pack(pady=8)

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

        def make_path(ext):
            return os.path.join(outdir, f"{self.last_base}{ext}")

        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.configure(state="disabled")
        self._toggle_ui(False)
        self._toggle_story_ui(False)
        self.open_story_btn.configure(state="disabled")
        self.last_output_json = None
        self.last_story_md = None
        self.running = True
        self._log("Lexi 词汇分类工具 v2.0")
        self._log("=" * 40)

        def run():
            try:
                result = self.ctrl.classify(
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
            self._log("\U0001f4a1 已启用 AI 短文生成，选择词汇数量后点击'生成短文'")

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
                    count=self.story_count_var.get(),
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
        self._log(f"模型: {result.model}")
        self._log(f"目标词汇: {len(result.words_used) + len(result.words_missed)}")
        self._log(f"已使用: {len(result.words_used)}")
        self._log(f"短文词数: {result.word_count}")
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

    def _refresh_styles(self):
        names = self.ctrl.styles.style_names()
        self.story_style_combo["values"] = ["(无)"] + names
        if not self.story_style_var.get() or self.story_style_var.get() not in names:
            self.story_style_var.set("(无)")

    def run(self):
        self.root.mainloop()


def main():
    app = LexiGUI()
    app.run()


if __name__ == "__main__":
    main()
