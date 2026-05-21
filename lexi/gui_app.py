"""LexiApp — GUI state and actions, decoupled from any UI framework."""

import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lexi.controller import LexiController, OutputOptions
from lexi.learned import LearnedDB
from lexi.stats import StatsTracker


class LexiApp:
    """Holds all mutable state and business-logic actions for the Lexi GUI.
    Pure Python — no Flet/tkinter imports. The view layer reads state
    attributes and calls action methods."""

    def __init__(self):
        self.ctrl = LexiController()
        self.learned_db = LearnedDB()
        self.stats = StatsTracker()
        self.stats.start_session()
        self.running = False
        self.output_dir = os.path.dirname(os.path.abspath(__file__)) or "."
        self.last_output_json = None
        self.last_base = ""
        self.last_story_md = None

        # ── Input paths ──
        self.input_file = ""
        self.categories_path = os.path.join(self.output_dir, "data", "categories_full.json")
        self.stopwords_path = os.path.join(self.output_dir, "data", "stopwords.txt")
        self.overrides_path = ""
        self.output_path = self.output_dir

        # ── Output format flags ──
        self.opt_md = True
        self.opt_json = True
        self.opt_csv = True
        self.opt_html = True
        self.opt_anki = False

        # ── Story params ──
        self.story_count = 20
        self.story_strategy = "balanced"
        self.story_length = "medium"
        self.story_style = None
        self.story_words = ""

        # ── Callbacks (set by view) ──
        self.on_log = lambda msg, tag="": None
        self.on_progress = lambda pct: None
        self.on_status = lambda msg: None
        self.on_story_toggle = lambda enabled: None
        self.on_story_result = lambda result: None
        self.on_classify_done = lambda json_path: None
        self.on_classify_error = lambda msg: None
        self.on_story_error = lambda msg: None
        self.on_nav = lambda idx: None  # 导航回调，由 main.py 设置

    # ── Actions ──────────────────────────────────────────────

    def run_classify(self):
        if self.running:
            return
        f = self.input_file
        if not f:
            self.on_log("请选择输入文件", "ok")
            return
        if not os.path.exists(f):
            self.on_log(f"文件不存在: {f}", "ok")
            return
        self.last_base = os.path.splitext(os.path.basename(f))[0]
        self.running = True
        self.last_output_json = None
        self.last_story_md = None
        self.on_log("Lexi 词汇分类工具 v3.0", "dim")
        self.on_log("─" * 36, "dim")

        def run():
            try:
                self.ctrl.classify(
                    input_file=f,
                    categories_path=self.categories_path,
                    stopwords_path=self.stopwords_path if os.path.exists(self.stopwords_path) else "data/stopwords.txt",
                    overrides_path=self.overrides_path if self.overrides_path and os.path.exists(self.overrides_path) else None,
                    outputs=OutputOptions(
                        markdown=self.opt_md, json=self.opt_json,
                        csv=self.opt_csv, html=self.opt_html, anki=self.opt_anki,
                    ),
                    output_dir=self.output_path,
                    base_name=self.last_base,
                    status_callback=lambda m: self.on_status(m.strip()),
                    progress_callback=self.on_progress,
                )
                self.on_log("─" * 36, "dim")
                self.on_log("✓ 分类完成。AI 短文生成已就绪。", "ok")
                jp = os.path.join(self.output_path, f"{self.last_base}_output.json")
                if os.path.exists(jp):
                    self.last_output_json = jp
                    self._import_to_learned(jp)
                    self.on_classify_done(jp)
            except Exception as e:
                self.on_log(f"错误: {e}", "ok")
                self.on_classify_error(str(e))
            finally:
                self.running = False
                self.on_progress(1.0)

        threading.Thread(target=run, daemon=True).start()

    def run_story(self):
        if self.running:
            return
        if not self.last_output_json:
            self.on_log("请先运行分类", "ok")
            return
        wl = [x.strip() for x in self.story_words.split(",") if x.strip()] if self.story_words.strip() else None
        out = self.output_path
        sn = self.story_style

        self.running = True
        self.on_story_toggle(False)
        self.on_log("", "dim")
        self.on_log("─" * 36, "dim")
        self.on_log("AI 短文生成中...", "dim")

        def run():
            try:
                result = self.ctrl.generate_story(
                    input_json=self.last_output_json, output_dir=out,
                    word_list=wl, count=self.story_count,
                    strategy=self.story_strategy,
                    length=self.story_length,
                    language="zh", style=sn,
                    progress_callback=self.on_progress,
                    status_callback=lambda m: self.on_status(m.strip()),
                )
                self.last_story_md = os.path.join(out, f"{self.last_base}_story.md")
                self.on_story_result(result)
            except Exception as e:
                self.on_log(f"错误: {e}", "ok")
                self.on_story_error(str(e))
            finally:
                self.running = False
                self.on_story_toggle(True)
                self.on_progress(1.0)

        threading.Thread(target=run, daemon=True).start()

    def refresh_styles(self):
        return self.ctrl.styles.style_names()

    def _import_to_learned(self, json_path):
        """Import all words from classified JSON into learning state."""
        try:
            import json
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            words = set()
            for main_cat in data.get("categories", {}).values():
                for entries in main_cat.values():
                    for entry in entries:
                        words.add(entry["word"])
            self.learned_db.import_words(list(words))
            import threading
            threading.Thread(
                target=lambda: self.learned_db.generate_meanings(self.ctrl.config),
                daemon=True).start()
        except Exception:
            pass

    def save_api_config(self, api_key, api_url, model):
        self.ctrl.config.api_key = api_key
        self.ctrl.config.api_base_url = api_url
        self.ctrl.config.model = model
        self.ctrl.save_config()
