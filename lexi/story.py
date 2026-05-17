import json
import os
import random
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable

from .models import WordInfo, ClassificationResult
from .config import LexiConfig, load_config

LENGTH_TARGETS = {"short": 100, "medium": 250, "long": 500}


@dataclass
class StoryResult:
    passage: str = ""
    words_used: List[str] = field(default_factory=list)
    words_missed: List[str] = field(default_factory=list)
    word_count: int = 0
    model: str = ""
    tokens_prompt: int = 0
    tokens_completion: int = 0


class StoryGenerator:
    def __init__(self, config: LexiConfig):
        self.config = config
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "Missing dependency 'openai'. Run: pip install openai"
                )
            if not self.config.api_key:
                raise ValueError(
                    "API key not configured. Run: python cli.py config --api-key <key>"
                )
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base_url,
            )
        return self._client

    def select_words(
        self,
        word_infos: Dict[str, WordInfo],
        count: int = 20,
        strategy: str = "balanced",
        exclude: Optional[List[str]] = None,
    ) -> List[str]:
        exclude_set = set(exclude or [])
        available = {
            w: wi for w, wi in word_infos.items()
            if w not in exclude_set and wi.classifications
        }
        if len(available) < count:
            count = len(available)
        if count == 0:
            return []

        if strategy == "top_frequency":
            sorted_words = sorted(
                available.keys(),
                key=lambda w: available[w].zipf_frequency,
                reverse=True,
            )
            return sorted_words[:count]

        if strategy == "random":
            return random.sample(list(available.keys()), count)

        if strategy == "balanced":
            buckets = defaultdict(list)
            for w, wi in available.items():
                cat = wi.primary_category()
                if cat:
                    buckets[cat].append(w)
            for cat in buckets:
                buckets[cat].sort(
                    key=lambda w: available[w].zipf_frequency, reverse=True
                )
            selected = []
            cat_names = list(buckets.keys())
            while len(selected) < count and cat_names:
                for cat in cat_names:
                    if buckets[cat]:
                        selected.append(buckets[cat].pop(0))
                        if len(selected) >= count:
                            break
                cat_names = [c for c in cat_names if buckets[c]]
            return selected[:count]

        if strategy == "stratified":
            buckets = defaultdict(list)
            for w, wi in available.items():
                cat = wi.primary_category()
                sub = wi.primary_sub_category()
                if cat and sub:
                    buckets[(cat, sub)].append(w)
            for key in buckets:
                buckets[key].sort(
                    key=lambda w: available[w].zipf_frequency, reverse=True
                )
            selected = []
            total = sum(len(v) for v in buckets.values())
            for key, words in buckets.items():
                quota = max(1, int(count * len(words) / total))
                selected.extend(words[:quota])
            while len(selected) < count:
                for key in buckets:
                    already = sum(1 for w in selected if w in buckets[key])
                    if already < len(buckets[key]):
                        remaining = [w for w in buckets[key] if w not in selected]
                        if remaining:
                            selected.append(remaining[0])
                            if len(selected) >= count:
                                break
            return selected[:count]

        return list(available.keys())[:count]

    @staticmethod
    def _build_prompt(
        words: List[str],
        word_infos: Optional[Dict[str, WordInfo]] = None,
        length: str = "medium",
        language: str = "en",
        style_text: Optional[str] = None,
    ) -> tuple:
        target_count = LENGTH_TARGETS.get(length, 250)
        cefr_levels = set()
        word_lines = []
        for w in words:
            if word_infos and w in word_infos:
                wi = word_infos[w]
                cefr = wi.cefr_level or "?"
                cefr_levels.add(cefr)
                word_lines.append(f"{w} ({cefr})")
            else:
                word_lines.append(w)
        cefr_range = ", ".join(sorted(cefr_levels)) if cefr_levels else "mixed"

        if language == "zh":
            system_msg = (
                "你是一位语言学习内容创作者。"
                "你的任务是为英语学习者撰写短文，帮助他们在语境中掌握词汇。"
            )
            if style_text:
                system_msg += (
                    "\n\n请模仿以下参考文本的写作风格来写这篇短文。"
                    "注意其句式结构、用词选择、语气和节奏。\n\n"
                    f"参考风格文本：\n{style_text}\n"
                )
            user_msg = (
                f"请用以下英语词汇写一篇短文。短文必须是连贯的叙事，不是零散的句子。\n\n"
                f"要求：\n"
                f"- 必须使用列表中的每一个单词至少一次\n"
                f"- 每个目标单词首次出现时，用 **加粗** 标记，例如 **abandon**\n"
                f"- 短文约 {target_count} 词\n"
                f"- 语言自然流畅，像为真实读者写的一样\n"
                f"- 只输出短文本身，不要任何解释、说明或标题\n\n"
                f"目标词汇（{len(words)} 个，CEFR 范围 {cefr_range}）：\n"
                + "\n".join(word_lines)
            )
        else:
            system_msg = (
                "You are a language learning content creator. "
                "Your task is to write short English passages that help "
                "learners acquire vocabulary through context."
            )
            if style_text:
                system_msg += (
                    "\n\nMimic the writing style of the following reference "
                    "text. Pay attention to its sentence structure, word "
                    "choice, tone, and rhythm.\n\n"
                    f"Reference style text:\n{style_text}\n"
                )
            user_msg = (
                f"Write a short English passage that naturally incorporates "
                f"ALL of the following vocabulary words. The passage should be "
                f"a coherent narrative, not disconnected sentences or a list.\n\n"
                f"Requirements:\n"
                f"- Use EVERY word in the list below at least once\n"
                f"- The first time each target word appears, highlight it with "
                f"**bold** like **this**\n"
                f"- Write approximately {target_count} words total\n"
                f"- The passage should read naturally — as if written for a real audience\n"
                f"- Output ONLY the passage. No explanations, no commentary, no headings\n\n"
                f"Target words ({len(words)} words, CEFR range {cefr_range}):\n"
                + "\n".join(word_lines)
            )

        return system_msg, user_msg

    def generate_story(
        self,
        words: List[str],
        word_infos: Optional[Dict[str, WordInfo]] = None,
        length: str = "medium",
        language: str = "en",
        style_text: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> StoryResult:
        words = list(dict.fromkeys(words))
        if not words:
            raise ValueError("Word list is empty")
        if len(words) > 50:
            raise ValueError(f"Too many words ({len(words)}). Maximum is 50.")

        if status_callback:
            status_callback("Building prompt...")
        if progress_callback:
            progress_callback(0.1)

        system_msg, user_msg = self._build_prompt(words, word_infos, length, language, style_text)

        if status_callback:
            status_callback(f"Calling {self.config.model}...")
        if progress_callback:
            progress_callback(0.2)

        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        except Exception as e:
            msg = str(e)
            if "401" in msg or "Unauthorized" in msg or "authentication" in msg.lower():
                raise ValueError(
                    f"Authentication failed. Check your API key.\n"
                    f"Config: {self.config.api_base_url}\n"
                    f"Run: python cli.py config --api-key <key>"
                ) from e
            if "429" in msg or "rate" in msg.lower():
                raise ValueError(
                    "Rate limit hit. Wait and retry, or use a different model."
                ) from e
            if "timeout" in msg.lower() or "connection" in msg.lower():
                raise ValueError(
                    f"Connection failed. Check api_base_url or network.\n"
                    f"Current: {self.config.api_base_url}"
                ) from e
            raise

        if progress_callback:
            progress_callback(0.6)

        passage = response.choices[0].message.content or ""
        passage = passage.strip()
        if passage.startswith("```"):
            passage = re.sub(r"^```\w*\n?", "", passage)
            passage = re.sub(r"\n```$", "", passage)

        if status_callback:
            status_callback("Verifying word usage...")
        if progress_callback:
            progress_callback(0.8)

        used, missed = _verify_word_usage(passage, words)

        word_count = len(passage.split())

        if status_callback:
            status_callback("Done")
        if progress_callback:
            progress_callback(1.0)

        return StoryResult(
            passage=passage,
            words_used=used,
            words_missed=missed,
            word_count=word_count,
            model=self.config.model,
            tokens_prompt=response.usage.prompt_tokens if response.usage else 0,
            tokens_completion=response.usage.completion_tokens if response.usage else 0,
        )


def generate_story(
    input_json: str,
    output_md: str = "story.md",
    word_list: Optional[List[str]] = None,
    count: int = 20,
    strategy: str = "balanced",
    length: str = "medium",
    language: str = "en",
    config_path: Optional[str] = None,
    api_key: Optional[str] = None,
    api_base_url: Optional[str] = None,
    model: Optional[str] = None,
    progress_callback: Optional[Callable[[float], None]] = None,
    status_callback: Optional[Callable[[str], None]] = None,
) -> StoryResult:
    if status_callback:
        status_callback("Loading classified words...")
    if progress_callback:
        progress_callback(0.05)

    word_infos = _load_word_infos_from_json(input_json)
    if not word_infos:
        raise ValueError(
            f"No classified words found in {input_json}. "
            "Run classification first: python cli.py <input> --output-json <json>"
        )

    config = load_config(config_path)
    if api_key:
        config.api_key = api_key
    if api_base_url:
        config.api_base_url = api_base_url
    if model:
        config.model = model

    generator = StoryGenerator(config)

    if word_list:
        words = [w.strip().lower() for w in word_list if w.strip()]
        unknown = [w for w in words if w not in word_infos]
        if unknown:
            if status_callback:
                status_callback(f"Warning: {len(unknown)} words not in classified set")
            words = [w for w in words if w in word_infos]
        if not words:
            raise ValueError("None of the specified words were found in the classified set")
    else:
        if status_callback:
            status_callback(f"Selecting {count} words ({strategy})...")
        if progress_callback:
            progress_callback(0.1)
        words = generator.select_words(word_infos, count=count, strategy=strategy)
        if not words:
            raise ValueError("No words available for selection")

    if status_callback:
        status_callback(f"Generating story with {len(words)} words...")
    if progress_callback:
        progress_callback(0.15)

    result = generator.generate_story(
        words=words,
        word_infos=word_infos,
        length=length,
        language=language,
        progress_callback=lambda p: progress_callback(0.15 + p * 0.7) if progress_callback else None,
        status_callback=status_callback,
    )

    if status_callback:
        status_callback("Saving story...")
    if progress_callback:
        progress_callback(0.9)

    _save_story_markdown(result, output_md, word_infos)

    if progress_callback:
        progress_callback(1.0)

    return result


def _load_word_infos_from_json(path: str) -> Dict[str, WordInfo]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    word_map: Dict[str, WordInfo] = {}
    categories = data.get("categories", {})
    for main_cat, sub_cats in categories.items():
        for sub_cat, entries in sub_cats.items():
            for entry in entries:
                w = entry["word"]
                cr = ClassificationResult(
                    main_category=main_cat,
                    sub_category=sub_cat,
                    confidence=entry.get("confidence", 1.0),
                    source=entry.get("source", "dictionary"),
                )
                if w in word_map:
                    word_map[w].classifications.append(cr)
                else:
                    word_map[w] = WordInfo(
                        word=w,
                        classifications=[cr],
                        zipf_frequency=entry.get("zipf", 0.0),
                        cefr_level=entry.get("cefr", ""),
                    )
    return word_map


def _save_story_markdown(
    result: StoryResult,
    path: str,
    word_infos: Optional[Dict[str, WordInfo]] = None,
):
    lines = [
        "# AI 生成短文\n",
        f"- **模型**: {result.model}",
        f"- **目标词汇**: {len(result.words_used) + len(result.words_missed)}",
        f"- **已使用**: {len(result.words_used)}",
        f"- **短文词数**: {result.word_count}",
    ]
    if result.tokens_prompt:
        lines.append(f"- **Tokens**: {result.tokens_prompt} prompt + {result.tokens_completion} completion")

    lines.append("\n---\n")
    lines.append(result.passage)
    lines.append("\n---\n")
    lines.append("## 目标词汇\n")
    lines.append("| 单词 | 分类 | CEFR | 状态 |")
    lines.append("|------|------|------|------|")

    for w in result.words_used:
        cat_path = ""
        cefr = ""
        if word_infos and w in word_infos:
            wi = word_infos[w]
            cat_path = f"{wi.primary_category()} › {wi.primary_sub_category()}"
            cefr = wi.cefr_level
        lines.append(f"| **{w}** | {cat_path} | {cefr} | ✓ |")

    for w in result.words_missed:
        cat_path = ""
        cefr = ""
        if word_infos and w in word_infos:
            wi = word_infos[w]
            cat_path = f"{wi.primary_category()} › {wi.primary_sub_category()}"
            cefr = wi.cefr_level
        lines.append(f"| {w} | {cat_path} | {cefr} | ✗ 未使用 |")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _verify_word_usage(passage: str, words: List[str]) -> tuple:
    used = []
    missed = []
    passage_lower = passage.lower()
    for w in words:
        pattern = re.compile(r"\b" + re.escape(w.lower()) + r"\b")
        if pattern.search(passage_lower):
            used.append(w)
        else:
            display = w.replace("_", " ")
            if display != w and re.compile(r"\b" + re.escape(display.lower()) + r"\b").search(passage_lower):
                used.append(w)
            else:
                missed.append(w)
    return used, missed
