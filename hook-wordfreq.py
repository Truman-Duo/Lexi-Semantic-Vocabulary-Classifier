# hook-wordfreq.py — only collect English language data
from PyInstaller.utils.hooks import collect_data_files

datas = []
all_data = collect_data_files('wordfreq')
for src, dst in all_data:
    basename = src.rsplit('\\', 1)[-1].rsplit('/', 1)[-1]
    if 'en' in basename or 'jieba' in basename or basename == '__init__.py':
        datas.append((src, dst))
