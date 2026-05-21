"""Multi-wordbook management."""

import json
import os
from dataclasses import dataclass, asdict
from datetime import date
from typing import List, Optional


DEFAULT_BOOKS_DIR = os.path.expanduser("~/.lexi/wordbooks")


@dataclass
class WordBook:
    name: str
    words: List[str]
    created: str = ""
    description: str = ""


class WordBookManager:
    def __init__(self, books_dir: Optional[str] = None):
        self.books_dir = books_dir or DEFAULT_BOOKS_DIR
        os.makedirs(self.books_dir, exist_ok=True)

    def list_books(self) -> List[str]:
        books = []
        for f in sorted(os.listdir(self.books_dir)):
            if f.endswith(".json"):
                books.append(f[:-5])
        return books

    def load_book(self, name: str) -> WordBook:
        path = os.path.join(self.books_dir, f"{name}.json")
        if not os.path.exists(path):
            return WordBook(name=name, words=[], created=date.today().isoformat())
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return WordBook(name=d["name"], words=d["words"],
                        created=d.get("created", ""), description=d.get("description", ""))

    def save_book(self, book: WordBook):
        path = os.path.join(self.books_dir, f"{book.name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(book), f, ensure_ascii=False, indent=2)

    def delete_book(self, name: str):
        path = os.path.join(self.books_dir, f"{name}.json")
        if os.path.exists(path):
            os.remove(path)

    def create_from_filter(self, learned_db, name: str, status: Optional[str] = None,
                           cefr: Optional[str] = None, description: str = "") -> WordBook:
        words = []
        for ws in learned_db.get_all():
            if status and ws.status != status:
                continue
            if cefr:
                pass  # learned_db entries don't have CEFR; skip filter
            words.append(ws.word)
        book = WordBook(name=name, words=words,
                        created=date.today().isoformat(), description=description)
        self.save_book(book)
        return book
