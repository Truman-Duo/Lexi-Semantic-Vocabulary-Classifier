# Lexi — Offline Multi-Label English Vocabulary Classifier

Lexi is an offline, multi-label English vocabulary classifier that categorizes words into a three-level semantic taxonomy (Subjective / Objective / Abstract) and 10 subcategories. It outputs frequency-sorted word lists in Markdown, JSON, CSV, interactive HTML, and Anki deck formats.

Ideal for language learners, teachers, and anyone who wants to understand the semantic structure of an English text.

---

## Features

- **Multi-label classification** — A word can belong to multiple semantic categories
- **Three-layer fallback** — Dictionary exact match → Derivational suffix matching → Suffix heuristics → POS tag fallback
- **Confidence scoring** — Each classification is annotated with source and confidence level
- **CEFR level mapping** — Zipf frequency is mapped to A1–C2 levels automatically
- **Phrase protection** — Multi-word expressions (e.g. *ad_hoc*, *look_for*) are preserved
- **Contraction expansion** — *don't* → *do not*, *it's* → *it is*, etc.
- **Multi-format output** — Markdown, JSON, CSV, interactive HTML, Anki (.apkg)
- **AI story generation** — Generate short passages with target vocabulary using your own API key (OpenAI-compatible)
- **Graphical interface** — Built with tkinter, no extra dependencies required
- **100% offline** — Core classification is fully offline; AI story generation is optional

---

## Classification Taxonomy

```
Output
├─ Subjective (human-related)
│  ├─ Emotions & Feelings    — emotion, joy, fear ...
│  ├─ Opinions & Judgments   — judgment, belief, opinion ...
│  ├─ Mental Activities      — cognition, memory, decision ...
│  └─ Subjective Actions     — action, walk, communicate ...
│
├─ Objective (world-related)
│  ├─ Concrete Things        — artifact, animal, building ...
│  ├─ Objective Actions      — happen, occur, change ...
│  └─ Attributes & Properties— attribute, color, quality ...
│
├─ Abstract (conceptual)
│  ├─ Basic Concepts         — concept, quantity, time ...
│  ├─ Social Concepts        — society, government, economy ...
│  └─ Relations & Links      — relation, cause, condition ...
│
└─ Filtered
   └─ Stopwords              — the, a, in, of ...
```

---

## Quick Start

### Requirements

- Python 3.8+
- Dependencies: `pip install lemminflect wordfreq nltk`
- (Optional) AI story generation: `pip install openai`
- (Optional) Anki export: `pip install genanki`

### First-Time Setup

```bash
# Download NLTK data
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4'); nltk.download('averaged_perceptron_tagger_eng')"

# Build category dictionary (5-10 minutes)
python build_full_categories.py
```

### GUI Mode

```bash
python gui.py
```

### CLI Mode

```bash
# Basic usage
python cli.py your_text.txt

# Full features
python cli.py your_text.txt \
  --output-csv output.csv \
  --output-html output.html \
  --output-anki deck.apkg \
  --overrides my_overrides.json

# AI story generation
python cli.py config --api-key sk-...           # Configure API once
python cli.py story output.json --count 20       # Auto-select 20 words
python cli.py story output.json --words "abandon,beneficial,consequence"
```

### Windows (Drag & Drop)

Drag a text file onto `run_lexi.bat` to run with CSV + HTML output automatically.

---

## Output Formats

| Format | File | Description |
|--------|------|-------------|
| Markdown | `output.md` | Numbered lists by category + summary statistics |
| JSON | `output.json` | Structured data with word, zipf, cefr, confidence, source |
| CSV | `*.csv` | Spreadsheet-ready, opens in Excel |
| HTML | `*.html` | Self-contained interactive browser (search, filter, sort) |
| Anki | `*.apkg` | Importable flashcard deck (requires `genanki`) |
| Story | `*_story.md` | AI-generated passage with target words highlighted (requires `openai`) |

---

## Advanced

### Custom Overrides

Create a JSON file to override classifications:

```json
{
  "Subjective": {
    "Emotions & Feelings": ["serendipity", "wanderlust"]
  }
}
```

Usage: `python cli.py input.txt --overrides overrides.json`

---

## Project Structure

```
lexi/
├── cli.py                      # CLI entry point
├── gui.py                      # GUI application (tkinter)
├── run_lexi.bat                # Windows launcher
├── build_full_categories.py    # Category dictionary builder
├── lexi/                       # Core package
│   ├── pipeline.py             # Pipeline orchestration + all output formats
│   ├── cleaner.py              # Text cleaning
│   ├── lemmatizer.py           # Lemmatization (lemminflect)
│   ├── classifier.py           # Classification engine
│   ├── sorter.py               # Frequency sorting + CEFR
│   ├── story.py                # AI story generation (OpenAI-compatible)
│   ├── config.py               # API configuration management
│   └── models.py               # Data models
└── data/
    ├── categories_full.json    # Pre-built category dictionary (~155k words)
    └── stopwords.txt           # Stopword list
```

---

## Version History

See [version.md](version.md) for changelog.

---

## License

Apache 2.0

<br>

---

<br>

# Lexi — 离线多标签英文词汇意群分类工具

Lexi 是一款离线多标签英文词汇意群分类工具。将单词归入三级意群框架（主观类 / 客观类 / 抽象类）及 10 个子类，输出词频排序的词汇表，支持 Markdown、JSON、CSV、交互式 HTML、Anki 牌组等多种格式。

适用于语言学习者、英语教师以及任何希望分析英文文本语义结构的人。

---

## 功能特点

- **多标签分类** — 一个单词可同时归属多个语义类别
- **三层回退策略** — 词典精确匹配 → 派生后缀匹配 → 后缀规则 → 词性标注回退
- **置信度评分** — 每个分类标注来源与置信度等级
- **CEFR 等级映射** — 从 Zipf 频率自动映射 A1–C2 等级
- **短语保护** — 多词表达（如 *ad_hoc*、*look_for*）自动保留
- **缩写展开** — *don't* → *do not*、*it's* → *it is* 等
- **多格式输出** — Markdown、JSON、CSV、交互式 HTML、Anki 牌组
- **AI 短文生成** — 使用自己的 API Key 让 AI 生成包含目标词汇的英文短文（OpenAI 兼容接口）
- **图形界面** — 基于 tkinter，无需额外依赖
- **完全离线** — 核心分类完全离线；AI 短文生成为可选功能

---

## 分类体系

```
输出
├─ 主观类（与"人"相关）
│  ├─ 情绪感受      — emotion, joy, fear ...
│  ├─ 观点判断      — judgment, belief, opinion ...
│  ├─ 心理活动      — cognition, memory, decision ...
│  └─ 主观动作      — action, walk, communicate ...
│
├─ 客观类（与"世界"相关）
│  ├─ 具体事物      — artifact, animal, building ...
│  ├─ 客观动作      — happen, occur, change ...
│  └─ 属性特征      — attribute, color, quality ...
│
├─ 抽象类（概念性）
│  ├─ 基础概念      — concept, quantity, time ...
│  ├─ 社会概念      — society, government, economy ...
│  └─ 关系连接      — relation, cause, condition ...
│
└─ 过滤词
   └─ 停用词        — the, a, in, of ...
```

---

## 快速开始

### 环境要求

- Python 3.8+
- 安装依赖：`pip install lemminflect wordfreq nltk`
- （可选）AI 短文生成：`pip install openai`
- （可选）Anki 导出：`pip install genanki`

### 首次配置

```bash
# 下载 NLTK 数据
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4'); nltk.download('averaged_perceptron_tagger_eng')"

# 构建分类词库（5-10 分钟）
python build_full_categories.py
```

### GUI 模式

```bash
python gui.py
```

### CLI 模式

```bash
# 基础用法
python cli.py 你的文本.txt

# 完整功能
python cli.py 你的文本.txt \
  --output-csv output.csv \
  --output-html output.html \
  --output-anki deck.apkg \
  --overrides my_overrides.json

# AI 短文生成
python cli.py config --api-key sk-...           # 首次配置 API
python cli.py story output.json --count 20       # 自动选 20 词生成
python cli.py story output.json --words "abandon,beneficial,consequence"
```

### Windows 拖放运行

将文本文件拖拽到 `run_lexi.bat` 上，自动生成 CSV + HTML 输出。

---

## 输出格式

| 格式 | 文件 | 说明 |
|------|------|------|
| Markdown | `output.md` | 按分类的编号列表 + 统计摘要 |
| JSON | `output.json` | 结构化数据，含词/词频/CEFR/置信度/来源 |
| CSV | `*.csv` | 可直接用 Excel 打开 |
| HTML | `*.html` | 自包含交互浏览器（搜索、筛选、排序） |
| Anki | `*.apkg` | 可导入 Anki 的牌组（需 `genanki`） |
| 短文 | `*_story.md` | AI 生成含目标词汇的英文短文（需 `openai`） |

---

## 高级功能

### 自定义覆盖

创建 JSON 文件覆盖内置分类：

```json
{
  "主观类": {
    "情绪感受": ["serendipity", "wanderlust"]
  }
}
```

使用：`python cli.py input.txt --overrides overrides.json`

---

## 项目结构

```
lexi/
├── cli.py                      # CLI 入口
├── gui.py                      # 图形界面（tkinter）
├── run_lexi.bat                # Windows 启动器
├── build_full_categories.py    # 分类词库构建脚本
├── lexi/                       # 核心代码包
│   ├── pipeline.py             # 管线编排 + 全部输出格式
│   ├── cleaner.py              # 文本清洗
│   ├── lemmatizer.py           # 词形还原（lemminflect）
│   ├── classifier.py           # 分类引擎
│   ├── sorter.py               # 词频排序 + CEFR
│   ├── story.py                # AI 短文生成（OpenAI 兼容接口）
│   ├── config.py               # API 配置管理
│   └── models.py               # 数据模型
└── data/
    ├── categories_full.json    # 预构建分类词库（约 15.5 万词）
    └── stopwords.txt           # 停用词表
```

---

## 版本历史

详见 [version.md](version.md)。

---

## 许可证

Apache 2.0
