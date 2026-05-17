# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

Lexi 是一款离线多标签英文词汇意群分类工具。输入英文文本文件，输出按"主观类/客观类/抽象类"三级意群分类的词汇表。

核心流程：`清洗 → 词形还原 → 分类 → 排序 → 输出`

## 架构

```
cli.py                    # 命令行入口（分类 + story/config 子命令）
gui.py                    # tkinter 图形界面（与 CLI 共享 pipeline）
lexi/
  __init__.py             # 导出 run_pipeline、ClassificationResult、WordInfo、StoryGenerator 等
  models.py               # 数据模型：ClassificationResult、WordInfo（含置信度/CEFR）
  pipeline.py             # 主流程编排 + Markdown/JSON/CSV/HTML/Anki 输出
  cleaner.py              # 文本清洗：去除音标/词性标注/特殊字符，展开缩写，保护多词短语
  lemmatizer.py           # 词形还原（lemminflect）
  classifier.py           # 分类器：词典匹配 → 派生模糊匹配 → 后缀规则 → 词性回退
  sorter.py               # 词频排序 + CEFR 等级映射
  story.py                # AI 短文生成（OpenAI 兼容接口，惰性导入 openai）
  config.py               # API 配置管理（~/.lexi/config.json）
build_full_categories.py  # 基于 WordNet 上义词路径预构建完整分类词库
data/
  stopwords.txt           # 停用词表
  categories_full.json    # 自动生成的 15.5 万词分类词库
```

## 分类体系

- **主观类** — 情绪感受、观点判断、心理活动、主观动作
- **客观类** — 具体事物、客观动作、属性特征
- **抽象类** — 基础概念、社会概念、关系连接
- **过滤词** — 停用词

## 运行方式

```bash
# CLI 模式
python cli.py test.txt --categories data/categories_full.json

# CLI 模式（使用全部新功能）
python cli.py test.txt --categories data/categories_full.json \
  --output-csv output.csv --output-html output.html --output-anki output.apkg

# AI 短文生成
python cli.py config --api-key sk-...              # 首次配置 API
python cli.py story output.json --count 20          # 自动选词生成短文
python cli.py story output.json --words "a,b,c"     # 手动指定词汇

# GUI 模式
python gui.py

# Windows 拖放/双击
run_lexi.bat              # 无参数 → 启动 GUI
run_lexi.bat test.txt     # 有参数 → CLI 模式
```

首次运行前：

```bash
pip install lemminflect wordfreq nltk
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4'); nltk.download('averaged_perceptron_tagger_eng')"
python build_full_categories.py   # 5-10分钟，输出 data/categories_full.json
```

## 依赖

- `lemminflect` — 词形还原
- `wordfreq` — Zipf 词频统计 + CEFR 等级映射
- `nltk` — WordNet 上义词路径、词性标注
- `customtkinter` — 现代化 GUI 界面（深色/浅色主题）
- `openai`（可选）— AI 短文生成（OpenAI 兼容接口）
- `genanki`（可选）— Anki APKG 牌组导出

## 新功能（v2.4）

- **CustomTkinter 现代化 UI**：圆角按钮、深色/浅色主题切换、跟随系统、hover 动效

- **AI 短文生成**：接入 OpenAI 兼容 API，选择目标词汇自动生成英文短文，支持 4 种选词策略
- **API 配置管理**：`cli.py config` 子命令 + GUI 设置对话框，配置文件存储在 `~/.lexi/config.json`
- **派生模糊匹配**：词典未命中时，自动剥离派生后缀（-ness、-less、-ful、-ly、-tion 等）重新匹配，置信度 0.8
- **置信度分数**：每个分类结果标注置信度（词典=1.0、模糊=0.8、后缀=0.6、词性回退=0.4）
- **CEFR 等级**：从 Zipf 频率映射 A1-C2 等级，Markdown/CSV/JSON/HTML 输出均包含
- **分类来源分布**：Markdown 统计摘要展示每类方法的占比
- **CSV 导出**：含 word、main_category、sub_category、zipf、cefr、confidence、source
- **交互式 HTML 浏览器**：自包含页面，支持分类树浏览、搜索、CEFR 过滤、词频/字母排序
- **Anki 牌组导出**（需 `pip install genanki`）：词为卡片，分类为标签
- **用户自定义覆盖**：`--overrides` 参数指定 JSON 文件，内容格式同 categories_full.json
- **GUI 界面**（tkinter）：文件选择、格式勾选、进度条、结果展示

## 关键设计决策

- 分类词库通过 WordNet 上义词路径自动构建，支持离线使用
- 多词短语在清洗阶段通过下划线合并后保留，不做词形还原
- 分类优先级：用户覆盖 > 停用词 > 词典精确匹配 > 派生模糊匹配 > 后缀规则 > 词性回退
- 输出按 Zipf 词频降序排列
- NLTK 资源在首次使用时惰性下载，不在 import 时触发
- GUI 使用 threading 避免界面阻塞，通过回调更新进度
- AI 短文生成为独立步骤，不嵌入分类 pipeline，CLI 通过 `story` 子命令调用
- openai SDK 采用惰性导入，缺失时给出清晰提示而非在启动时崩溃
