import json
import os
import random
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable

from .models import WordInfo, ClassificationResult
from .config import LexiConfig, load_config
from .style_analyzer import StyleProfile

LENGTH_TARGETS = {"short": 100, "medium": 250, "long": 500}
REPETITIONS = {"short": 3, "medium": 4, "long": 5}
WORDS_PER_TARGET = 13


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
        style_profile: Optional[StyleProfile] = None,
        style_name: str = "",
    ) -> tuple:
        reps = REPETITIONS.get(length, 3)
        passage_length = max(120, len(words) * WORDS_PER_TARGET)
        spacing = max(3, passage_length // (len(words) * reps)) if words else 8
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
            if style_profile and style_profile.avg_sentence_length > 0:
                system_msg += _build_style_constraints_zh(style_profile, style_name)
            user_msg = (
                f"请用以下英语词汇写一篇短文。短文必须是连贯的叙事，不是零散的句子。\n\n"
                f"要求：\n"
                f"- 每个目标单词必须在短文中出现至少 {reps} 次（在上下文中自然重复）\n"
                f"- 目标词密度：约每 {spacing} 个词出现 1 个目标词实例\n"
                f"- 每个目标单词首次出现时，用 **加粗** 标记，例如 **abandon**\n"
                f"- 短文约 {passage_length} 词\n"
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
            if style_profile and style_profile.avg_sentence_length > 0:
                system_msg += _build_style_constraints_en(style_profile, style_name)
            user_msg = (
                f"Write a short English passage that naturally incorporates "
                f"ALL of the following vocabulary words. The passage should be "
                f"a coherent narrative, not disconnected sentences or a list.\n\n"
                f"Requirements:\n"
                f"- Use EVERY word at least {reps} times, repeating naturally in context\n"
                f"- Target word density: roughly 1 target word per {spacing} words of text\n"
                f"- The first time each target word appears, highlight it with "
                f"**bold** like **this**\n"
                f"- Write approximately {passage_length} words total\n"
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
        style_profile: Optional[StyleProfile] = None,
        style_name: str = "",
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

        system_msg, user_msg = self._build_prompt(words, word_infos, length, language, style_profile, style_name)

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


def _build_style_constraints_en(profile: StyleProfile, style_name: str) -> str:
    label = f' style "{style_name}"' if style_name else ""
    parts = [
        f"\n\nApply these specific writing constraints derived from"
        f" quantitative analysis of the reference{label}:\n",
    ]
    if profile.avg_sentence_length > 0:
        parts.append(
            f"Sentence structure:\n"
            f"- Target average sentence length: ~{profile.avg_sentence_length:.0f} words\n"
            f"- Vary sentence length naturally (reference σ = {profile.sentence_length_std:.1f})\n"
        )
    if profile.avg_word_length > 0:
        parts.append(
            f"Vocabulary:\n"
            f"- Average word length: ~{profile.avg_word_length:.1f} characters\n"
        )
    if profile.type_token_ratio > 0:
        parts.append(
            f"- Vocabulary diversity (TTR): ~{profile.type_token_ratio:.2f}\n"
        )
    if profile.cefr_distribution:
        parts.append(f"- Target CEFR range: {profile.dominant_cefr()}\n")
    if profile.passive_voice_ratio > 0:
        parts.append(
            f"Voice:\n"
            f"- Passive voice: ~{profile.passive_voice_ratio*100:.0f}% of verb constructions\n"
        )
    if profile.flesch_kincaid_grade > 0:
        parts.append(
            f"Readability:\n"
            f"- Flesch-Kincaid grade level: ~{profile.flesch_kincaid_grade:.1f}\n"
            f"- Flesch Reading Ease: ~{profile.flesch_reading_ease:.1f}\n"
        )
    if any([
        profile.nominalization_ratio, profile.modifier_density,
        profile.lexical_density, profile.subordination_ratio,
        profile.coordination_ratio, profile.transition_density,
        profile.pronoun_density,
    ]):
        parts.append("Grammar and syntax:")
        if profile.nominalization_ratio > 0:
            parts.append(
                f"- Nominalization: ~{profile.nominalization_ratio*100:.0f}% of words "
                f"(use of -tion/-ment/-ity/-ness etc.)"
            )
        if profile.modifier_density > 0:
            parts.append(
                f"- Modifier density: ~{profile.modifier_density:.2f} "
                f"(adjectives + adverbs per content word)"
            )
        if profile.lexical_density > 0:
            parts.append(
                f"- Lexical density: ~{profile.lexical_density:.2f} "
                f"(content words ratio, i.e. information density)"
            )
        if profile.subordination_ratio > 0:
            parts.append(
                f"- Subordination: ~{profile.subordination_ratio:.1f} per sentence "
                f"(use of although/because/while/if/when clauses)"
            )
        if profile.coordination_ratio > 0:
            parts.append(
                f"- Coordination: ~{profile.coordination_ratio:.1f} per sentence "
                f"(use of and/but/or connections)"
            )
        if profile.transition_density > 0:
            parts.append(
                f"- Transition words: ~{profile.transition_density:.1f} per 100 words "
                f"(however/therefore/moreover etc.)"
            )
        if profile.pronoun_density > 0:
            parts.append(
                f"- Pronoun density: ~{profile.pronoun_density*100:.0f}% pronouns "
                f"(personal vs. impersonal style)"
            )
    return "\n".join(parts)


def _build_style_constraints_zh(profile: StyleProfile, style_name: str) -> str:
    label = f'风格 "{style_name}"' if style_name else ""
    parts = [
        f"\n\n请应用以下从参考{label}中量化分析得出的写作约束：\n",
    ]
    if profile.avg_sentence_length > 0:
        parts.append(
            f"句子结构：\n"
            f"- 目标平均句长：约 {profile.avg_sentence_length:.0f} 词\n"
            f"- 句长自然变化（参考 σ = {profile.sentence_length_std:.1f}）\n"
        )
    if profile.avg_word_length > 0:
        parts.append(
            f"词汇：\n"
            f"- 平均词长：约 {profile.avg_word_length:.1f} 字符\n"
        )
    if profile.type_token_ratio > 0:
        parts.append(
            f"- 词汇多样性（型例比）：约 {profile.type_token_ratio:.2f}\n"
        )
    if profile.cefr_distribution:
        parts.append(f"- 目标 CEFR 范围：{profile.dominant_cefr()}\n")
    if profile.passive_voice_ratio > 0:
        parts.append(
            f"语态：\n"
            f"- 被动语态：约 {profile.passive_voice_ratio*100:.0f}% 的动词结构\n"
        )
    if profile.flesch_kincaid_grade > 0:
        parts.append(
            f"可读性：\n"
            f"- Flesch-Kincaid 年级水平：约 {profile.flesch_kincaid_grade:.1f}\n"
        )
    if any([
        profile.nominalization_ratio, profile.modifier_density,
        profile.lexical_density, profile.subordination_ratio,
        profile.coordination_ratio, profile.transition_density,
        profile.pronoun_density,
    ]):
        parts.append("语法与句法：")
        if profile.nominalization_ratio > 0:
            parts.append(
                f"- 名物化比例：约 {profile.nominalization_ratio*100:.0f}% "
                f"（-tion/-ment/-ity/-ness 等结尾词的使用密度）"
            )
        if profile.modifier_density > 0:
            parts.append(
                f"- 修饰词密度：约 {profile.modifier_density:.2f} "
                f"（形容词+副词 与 实词的比值）"
            )
        if profile.lexical_density > 0:
            parts.append(
                f"- 实词密度：约 {profile.lexical_density:.2f} "
                f"（信息密度指标）"
            )
        if profile.subordination_ratio > 0:
            parts.append(
                f"- 从属连词比例：约 {profile.subordination_ratio:.1f} 个/句 "
                f"（although/because/while/if/when 等从句）"
            )
        if profile.coordination_ratio > 0:
            parts.append(
                f"- 并列连词比例：约 {profile.coordination_ratio:.1f} 个/句 "
                f"（and/but/or 等连接）"
            )
        if profile.transition_density > 0:
            parts.append(
                f"- 过渡词密度：约 {profile.transition_density:.1f} 个/100词 "
                f"（however/therefore/moreover 等）"
            )
        if profile.pronoun_density > 0:
            parts.append(
                f"- 代词密度：约 {profile.pronoun_density*100:.0f}% "
                f"（人称化 vs. 非人称化风格）"
            )
    return "\n".join(parts)
