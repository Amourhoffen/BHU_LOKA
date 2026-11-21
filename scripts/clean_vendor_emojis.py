#!/usr/bin/env python3
"""
Clean all remaining emojis from vendor JS files.
"""

import os
import re

emoji_replacements = {
    '🌾': '',
    '💼': '',
    '🎓': '',
    '👷': '',
    '🔬': '',
    '⚡': '',
    '⚠️': '',
    '🛡️': '',
    '🛡': '',
    '🌊': '',
    '🏔': '',
    '🌡': '',
    '💧': '',
    '🛰': '',
    '🌸': '',
    '🔵': '',
    '⚪': '',
    '🟢': '',
    '⚫': '',
    '🏥': '',
    '⚠': '',
    '🚨': '',
    '🥣': '',
    '🔒': '',
    '📉': '',
    '➔': '->',
    '⏱️': '',
    '⏱': '',
    '⏸️': '',
    '🔮': '',
    '⭐': '',
}

target_files = [
    'Bhu Loka - भूलोक/public/Assets/vendor/bhu_loka_ai.js',
    'Bhu Loka - भूलोक/Assets/vendor/bhu_loka_ai.js',
    'Bhu Loka - भूलोक/public/Assets/vendor/bhu_loka_flood_intel.js',
    'Bhu Loka - भूलोक/Assets/vendor/bhu_loka_flood_intel.js',
    'Bhu Loka - भूलोक/public/Assets/vendor/bhu_loka_agri.js',
    'Bhu Loka - भूलोक/Assets/vendor/bhu_loka_agri.js',
]

for fp in target_files:
    if os.path.exists(fp):
        with open(fp, 'r', encoding='utf-8') as f:
            text = f.read()
        orig = text
        for em, rep in emoji_replacements.items():
            text = text.replace(em, rep)
        # Also clean double spaces created by emoji removal
        text = text.replace("icon: '',", "icon: '',")
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'Cleaned {fp}: {len(orig)} -> {len(text)} chars (delta: {len(text)-len(orig)})')

print('Vendor files cleaned of emojis.')
