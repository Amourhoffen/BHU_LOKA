import os
import shutil
import subprocess

# 1. Backup all sensitive/private files to local gitignored archive
backup_dir = '_private_research_archive_local'
os.makedirs(backup_dir, exist_ok=True)

items_to_remove = [
    'Amour_Hoffen_NASA_Research_Paper.zip',
    'BHU-LOKA (2).pptx',
    'BHU-LOKA (2).pptx.pdf',
    'BHU_LOKA_Final_Research_Paper.pdf',
    'BHU_LOKA_NASA_Presentation.pptx',
    'BHU_LOKA_Presentation_Amour_Hoffen.html',
    'BHU_LOKA_Presentation_Speaker_Notes.md',
    'Final_Research_Work (2).zip',
    'Final_Research_Work',
    'IITP Research',
    'Research_Papers',
    'Sequential_Compound_Hydro_Thermal_Risk_and_Urban_Corner_Reflector_Flood_Mapping_in_Continental_Alluvial_Metropolises__Empirical_Earth_Observation___3_.pdf',
    'Sequential_Compound_Hydro_Thermal_Risk_and_Urban_Corner_Reflector_Flood_Mapping_in_Continental_Alluvial_Metropolises__Empirical_Earth_Observation___4_.pdf',
    'public/BHU_LOKA_Presentation_Amour_Hoffen.html',
    'public/index.html.bak2'
]

print("=== 1. Backing up private items locally ===")
for item in items_to_remove:
    if os.path.exists(item):
        dest = os.path.join(backup_dir, os.path.basename(item))
        if os.path.isfile(item):
            shutil.copy2(item, dest)
            print(f"Backed up file: {item} -> {dest}")
        elif os.path.isdir(item):
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
            print(f"Backed up directory: {item} -> {dest}")

# 2. Remove items from Git tracking and working tree
print("\n=== 2. Removing items from Git ===")
for item in items_to_remove:
    if os.path.exists(item):
        subprocess.run(['git', 'rm', '-rf', item], check=False)
        print(f"git rm -rf: {item}")

# 3. Update .gitignore with strict security & private research exclusions
print("\n=== 3. Updating .gitignore with enhanced security & exclusions ===")
with open('.gitignore', 'r', encoding='utf-8') as f:
    gitignore_content = f.read()

new_rules = """
# ==============================================================================
# Enhanced Security, Private Research & Binary File Exclusions
# ==============================================================================
_private_research_archive_local/
Final_Research_Work/
IITP Research/
Research_Papers/
*.zip
*.tar
*.gz
*.pptx
*.ppt
*.pdf
*.docx
*.doc

# Secret keys, credentials & service accounts
*.key
*.pem
*.secret
*.token
*serviceAccountKey*.json
.env*
!BhuLoka_API_Config.env.example
"""

if '_private_research_archive_local/' not in gitignore_content:
    with open('.gitignore', 'a', encoding='utf-8') as f:
        f.write("\n" + new_rules.strip() + "\n")
    print("Appended enhanced security rules to .gitignore")

# 4. Remove hardcoded Firebase API key from HTML files
print("\n=== 4. Neutralizing hardcoded API key in client HTML ===")
html_files = [
    'index.html',
    'public/index.html',
    'bhu_loka_cyber_dashboard.html',
    'public/bhu_loka_cyber_dashboard.html'
]

old_key_str = 'apiKey: "AIzaSyAAkKgYx1u-1KwTK3C4FVxYjamx2newU3I",'
safe_key_str = 'apiKey: (typeof window !== "undefined" && window.__BHU_FIREBASE_KEY__) || "",'

for hf in html_files:
    if os.path.exists(hf):
        with open(hf, 'r', encoding='utf-8') as f:
            c = f.read()
        if old_key_str in c:
            c = c.replace(old_key_str, safe_key_str)
            with open(hf, 'w', encoding='utf-8') as f:
                f.write(c)
            print(f"Secured API key in {hf}")

# 5. Clean references in README.md to removed PDFs
print("\n=== 5. Updating README.md deliverables table ===")
with open('README.md', 'r', encoding='utf-8') as f:
    readme = f.read()

# Replace rows referencing local PDF deliverables with web deliverables
old_ppt_row = '| **Presentation Deck PDF** | [`BHU-LOKA (2).pptx.pdf`](./BHU-LOKA%20(2).pptx.pdf) | High-definition research presentation deck (`88.3 MB`) |'
new_ppt_row = '| **Research Presentation Deck** | [https://bhu-loka.web.app/presentation](https://bhu-loka.web.app/presentation) | High-definition interactive research presentation deck |'

old_paper_row = '| **12-Page Research Paper PDF** | [`Sequential_Compound_Hydro_Thermal_Risk_...pdf`](./Sequential_Compound_Hydro_Thermal_Risk_and_Urban_Corner_Reflector_Flood_Mapping_in_Continental_Alluvial_Metropolises__Empirical_Earth_Observation___3_.pdf) | Complete peer-review manuscript with equations, Otsu calibration, and SBCV benchmarks |'
new_paper_row = '| **Peer-Review Manuscript** | [Manuscript Elsevier Format](Research_Paper_Workflow/MANUSCRIPT_ELSEVIER_FORMAT.html) | Complete peer-review manuscript with equations, Otsu calibration, and SBCV benchmarks |'

readme = readme.replace(old_ppt_row, new_ppt_row)
readme = readme.replace(old_paper_row, new_paper_row)

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme)
print("Updated README.md deliverables")

print("\n=== COMPLETED SECURITY ENHANCEMENT & FILE PURGE ===")
