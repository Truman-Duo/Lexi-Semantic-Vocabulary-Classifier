# Version History

## v2.1 — 架构重构 + AI 风格模板 + 测试套件 (2026-05-17)

### 新增功能

- **风格模板系统** (`lexi/styles.py`) — 用户可保存参考文本（托福/雅思/NYT 等）作为风格教练，生成短文时选择风格，AI 模仿其句式/用词/语气
- **CLI 风格管理** — `python cli.py style add/list/show/delete` 子命令
- **GUI 风格选择器** — 短文面板新增风格下拉框 + 刷新按钮
- **测试套件** (`tests/`) — 70 个 pytest 单元测试，覆盖 cleaner/lemmatizer/classifier/sorter/story/styles/controller
- **pyproject.toml** — 项目元数据 + pytest 配置

### 架构改进

- **LexiController** (`lexi/controller.py`) — 统一入口层，解耦 UI 与业务逻辑，CLI 和 GUI 同等使用
- **输出抽象** — `OutputOptions` / `ClassifyResult` 数据类，替代原先散落的路径参数
- 短文生成 prompt 支持 `style_text` 参数，可注入风格参考文本

### 工程改进

- CLI 和 GUI 均通过 LexiController 调用，不再直接引用 pipeline/story 内部函数
- `openai` 包改为惰性导入，仅在调用短文生成时才加载
- `.gitignore` 新增 `.pytest_cache/` 和 `tests/__pycache__/`
- 新增 `ROADMAP.md` — 产品路线图（P0-P4）

---

## v0.0.2 — 多格式导出 + GUI + 置信度分类 (2026-05-06)

### 新增功能

- **GUI 图形界面** (`gui.py`) — 基于 tkinter，支持文件选择、格式勾选、进度条、结果展示
- **CSV 导出** — 每词附带 word / main_category / sub_category / zipf_frequency / cefr_level / confidence / source
- **交互式 HTML 浏览器** — 自包含网页，支持分类树浏览、搜索过滤、CEFR 筛选、排序切换
- **Anki 牌组导出** — 需 `genanki` 包，单词为卡片正面，分类/CEFR/词频为背面
- **置信度分数** — 每个分类标注来源（dictionary / fuzzy / suffix / pos_fallback）和置信度（1.0→0.4）
- **派生词模糊匹配** — 词典未命中时自动剥离 -ness/-tion/-ment 等后缀重新匹配，置信度 0.8
- **CEFR 等级映射** — 从 Zipf 频率自动映射 A1–C2 等级，所有输出格式均包含
- **用户自定义分类覆盖** — `--overrides` 参数支持 JSON 覆盖文件，优先级最高
- **统计摘要** — Markdown 末尾输出分类方法分布和各类别占比
- **进度回调** — pipeline 支持 progress_callback / status_callback，GUI 实时更新

### 工程改进

- 依赖包改为惰性导入，模块加载不崩溃，缺失时给出清晰提示
- `cli.py` 无参数时显示完整帮助和使用示例
- `run_lexi.bat` 大幅精简，仅保留入口选择和词库自动构建
- NLTK 资源在首次调用时惰性下载，不在 import 时触发
- 新增 `lexi/models.py` 数据模型（ClassificationResult / WordInfo）
- 更新 `lexi/__init__.py` 导出新类型
- 修复 cli.py 默认 --categories 路径

### 文档

- 新增 `使用说明.md` — 安装、GUI/CLI 操作、输出格式、高级功能
- 新增 `CLAUDE.md` — 项目架构和开发指引
- 更新 `.gitignore` — 屏蔽 pycache / .idea / 输出文件

---

## v0.0.1 — 初始构建 (2026-04-15)

定位：首个可运行版本，核心功能完整，适合个人使用和早期反馈。

### 已实现的功能

1. **核心分类管线（Pipeline）**
   - 流式文本清洗（支持生词本、词典导出、普通文本）
   - 自动删除音标（/.../）、词性标注（n.、vt.）、数字、标点、中文
   - 缩写展开（don't → do not 等）

2. **词形还原（Lemmatization）**
   - 多词性回退：优先动词 → 名词 → 形容词 → 副词
   - 支持多词性原形保留

3. **三级意群分类框架（Multi-label）**
   - 主观类：情绪感受 / 观点判断 / 心理活动 / 主观动作
   - 客观类：具体事物 / 客观动作 / 属性特征
   - 抽象类：基础概念 / 社会概念 / 关系连接
   - 过滤词：停用词（代词、介词、连词等）

4. **分类策略（三层回退）**
   - 第一层：预定义词库（WordNet 上位词映射 + 手工补充）- 覆盖率约 85%
   - 第二层：后缀启发式（-ly、-ing、-tion 等）- 覆盖率约 10%
   - 第三层：NLTK 词性标注回退 - 覆盖率 100%，无未分类词

5. **词频排序**
   - 基于 wordfreq 库的 Zipf 频率降序排序
   - 高频词排在前面，符合认知学习规律

6. **短语保护**
   - 自动识别 WordNet 中的多词表达（如 ad_hoc、de_facto）
   - 避免将固定搭配拆分成单个单词

7. **输出格式**
   - Markdown：人类可读的分类笔记
   - JSON：结构化数据，便于程序处理
   - 支持一词多类（multi-label），一个单词可出现在多个分类下

8. **用户体验**
   - 命令行工具 cli.py
   - 一键运行脚本 run_lexi.bat（Windows），自动检查环境和依赖
   - 支持拖拽文件到批处理文件运行

### 统计数据（基于测试输入）

| 指标 | 数值 |
|------|------|
| 输入单词数 | 4672（原始） |
| 还原后唯一词数 | 4521 |
| 分类覆盖率 | 100%（无不分类词） |
| 单次处理时间 | < 2 秒（数千词） |

### 依赖库

- `lemminflect`：词形还原
- `wordfreq`：词频统计
- `nltk`：词性标注、WordNet 接口

### 已知限制（v0.0.2 已部分改进）

- 不支持 WordNet 未收录的罕见词（通过词性回退仍能分类，但可能不够精准）
- 短语保护仅覆盖 WordNet 中的固定搭配
- 分类词库 categories_full.json 生成需要 5-10 分钟（首次）
