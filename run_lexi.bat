@echo off
title Lexi v2.4

cd /d "%~dp0"

if not exist "data\categories_full.json" (
    echo Building category dictionary (one-time setup, 5-10 min)...
    python build_full_categories.py
    if errorlevel 1 (
        echo ERROR: Failed to build dictionary.
        pause
        exit /b 1
    )
)

if "%~1"=="" (
    python gui.py
    exit /b 0
)

python cli.py "%~1" --categories data/categories_full.json --output-csv "%~dpn1_output.csv" --output-html "%~dpn1_output.html"
if errorlevel 1 pause
