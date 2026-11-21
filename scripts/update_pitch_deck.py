import os

repo = r'C:\Users\ljpri\OneDrive\Desktop\Learning Pathways\LearningPathways\Bhu Loka - भूलोक'
for p in ['CHALLENGE_03_HYDRAA_LAKE_PROTECTION_PITCH_DECK.html', 'public/CHALLENGE_03_HYDRAA_LAKE_PROTECTION_PITCH_DECK.html']:
    fp = os.path.join(repo, p)
    if os.path.exists(fp):
        with open(fp, 'r', encoding='utf-8') as f:
            c = f.read()
        c = c.replace('Section 23 Ready', 'Field Verification Required (BSA 2023 §63)')
        c = c.replace('Figure 2: Official 4-Quadrant Statutory Dossier (Satellite, Cadastral, FTL, Encroachment)',
                      'Figure 2: Research Benchmark Reference: Yelemallappachetty Lake (Bengaluru) Cadastral FTL Screening (Survey of India / KLCDA Reference)')
        c = c.replace('Court-Admissible', 'Screening-Grade (Subject to BSA 2023 §63)')
        c = c.replace('Court Admissible', 'Screening-Grade (Subject to BSA 2023 §63)')
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(c)
        print(f'Updated {p}')
