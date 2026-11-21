import os

replacements = [
    ('<title>BHU LOKA — Challenge 03: Protecting Lakes & Government Land (Telangana / HYDRAA)</title>', '<title>BHU LOKA — Cadastral Waterbody Protection & Land Intelligence (HYDRAA / WALTA / BSA 2023)</title>'),
    ('<span class="badge-telangana">TELANGANA CHALLENGE 03</span>', '<span class="badge-telangana">CADASTRAL SCREENING</span>'),
    ('<span>BHU LOKA &bull; Telangana Challenge 03 Solution</span>', '<span>BHU LOKA &bull; Cadastral Waterbody Protection Platform</span>'),
    ('GOVERNMENT CHALLENGE RESOLUTION', 'CADASTRAL SCREENING & FIELD AUDIT FRAMEWORK'),
    ('<h2>How BHU LOKA Answers Challenge 03 Exactly</h2>', '<h2>How BHU LOKA Solves Cadastral Waterbody Protection Exactly</h2>'),
    ('Challenge 03 (Protecting Lakes and Government Land)', 'Cadastral Waterbody Protection (Protecting Lakes and Government Land)')
]

for fp in ['CHALLENGE_03_HYDRAA_LAKE_PROTECTION_PITCH_DECK.html', 'public/CHALLENGE_03_HYDRAA_LAKE_PROTECTION_PITCH_DECK.html']:
    if os.path.exists(fp):
        with open(fp, 'r', encoding='utf-8') as f:
            c = f.read()
        for old, new in replacements:
            c = c.replace(old, new)
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(c)
        print(f'Updated {fp}')
