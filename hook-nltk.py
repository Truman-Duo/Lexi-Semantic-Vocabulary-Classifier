# hook-nltk.py — override PyInstaller's default nltk hook
# The default hook recursively collects ALL of ~/nltk_data (~3.5GB on this machine).
# This project only uses averaged_perceptron_tagger_eng for POS tagging at runtime.
# We collect NONE of nltk_data — classifier.py already has _ensure_nltk_resources()
# which calls nltk.download() if the tagger is missing.

from PyInstaller.utils.hooks import collect_submodules, copy_metadata

# Only collect Python submodules (code), NOT data files
hiddenimports = collect_submodules('nltk')

# Collect metadata for version info
datas = copy_metadata('nltk')
