#!/usr/bin/env python3
"""Lexi GUI — 基于 tkinter 的词汇分类工具图形界面"""

import os
import sys
import threading
from tkinter import (
    Tk, Frame, Label, LabelFrame, Entry, Button, Text,
    Checkbutton, BooleanVar, StringVar, IntVar,
    filedialog, messagebox, ttk,
)

# Ensure parent directory is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lexi.pipeline import run_pipeline


class LexiGUI:
    def __init__(self):
        self.root = Tk()
        self.root.title("Lexi 词汇分类工具 v2.0")
        self.root.geometry("720x620")
        self.root.resizable(True, True)

        # State
        self.running = False
        self.output_dir = os.path.dirname(os.path.abspath(__file__)) or "."

        self._build_ui()

    def _build_ui(self):
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

        self.result_text = Text(sec4, height=8, state="disabled",
                                font=("Consolas", 9), wrap="word")
        self.result_text.pack(fill="both", expand=True)

        # Open output folder button
        self.open_btn = Button(self.root, text="📂 打开输出文件夹",
                               command=self._open_output, state="disabled")
        self.open_btn.pack(pady=(4, 10))

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
        # Disable/enable input section children
        for child in self.root.winfo_children():
            if isinstance(child, LabelFrame):
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, Button) and grandchild != self.run_btn:
                        grandchild.configure(state=state)

    def _open_output(self):
        path = self.output_dir
        if os.path.isdir(path):
            os.startfile(path)

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

        base = os.path.splitext(os.path.basename(input_file))[0]

        def make_path(ext):
            return os.path.join(outdir, f"{base}{ext}")

        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.configure(state="disabled")
        self._toggle_ui(False)
        self.running = True
        self._log("Lexi 词汇分类工具 v2.0")
        self._log("=" * 40)

        def run():
            try:
                run_pipeline(
                    input_file=input_file,
                    categories_json=cat_file,
                    stopwords_txt=stop_file if os.path.exists(stop_file) else None,
                    overrides_json=over_file if over_file and os.path.exists(over_file) else None,
                    output_md=make_path("_output.md") if self.opt_md.get() else None,
                    output_json=make_path("_output.json") if self.opt_json.get() else None,
                    output_csv=make_path("_output.csv") if self.opt_csv.get() else None,
                    output_html=make_path("_output.html") if self.opt_html.get() else None,
                    output_anki=make_path("_output.apkg") if self.opt_anki.get() else None,
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

    def _on_error(self, msg):
        self._log(f"错误: {msg}")
        self._toggle_ui(True)
        self.running = False
        self.run_btn.configure(state="normal")
        messagebox.showerror("处理出错", msg)

    def run(self):
        self.root.mainloop()


def main():
    app = LexiGUI()
    app.run()


if __name__ == "__main__":
    main()
