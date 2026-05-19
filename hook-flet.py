# hook-flet.py — collect ALL flet modules AND data files (icons.json, etc.)
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('flet')
