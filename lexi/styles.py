import os
import re
from dataclasses import dataclass, field
from typing import Optional


DEFAULT_STYLES_DIR = os.path.expanduser("~/.lexi/styles")


@dataclass
class Style:
    name: str
    description: str = ""
    source: str = ""
    body: str = ""


class StyleManager:
    def __init__(self, styles_dir: Optional[str] = None):
        self.styles_dir = styles_dir or DEFAULT_STYLES_DIR
        os.makedirs(self.styles_dir, exist_ok=True)

    def list_styles(self):
        styles = []
        if not os.path.isdir(self.styles_dir):
            return styles
        for filename in sorted(os.listdir(self.styles_dir)):
            path = os.path.join(self.styles_dir, filename)
            if filename.endswith(".md") and os.path.isfile(path):
                try:
                    styles.append(self._parse_file(path))
                except (ValueError, OSError):
                    continue
        return styles

    def get_style(self, name: str):
        path = self._path_for(name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Style '{name}' not found at {path}")
        return self._parse_file(path)

    def add_style(self, name: str, body: str, description: str = "", source: str = ""):
        style = Style(name=name, description=description, source=source, body=body)
        self._write_file(style)
        return style

    def delete_style(self, name: str):
        path = self._path_for(name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Style '{name}' not found")
        os.remove(path)

    def style_names(self):
        return [s.name for s in self.list_styles()]

    def _path_for(self, name: str):
        if name.endswith(".md"):
            return os.path.join(self.styles_dir, name)
        return os.path.join(self.styles_dir, f"{name}.md")

    def _parse_file(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
        if not m:
            raise ValueError(f"Missing YAML frontmatter in {path}")

        front_raw, body = m.group(1), m.group(2).strip()
        front = {}
        for line in front_raw.strip().split("\n"):
            line = line.strip()
            if ":" in line:
                key, _, val = line.partition(":")
                front[key.strip()] = val.strip().strip('"').strip("'")

        return Style(
            name=front.get("name", os.path.splitext(os.path.basename(path))[0]),
            description=front.get("description", ""),
            source=front.get("source", ""),
            body=body,
        )

    def _write_file(self, style: Style):
        path = self._path_for(style.name)
        front = (
            f"---\n"
            f'name: "{style.name}"\n'
            f'description: "{style.description}"\n'
            f'source: "{style.source}"\n'
            f"---\n"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(front)
            f.write(style.body)
            f.write("\n")
