import re

with open('bhu_loka_cyber_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# find health occurrences
print("Health occurrences in dashboard:")
for idx, line in enumerate(text.splitlines()):
    if 'health' in line.lower() and ('id=' in line.lower() or 'tab' in line.lower() or 'pane' in line.lower() or 'button' in line.lower()):
        print(f"  L{idx+1}: {line.strip()[:100]}")

print("\nFarmer occurrences in dashboard:")
for idx, line in enumerate(text.splitlines()):
    if 'farmer' in line.lower() and ('id=' in line.lower() or 'tab' in line.lower() or 'pane' in line.lower() or 'button' in line.lower()):
        print(f"  L{idx+1}: {line.strip()[:100]}")
