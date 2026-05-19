"""AI exercise generation — cloze, multiple-choice, sentence checking, definitions."""

import json
import re
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .config import LexiConfig
from .models import WordInfo


@dataclass
class ExerciseItem:
    sentence: str = ""
    blank_word: str = ""
    options: List[str] = field(default_factory=list)
    correct: str = ""
    definition: str = ""
    word: str = ""


@dataclass
class Exercise:
    type: str = ""
    prompt: str = ""
    items: List[ExerciseItem] = field(default_factory=list)


class ExerciseGenerator:
    def __init__(self, config: LexiConfig):
        self.config = config
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            if not self.config.api_key:
                raise ValueError("API key not configured. Run: python cli.py config")
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base_url,
            )
        return self._client

    def _call(self, system_msg: str, user_msg: str) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content or ""

    def generate_cloze(
        self, words: List[str],
        word_infos: Optional[Dict[str, WordInfo]] = None,
        count: int = 5,
    ) -> Exercise:
        word_list = ", ".join(words[:min(20, len(words))])
        system_msg = "You are an English teacher creating fill-in-the-blank exercises."
        user_msg = (
            f"Create {count} sentences for a cloze exercise.\n"
            f"Each sentence must use ONE of these target words: {word_list}\n"
            f"Replace the target word with ______ in the sentence.\n"
            f"The sentence should provide enough context to guess the word.\n\n"
            f"Output format (JSON array):\n"
            f'[{{"sentence": "The ______ was unexpected.", "word": "outcome"}}]\n\n'
            f"Output ONLY valid JSON. No other text."
        )
        result = self._call(system_msg, user_msg)
        items = self._parse_cloze(result, words)
        return Exercise(type="cloze", prompt=f"填入正确的单词（{len(items)} 题）", items=items)

    def _parse_cloze(self, text: str, words: List[str]) -> List[ExerciseItem]:
        try:
            data = json.loads(self._extract_json(text))
        except json.JSONDecodeError:
            data = []
        items = []
        word_set = {w.lower() for w in words}
        for d in data:
            w = d.get("word", "")
            if w.lower() in word_set:
                items.append(ExerciseItem(
                    sentence=d.get("sentence", ""),
                    blank_word=w,
                    correct=w,
                ))
        return items[:len(words)]

    def generate_choice(
        self, words: List[str],
        word_infos: Optional[Dict[str, WordInfo]] = None,
        count: int = 5,
    ) -> Exercise:
        selected = words[:min(count, len(words))]
        word_list = ", ".join(selected)
        system_msg = "You are an English vocabulary teacher creating multiple-choice questions."
        user_msg = (
            f"Create a multiple-choice question for EACH of these words: {word_list}\n"
            f"For each word, write a question that tests understanding of its meaning.\n"
            f"Provide 4 options (A/B/C/D) where one is correct and 3 are plausible distractors.\n\n"
            f"Output format (JSON array):\n"
            f'[{{"word": "outcome", "question": "What does outcome mean?", '
            f'"options": ["result", "income", "outline", "outcry"], "correct": "result"}}]\n\n'
            f"Output ONLY valid JSON. No other text."
        )
        result = self._call(system_msg, user_msg)
        try:
            data = json.loads(self._extract_json(result))
        except json.JSONDecodeError:
            data = []
        items = []
        for d in data:
            items.append(ExerciseItem(
                word=d.get("word", ""),
                sentence=d.get("question", ""),
                options=d.get("options", []),
                correct=d.get("correct", ""),
            ))
        return Exercise(type="choice", prompt=f"选择题（{len(items)} 题）", items=items)

    def check_sentence(self, sentence: str, word: str) -> str:
        system_msg = (
            "You are an English writing tutor. Check the student's sentence "
            "for grammar, spelling, and correct usage of the target word. "
            "Provide a corrected version if needed, and rate the usage 1-5."
        )
        user_msg = (
            f"Target word: {word}\n"
            f"Student sentence: {sentence}\n\n"
            f"Reply in Chinese with:\n"
            f"1. 用法评分: X/5\n"
            f"2. 是否正确使用了 '{word}'？\n"
            f"3. 语法问题（如有）\n"
            f"4. 修改建议（如有）"
        )
        return self._call(system_msg, user_msg)

    def generate_definitions(
        self, words: List[str],
        word_infos: Optional[Dict[str, WordInfo]] = None,
    ) -> Exercise:
        word_list = ", ".join(words[:min(20, len(words))])
        system_msg = "You are a dictionary editor. Write clear, concise English definitions."
        user_msg = (
            f"Write a short English definition for each word: {word_list}\n\n"
            f"Output format (JSON array):\n"
            f'[{{"word": "outcome", "definition": "The final result or consequence of an action or event"}}]\n\n'
            f"Output ONLY valid JSON. No other text."
        )
        result = self._call(system_msg, user_msg)
        try:
            data = json.loads(self._extract_json(result))
        except json.JSONDecodeError:
            data = []
        items = []
        word_set = {w.lower() for w in words}
        seen = set()
        for d in data:
            w = d.get("word", "")
            if w.lower() in word_set and w.lower() not in seen:
                seen.add(w.lower())
                items.append(ExerciseItem(
                    word=w,
                    definition=d.get("definition", ""),
                    correct=w,
                ))
        random.shuffle(items)
        return Exercise(
            type="definition",
            prompt=f"将以下单词与其释义连线（{len(items)} 对）",
            items=items,
        )

    @staticmethod
    def _extract_json(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```\w*\n?", "", text)
            text = re.sub(r"\n```$", "", text)
        m = re.search(r"\[.*\]", text, re.DOTALL)
        return m.group(0) if m else "[]"
