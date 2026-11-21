import os

replacements = [
    # urban studio
    ('CHALLENGE 03: PROTECTING LAKES AND GOVERNMENT LAND (FTL / WATER BUFFER AUDIT)', 'CADASTRAL WATERBODY PROTECTION & FTL BUFFER AUDIT (BSA 2023 §63)'),
    ('2. CHALLENGE 03: LAKE FULL TANK LEVEL (FTL) &amp; BUFFER ENCROACHMENT AUDIT', '2. CADASTRAL SURVEY: LAKE FULL TANK LEVEL (FTL) &amp; BUFFER SPATIAL AUDIT'),
    ('Ref: Challenge 03 &bull; Revenue Dept, Telangana', 'Ref: Cadastral Screening &bull; Revenue Dept &amp; WALTA Guidelines'),
    ('BHU LOKA (भूलोक) &bull; Pan-India Sovereign Geospatial AI Platform &bull; Challenge 03', 'BHU LOKA (भूलोक) &bull; Pan-India Sovereign Geospatial AI Platform &bull; Cadastral Screening'),
    ('# GOVERNMENT LAND & LAKE PROTECTION AUDIT DOSSIER (CHALLENGE 03)', '# GOVERNMENT LAND & LAKE PROTECTION AUDIT DOSSIER (BSA 2023 §63)'),
    
    # flood intel
    ('NASA Space Apps Challenge 2026 · Dancing with the SARs', 'BHU LOKA Sovereign Earth System & Multi-Hazard Research Workstation'),
    ('NASA Space Apps Challenge 2026 &middot; Dancing with the SARs', 'BHU LOKA Sovereign Earth System &middot; IIT Patna'),
    ('OFFICIAL NASA CHALLENGE CITATION:', 'OFFICIAL RESEARCH CITATION:'),
    ('NASA Space Apps Challenge 2026: Dancing with the SARs', 'BHU LOKA Sovereign Earth System: Urban Dihedral SAR Mapping'),
    ('**Challenge:** NASA Space Apps Challenge 2026 (Category: Dancing with the SARs)', '**Research Mission:** Sovereign Earth System & Multi-Hazard Geospatial Intelligence Workstation'),
    
    # ai js
    ("challenge: 'Dancing with the SARs (NASA 2026)'", "mission: 'Sentinel-1 SAR Deluge (Patna 2019)'"),
    ("NASA Space Apps Challenge 2026: 'Dancing with the SARs' — Scientific Model Audit:", "BHU LOKA Sovereign Earth System — Scientific Model Audit (Sentinel-1 SAR Deluge):"),
    ("BHU LOKA Official 9-Slide Presentation Deck (NASA Space Apps Challenge 2026):", "BHU LOKA Official Research Presentation Deck (IIT Patna & IIITDM Jabalpur):"),
    ("sourceTag: 'NASA Space Apps Challenge 2026: Team Amour Hoffen'", "sourceTag: 'BHU LOKA Sovereign Research Workstation: Team Amour Hoffen'"),

    # cyber dashboard & index
    ('Challenge 03 &middot; Jal Raksha FTL Surveillance', 'Cadastral Screening &middot; Jal Raksha FTL Surveillance'),
    ('"BHU LOKA (भूलोक) was conceived, engineered, and published by Team Amour Hoffen for NASA Space Apps Challenge 2026:\n\n"', '"BHU LOKA (भूलोक) is an autonomous sovereign Earth System & Multi-Hazard Intelligence Workstation developed at IIT Patna:\n\n"'),
    ('"BHU LOKA (भूलोक) ko Team Amour Hoffen ne NASA Space Apps Challenge 2026 ke liye banaya hai:\n\n"', '"BHU LOKA (भूलोक) ek sovereign Earth Intelligence aur Multi-Hazard Workstation hai jise IIT Patna aur IIITDM Jabalpur ki team ne develop kiya hai:\n\n"'),
    ('Supervisor: Dr. Pallav Rustogi | NASA Space Apps Challenge 2026: Dancing with the SARs', 'Supervisor: Dr. Pallav Rustogi | IIT Patna & IIITDM Jabalpur'),
    ('Jabalpur) &middot; Challenge: Dancing with the SARs', 'Jabalpur) &middot; Domain: Sovereign GIS & Earth Intelligence'),
    ('Mission: JAL RAKSHA (Telangana Challenge 03)', 'Mission: JAL RAKSHA (Cadastral Waterbody Screening)')
]

files_to_update = [
    'Assets/vendor/bhu_loka_urban_studio.js',
    'public/Assets/vendor/bhu_loka_urban_studio.js',
    'Assets/vendor/bhu_loka_flood_intel.js',
    'public/Assets/vendor/bhu_loka_flood_intel.js',
    'Assets/vendor/bhu_loka_ai.js',
    'public/Assets/vendor/bhu_loka_ai.js',
    'bhu_loka_cyber_dashboard.html',
    'public/bhu_loka_cyber_dashboard.html',
    'index.html',
    'public/index.html'
]

total_replaces = 0
for fp in files_to_update:
    if not os.path.exists(fp):
        continue
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    for old, new in replacements:
        content = content.replace(old, new)
    if content != orig:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        total_replaces += 1
        print(f'Updated {fp}')

print(f'Done! Successfully updated {total_replaces} files.')
