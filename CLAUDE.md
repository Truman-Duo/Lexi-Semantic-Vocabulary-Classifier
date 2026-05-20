# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

Lexi 是一款离线多标签英文词汇意群分类工具。输入英文文本文件，输出按"主观类/客观类/抽象类"三级意群分类的词汇表。

核心流程：`清洗 → 词形还原 → 分类 → 排序 → 输出`

## 架构

```
cli.py                    # 命令行入口（分类 + story/config/style 子命令）
gui.py                    # Flet 视图层（纯渲染，无业务逻辑）
lexi/
  __init__.py             # 导出公共 API
  models.py               # 数据模型：ClassificationResult、WordInfo
  pipeline.py             # 主流程编排 + 5 种输出格式
  cleaner.py              # 文本清洗
  lemmatizer.py           # 词形还原（lemminflect）
  classifier.py           # 分类器：词典 → 模糊 → 后缀 → 词性回退
  sorter.py               # 词频排序 + CEFR 映射
  story.py                # AI 短文生成（OpenAI 兼容接口）
  config.py               # API 配置管理（~/.lexi/config.json）
  controller.py           # LexiController 统一入口
  styles.py               # 风格模板 CRUD（~/.lexi/styles/）
  style_analyzer.py       # StyleAnalyzer 15 项量化指标
  gui_app.py              # LexiApp — GUI 状态与操作，与 UI 框架解耦
build_full_categories.py  # WordNet 上义词分类词库构建
data/
  stopwords.txt           # 停用词表
  categories_full.json    # 15.5 万词分类词库
tests/                    # 88 个 pytest 单元测试
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
- `flet` — 现代 Flutter 桌面 GUI（圆角按钮、深色/浅色主题）
- `openai`（可选）— AI 短文生成（OpenAI 兼容接口）
- `genanki`（可选）— Anki APKG 牌组导出

## 新功能（v3.0）

- **Flet 现代化 UI**：圆角按钮、深色/浅色主题切换、跟随系统、hover 动效
- **AI 短文生成**：接入 OpenAI 兼容 API，选择目标词汇自动生成英文短文，支持 4 种选词策略
- **风格模板系统**：量化风格特征提取（StyleAnalyzer 15 项指标），密度感知短文生成
- **API 配置管理**：`cli.py config` 子命令 + GUI 设置对话框，配置文件存储在 `~/.lexi/config.json`
- **LexiController 统一入口**：解耦 UI 与业务逻辑，CLI/GUI 同等使用
- **测试套件**：88 个 pytest 单元测试覆盖全部核心模块
- **派生模糊匹配**：词典未命中时，自动剥离派生后缀重新匹配，置信度 0.8
- **置信度分数**：每个分类结果标注置信度（词典=1.0、模糊=0.8、后缀=0.6、词性回退=0.4）
- **CEFR 等级**：从 Zipf 频率映射 A1-C2 等级，所有输出均包含
- **CSV/HTML/Anki 导出**：多格式输出，含词频/CEFR/置信度/来源

## 关键设计决策

- 分类词库通过 WordNet 上义词路径自动构建，支持离线使用
- 多词短语在清洗阶段通过下划线合并后保留，不做词形还原
- 分类优先级：用户覆盖 > 停用词 > 词典精确匹配 > 派生模糊匹配 > 后缀规则 > 词性回退
- 输出按 Zipf 词频降序排列
- NLTK 资源在首次使用时惰性下载，不在 import 时触发
- GUI 使用 threading 避免界面阻塞，通过回调更新进度
- AI 短文生成为独立步骤，不嵌入分类 pipeline，CLI 通过 `story` 子命令调用
- openai SDK 采用惰性导入，缺失时给出清晰提示而非在启动时崩溃

## ⚠️ PyInstaller 打包（必读）

### 最终方案：`flet pack --onedir`

**不需要**手写 spec、hook-nltk.py、hook-flet.py、hook-wordfreq.py。
`flet pack` 是 Flet 官方打包命令，自动处理 Flutter 客户端、控件注册、icons.json 等所有 Flet 特有依赖。

```bash
# 先移走 nltk_data（~3.5GB）
mv C:/Users/Duo/AppData/Roaming/nltk_data C:/Users/Duo/AppData/Roaming/nltk_data.bak

# 打包
flet pack gui.py --name Lexi --onedir \
  --add-data "data/categories_full.json;data" \
  --add-data "data/stopwords.txt;data" \
  --hidden-import nltk \
  --hidden-import lemminflect \
  --hidden-import wordfreq

# 恢复 nltk_data
mv C:/Users/Duo/AppData/Roaming/nltk_data.bak C:/Users/Duo/AppData/Roaming/nltk_data
```

Windows 上 `--add-data` 分隔符是分号 `;`。输出在 `dist/Lexi/`，整个文件夹分发。

### 反复踩过的坑

| 问题 | 原因 | 解决 |
|------|------|------|
| exe 1.4GB / 打包 3 小时 | nltk_data 3.5GB 被 PyInstaller 自动收集 + UPX 逐文件压缩 | **打包前移走 nltk_data** |
| `ModuleNotFoundError: No module named 'pydoc'` | excludes 排除了 `pydoc`，nltk 需要它 | 不排除 pydoc/unittest |
| `ModuleNotFoundError: No module named 'nltk.sem'` | excludes 排除了 nltk 子模块，nltk 内部交叉 import | **不排除任何 nltk 子模块** |
| `ft.border.all() has no attribute 'all'` | Flet 模块代理机制在 PyInstaller 下失效 | `ft.border.xxx()` → `ft.Border.xxx()` |
| `FilledButton got unexpected keyword 'text'` | Flet 0.85.x API 改名 | `text=""` → `content=""` |
| `Unknown control: FilePicker` | Flet FilePicker 控件在打包后注册失败 | 换 tkinter `filedialog`，Python 内置可靠 |
| `icons.json No such file` | `collect_submodules` 只收 .py，漏了 JSON 数据 | 用 `flet pack` 代替手写 spec，它自动包含 |
| 打包后按钮边框消失 | `--onedir` 的 EXE 类与 COLLECT 分离导致 `--noconsole` 不生效 | 已确认 `flet pack --onedir` 自动处理 |

### GUI 架构解耦

```
gui_app.py (LexiApp)          gui.py (Flet 视图)
─────────────────────         ─────────────────
状态: input_file,             控件: TextField, Button,
      opt_md, story_count...        ProgressBar, Dropdown...
                              ↓
操作: run_classify()     ←    按钮 on_click 调用 app 方法
      run_story()             ↓
回调: on_log, on_progress →  更新控件（page.update()）
      on_classify_done
```

`LexiApp` 不 import 任何 UI 框架，CLI 和 GUI 共用。视图层只做控件创建 + 事件绑定 + `page.update()`。

## ⚠️ Flet 0.85.x 打包：全部踩坑记录与解法

Flet 0.85.x 与旧版 / 文档 / 社区示例存在大量 API 断裂。以下每一条都是打包后实际崩溃过的，必须在修改 `gui.py` 后逐项验证。

### 1. 按钮文字：`text` → `content`

```python
# ❌ 错误
ft.FilledButton(text="开始分类")
ft.OutlinedButton(text="浏览")
# ✅ 正确
ft.FilledButton(content="开始分类")
ft.OutlinedButton(content="浏览")
```

`TextButton`、`ElevatedButton`、`IconButton` 同理。`text` 参数在 0.85.x 中已移除。

### 2. 边框：`ft.border.xxx()` → `ft.Border.xxx()`

```python
# ❌ 错误：模块代理机制在 PyInstaller 下失效
ft.border.all(1, color)
ft.border.only(bottom=...)
# ✅ 正确：直接使用 Border 类
ft.Border.all(1, color)
ft.Border.only(bottom=ft.BorderSide(1, color))
```

根因：`ft.border` 是模块代理，打包后 `__getattr__` 机制断裂，`ft.border.all` 不存在。

### 3. 弹窗：`page.show_dialog()` 不是 `page.open()` 也不是 `page.dialog =`

```python
# ❌ 错误 1
page.open(dlg)                    # 0.85.x 不存在
# ❌ 错误 2
page.dialog = dlg; dlg.open = True; page.update()  # 不生效
# ✅ 正确
page.show_dialog(dlg)             # 显示
page.pop_dialog()                 # 关闭
```

这是 API 配置和风格模板弹窗反复打不开的唯一根因。三次尝试（`page.open` → `page.dialog = dlg` → `page.show_dialog`）才找到正确的。

### 9. Tab 组件：`ft.Tab` 无 `text` 无 `content` 参数

```python
# ❌ 错误 1
ft.Tab(text="导入分类", content=build_page())
# ❌ 错误 2
ft.Tab(label="导入分类", content=build_page())  # label 存在但 content 不存在
# ✅ 正确：手写按钮行 + Stack 手动切换
tab_buttons = [ft.TextButton("导入分类", on_click=lambda _, i=0: switch(i)), ...]
tab_stack = ft.Stack(controls=[page0, page1, ...])  # 手动控制 visible
```

根因：`ft.Tab` 只有 `label` 和 `icon`，没有 `content` 参数。使用 `ft.TextButton` 行 + `ft.Stack` + 手动 `visible` 切换替代。

### 10. `ft.alignment.top_center` 不存在

```python
# ❌ 错误
ft.alignment.top_center
# ✅ 正确
ft.alignment.Alignment(0, -1)  # x=0(center), y=-1(top)
```

### 11. `coroutine scroll_to was never awaited`

```python
# ❌ 错误：scroll_to 是 async，但不能在同步 on_click 中 await
main_col.scroll_to(offset=-1, duration=300)
# ✅ 正确：删掉 —— 页面切换后不需要自动滚动
```

### 12. Python 闭包陷阱：循环变量捕获

```python
# ❌ 错误
for d in data:
    btn.on_click = lambda _: foo(d)  # d 永远是最后一个值

# ✅ 正确：工厂函数 + 默认参数捕获
for d in data:
    def _mk(dd):
        return lambda _: foo(dd)
    btn.on_click = _mk(d)
```

### 13. `gui.py` 与 `gui/` 包名冲突

```python
# ❌ 错误：gui.py + gui/ 目录同时存在
# Python 解析 import gui 时先找到 gui.py，导致 gui/ 下模块不可访问
# ✅ 正确：gui.py → main.py，debug_launcher import main

### 4. 文件选择：Flet FilePicker 打包后不可用，回退 tkinter

```python
# ❌ 错误 1：打包后 Unknown control: FilePicker
picker = ft.FilePicker()
# ❌ 错误 2：能创建，但 pick_files() 永久 timeout(10s)
await picker.pick_files()        # TimeoutException
# ❌ 错误 3：tkinter 在子线程调 → RuntimeError: main thread is not in main loop
threading.Thread(target=tkinter.filedialog.askopenfilename).start()
# ✅ 正确：tkinter 在 Flet on_click 回调中直接调用（回调在主线程）
def browse(_):
    import tkinter.filedialog
    p = tkinter.filedialog.askopenfilename(title="选择文件")
    if p: field.value = p; field.update()
```

**关键理解**：Flet 的按钮 `on_click` 回调运行在**主线程**，所以 tkinter 对话框可以直接调，不会阻塞 Flet 事件循环之外的任何东西。不需要 `threading`，不需要 `page.run_task()`。

### 5. Dropdown 回调：`on_change` → `on_select`

```python
# ❌ 错误
ft.Dropdown(on_change=handler)
# ✅ 正确
ft.Dropdown(on_select=handler)
```

### 6. NavigationRail：`on_change` 存在（不要改）

```python
# ✅ 正确：0.85.x 中 on_change 依然存在
ft.NavigationRail(on_change=handler)
```
这是唯一没变的老 API，不要自作主张改成 `on_select`。

### 7. threading.excepthook：属性名是 `exc_traceback` 不是 `exc_tb`

```python
# ❌ 错误（Python 3.12）
args.exc_tb
# ✅ 正确
args.exc_traceback
```

### 8. Flet 入口：`ft.app()` → `ft.run()`

```python
# ❌ DeprecationWarning (0.80.0+)
ft.app(target=main)
# ✅ 正确
ft.run(target=main)  # 暂保持 app() 也可用，但会有警告
```

---

## 打包前自动化检查脚本

```bash
python -c "
import flet as ft, inspect

# 1. 按钮 content 不是 text
sig = inspect.signature(ft.FilledButton.__init__)
assert 'content' in sig.parameters
assert 'text' not in sig.parameters

# 2. Dropdown on_select 不是 on_change
sig = inspect.signature(ft.Dropdown.__init__)
assert 'on_select' in sig.parameters
assert 'on_change' not in sig.parameters

# 3. FilePicker 无 on_result（打包后不可用）
assert not hasattr(ft.FilePicker(), 'on_result')

# 4. 弹窗有 show_dialog / pop_dialog
assert callable(getattr(ft.Page, 'show_dialog', None))
assert callable(getattr(ft.Page, 'pop_dialog', None))

# 5. 边框
assert callable(getattr(ft.Border, 'all', None))

# 6. TextField password
sig = inspect.signature(ft.TextField.__init__)
assert 'password' in sig.parameters

# 7. NavigationRail on_change（这条不变）
sig = inspect.signature(ft.NavigationRail.__init__)
assert 'on_change' in sig.parameters

print('ALL 8 API CHECKS PASSED')
"
```

**补充 Flet 0.85 API 差异：**
- `ft.Tab(text=)` → 不存在；`label` 存在但 Tab 也无 `content` 参数，Tabs 需手写按钮+Stack 实现
- `ft.Tabs(on_change=)` 存在，同 NavigationRail

---

## 打包流程

### 正常包
```bash
mv ~/AppData/Roaming/nltk_data ~/AppData/Roaming/nltk_data.bak
flet pack gui.py --name Lexi --onedir \
  --add-data "data/categories_full.json;data" \
  --add-data "data/stopwords.txt;data" \
  --hidden-import nltk --hidden-import lemminflect --hidden-import wordfreq
mv ~/AppData/Roaming/nltk_data.bak ~/AppData/Roaming/nltk_data
# 输出: out/Lexi/Lexi.exe (~22MB) + 运行时 (~200MB)
```

### Debug 包
```bash
mv ~/AppData/Roaming/nltk_data ~/AppData/Roaming/nltk_data.bak
pyinstaller Lexi_debug.spec
mv ~/AppData/Roaming/nltk_data.bak ~/AppData/Roaming/nltk_data
# 输出: dist/Lexi_debug.exe (~145MB, console=True, upx=False)
```

### 双包对比

| | 正常包 | Debug 包 |
|---|---|---|
| 打包工具 | `flet pack` | `pyinstaller Lexi_debug.spec` |
| 入口 | `gui.py` | `debug_launcher.py` → 设 `sys._lexi_debug=True` → `gui.py` |
| console | False | **True（父进程，GUI 崩溃后存活）** |
| 按钮点击 | 无日志 | `[时间] 🖱 CLICK: 控件类型#id` |
| 侧栏导航 | 无日志 | `[时间] 🖱 NAV: index → 标签名` |
| 操作链路 | 无 | `dbg()` 输出：浏览选择路径、分类参数、短文参数 |
| 函数调用 | 无 | `@trace` 装饰器 → enter/exit + 耗时(ms) |
| GUI 异常 | 窗口消失 | `sys.excepthook` → 控制台完整 traceback |
| 线程异常 | 静默丢失 | `threading.excepthook` → `exc_traceback` 完整输出 |
| UPX | True | **False（快速打包）** |
| 体积 | ~22MB | ~145MB |
