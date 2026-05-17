import json
import os
from dataclasses import dataclass, field
from typing import Optional


DEFAULT_CONFIG_DIR = os.path.expanduser("~/.lexi")
DEFAULT_CONFIG_PATH = os.path.join(DEFAULT_CONFIG_DIR, "config.json")


@dataclass
class LexiConfig:
    api_key: str = ""
    api_base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    temperature: float = 0.8
    max_tokens: int = 2048


def load_config(path: Optional[str] = None) -> LexiConfig:
    config = LexiConfig()
    file_path = path or DEFAULT_CONFIG_PATH
    if not os.path.exists(file_path):
        return config
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for key in ("api_key", "api_base_url", "model", "temperature", "max_tokens"):
        if key in data:
            setattr(config, key, data[key])
    return config


def save_config(config: LexiConfig, path: Optional[str] = None) -> str:
    file_path = path or DEFAULT_CONFIG_PATH
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump({
            "api_key": config.api_key,
            "api_base_url": config.api_base_url,
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }, f, ensure_ascii=False, indent=2)
    return file_path


def config_exists(path: Optional[str] = None) -> bool:
    return os.path.exists(path or DEFAULT_CONFIG_PATH)
