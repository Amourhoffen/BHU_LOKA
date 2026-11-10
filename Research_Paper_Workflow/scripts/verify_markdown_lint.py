import glob
import re

total_issues = 0
for filepath in sorted(glob.glob(r"Bhu Loka - भूलोक/Research_Paper_Workflow/Review/*.md")):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    issues = []
    in_code = False
    for idx, line in enumerate(lines):
        if line.startswith("```"):
            if not in_code:
                in_code = True
                lang = line[3:].strip()
                if not lang:
                    issues.append((idx + 1, "MD040: Fenced code block without language"))
            else:
                in_code = False
        if line.endswith(" ") or line.endswith("\t"):
            if not line.endswith("  "):
                issues.append((idx + 1, "MD009: Trailing whitespace"))
        if re.search(r"^#{1,6}\s{2,}", line):
            issues.append((idx + 1, f"MD019: Multiple spaces after hash: {line[:30]}"))

    for idx in range(len(lines) - 1):
        if lines[idx].strip() == "" and lines[idx + 1].strip() == "":
            issues.append((idx + 1, "MD012: Multiple consecutive blank lines"))

    print(f"{filepath}: {len(issues)} issues remaining")
    for line_num, msg in issues:
        print(f"  L{line_num}: {msg}")
    total_issues += len(issues)

print(f"\nTOTAL ISSUES ACROSS ALL REVIEW FILES: {total_issues}")

