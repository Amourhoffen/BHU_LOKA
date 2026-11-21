import os
import re
import subprocess

# Get tracked files
res = subprocess.run(['git', 'ls-files'], capture_output=True, text=True)
files = res.stdout.splitlines()

# Patterns for secrets and keys
patterns = [
    (re.compile(r'(?i)api[_-]?key\s*[:=]\s*[\'"][A-Za-z0-9_\-]{16,}[\'"]'), 'GENERIC_API_KEY'),
    (re.compile(r'(?i)secret[_-]?key\s*[:=]\s*[\'"][A-Za-z0-9_\-]{16,}[\'"]'), 'SECRET_KEY'),
    (re.compile(r'(?i)aws[_-]?(?:access[_-]?key|secret[_-]?access[_-]?key)\s*[:=]\s*[\'"][A-Za-z0-9_\-]{16,}[\'"]'), 'AWS_KEY'),
    (re.compile(r'AIza[0-9A-Za-z\-_]{35}'), 'GOOGLE_FIREBASE_API_KEY'),
    (re.compile(r'ghp_[0-9a-zA-Z]{36}'), 'GITHUB_PAT'),
    (re.compile(r'sk-[a-zA-Z0-9]{20,}'), 'OPENAI_KEY'),
    (re.compile(r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----'), 'PRIVATE_KEY')
]

found_secrets = []

for fp in files:
    if not os.path.exists(fp):
        continue
    # skip binary files
    if fp.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.joblib', '.zip', '.pdf', '.pptx', '.tif', '.tiff', '.geojson', '.csv')):
        continue
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            for pat, label in patterns:
                matches = pat.findall(content)
                if matches:
                    found_secrets.append((fp, label, matches[:3]))
    except Exception as e:
        pass

print(f"=== SECURITY SCAN RESULTS: {len(found_secrets)} potential findings ===")
for fp, label, matches in found_secrets:
    print(f"FILE: {fp} | TYPE: {label} | SAMPLES: {matches}")
