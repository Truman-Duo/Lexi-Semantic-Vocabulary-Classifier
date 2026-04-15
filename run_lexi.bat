@echo off
chcp 65001 >nul
title Lexi 词汇分类工具 v2.0
echo ========================================
echo        Lexi 词汇分类工具 v0.1.0
echo ========================================
echo.

if "%~1"=="" (
    echo 使用方法：将文本文件拖拽到此批处理文件上
    echo 或者命令行运行：%0 文件名.txt
    echo.
    pause
    exit /b 1
)

set INPUT_FILE=%~1
set CATEGORIES_FILE=data\categories_full.json

echo (1/5) 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)
python --version
echo.

echo (2/5) 检查依赖包...
python -c "import lemminflect" >nul 2>&1
if errorlevel 1 (
    echo 正在安装 lemminflect...
    pip install lemminflect
) else (
    echo lemminflect 已安装
)
python -c "import wordfreq" >nul 2>&1
if errorlevel 1 (
    echo 正在安装 wordfreq...
    pip install wordfreq
) else (
    echo wordfreq 已安装
)
python -c "import nltk" >nul 2>&1
if errorlevel 1 (
    echo 正在安装 nltk...
    pip install nltk
) else (
    echo nltk 已安装
)
echo.

echo (3/5) 检查 NLTK 数据...
python -c "import nltk; nltk.data.find('corpora/wordnet')" >nul 2>&1
if errorlevel 1 (
    echo 正在下载 wordnet...
    python -c "import nltk; nltk.download('wordnet')"
)
python -c "import nltk; nltk.data.find('corpora/omw-1.4')" >nul 2>&1
if errorlevel 1 (
    echo 正在下载 omw-1.4...
    python -c "import nltk; nltk.download('omw-1.4')"
)
python -c "import nltk; nltk.data.find('taggers/averaged_perceptron_tagger_eng')" >nul 2>&1
if errorlevel 1 (
    echo 正在下载 averaged_perceptron_tagger_eng...
    python -c "import nltk; nltk.download('averaged_perceptron_tagger_eng')"
)
if errorlevel 1 (
    python -c "import nltk; nltk.download('averaged_perceptron_tagger')" >nul 2>&1
)
echo NLTK 数据准备完成。
echo.

echo (4/5) 检查分类词库...
if not exist "%CATEGORIES_FILE%" (
    echo 未找到完整分类词库，正在生成（可能需要5-10分钟）...
    python build_full_categories.py
    if errorlevel 1 (
        echo 词库生成失败，请检查 build_full_categories.py
        pause
        exit /b 1
    )
) else (
    echo 分类词库已存在。
)
echo.

echo (5/5) 正在分析文件："%INPUT_FILE%"
echo 请稍候...
echo.
python cli.py "%INPUT_FILE%" --categories "%CATEGORIES_FILE%"

if errorlevel 1 (
    echo.
    echo 处理出错，请检查输入文件格式或分类词库。
    pause
    exit /b 1
)

echo.
echo ========================================
echo 处理完成！输出文件：output.md 和 output.json
echo ========================================
pause