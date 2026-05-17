import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable

from .config import LexiConfig, load_config, save_config
from .pipeline import run_pipeline
from .story import StoryGenerator, StoryResult, _load_word_infos_from_json, _save_story_markdown
from .styles import StyleManager, Style


@dataclass
class OutputOptions:
    markdown: bool = True
    json: bool = True
    csv: bool = False
    html: bool = False
    anki: bool = False


@dataclass
class ClassifyResult:
    output_files: Dict[str, str] = field(default_factory=dict)
    total_words: int = 0


class LexiController:
    def __init__(self, config: Optional[LexiConfig] = None):
        self._config = config or load_config()
        self._style_manager = StyleManager()

    @property
    def config(self) -> LexiConfig:
        return self._config

    @config.setter
    def config(self, cfg: LexiConfig) -> None:
        self._config = cfg

    def save_config(self, path: Optional[str] = None) -> str:
        return save_config(self._config, path)

    def load_config(self, path: Optional[str] = None) -> LexiConfig:
        self._config = load_config(path)
        return self._config

    @property
    def styles(self) -> StyleManager:
        return self._style_manager

    def classify(
        self,
        input_file: str,
        categories_path: str = "data/categories_full.json",
        stopwords_path: str = "data/stopwords.txt",
        overrides_path: Optional[str] = None,
        outputs: Optional[OutputOptions] = None,
        output_dir: str = ".",
        base_name: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> ClassifyResult:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")

        base = base_name or os.path.splitext(os.path.basename(input_file))[0]
        opts = outputs or OutputOptions()
        output_map: Dict[str, str] = {}

        def _path(ext: str) -> Optional[str]:
            if ext == "anki":
                full = f"{base}_output.apkg"
            else:
                full = f"{base}_output.{ext}"
            p = os.path.join(output_dir, full)
            output_map[ext] = p
            return p

        run_pipeline(
            input_file=input_file,
            categories_json=categories_path,
            stopwords_txt=stopwords_path,
            overrides_json=overrides_path,
            output_md=_path("md") if opts.markdown else None,
            output_json=_path("json") if opts.json else None,
            output_csv=_path("csv") if opts.csv else None,
            output_html=_path("html") if opts.html else None,
            output_anki=_path("anki") if opts.anki else None,
            progress_callback=progress_callback,
            status_callback=status_callback,
        )

        total_words = 0
        json_path = output_map.get("json")
        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                total_words = data.get("total_words", 0)
            except (json.JSONDecodeError, OSError):
                pass

        return ClassifyResult(output_files=output_map, total_words=total_words)

    def generate_story(
        self,
        input_json: str,
        output_dir: str = ".",
        base_name: Optional[str] = None,
        word_list: Optional[List[str]] = None,
        count: int = 20,
        strategy: str = "balanced",
        length: str = "medium",
        language: str = "en",
        style: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> StoryResult:
        if not os.path.exists(input_json):
            raise FileNotFoundError(f"Input JSON not found: {input_json}")

        base = base_name or os.path.splitext(os.path.basename(input_json))[0]
        story_md = os.path.join(output_dir, f"{base}_story.md")

        style_text: Optional[str] = None
        if style:
            try:
                style_obj = self._style_manager.get_style(style)
                style_text = style_obj.body
            except FileNotFoundError:
                raise ValueError(
                    f"Style '{style}' not found. "
                    f"Available: {', '.join(self._style_manager.style_names())}"
                )

        if status_callback:
            status_callback("Loading classified words...")
        word_infos = _load_word_infos_from_json(input_json)
        if not word_infos:
            raise ValueError(
                f"No classified words found in {input_json}. "
                "Run classification first."
            )

        generator = StoryGenerator(self._config)

        if word_list:
            words = [w.strip().lower() for w in word_list if w.strip()]
            unknown = [w for w in words if w not in word_infos]
            if unknown and status_callback:
                status_callback(f"Warning: {len(unknown)} words not in classified set")
            words = [w for w in words if w in word_infos]
            if not words:
                raise ValueError("None of the specified words were found in the classified set")
        else:
            if status_callback:
                status_callback(f"Selecting {count} words ({strategy})...")
            words = generator.select_words(word_infos, count=count, strategy=strategy)
            if not words:
                raise ValueError("No words available for selection")

        if status_callback:
            status_callback(f"Generating story with {len(words)} words...")

        result = generator.generate_story(
            words=words,
            word_infos=word_infos,
            length=length,
            language=language,
            style_text=style_text,
            progress_callback=progress_callback,
            status_callback=status_callback,
        )

        _save_story_markdown(result, story_md, word_infos)

        return result
