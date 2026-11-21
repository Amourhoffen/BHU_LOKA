import os, re

emoji_pattern = re.compile(
    "["
    "\U0001F1E0-\U0001F1FF"
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U00002300-\U000023FF"
    "\U00002600-\U000026FF"
    "]+",
    flags=re.UNICODE
)

target_dir = 'Bhu Loka - भूलोक/public'
for root, dirs, files in os.walk(target_dir):
    for f in files:
        if f.endswith(('.html', '.js')):
            fp = os.path.join(root, f)
            with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                c = fh.read()
            found = emoji_pattern.findall(c)
            # filter out box-drawing characters like '──'
            real_emojis = [x for x in found if not any(ord(ch) in [0x2500, 0x2501, 0x2502, 0x2503, 0x2550, 0x2551, 0x2588, 0x2591, 0x2592, 0x2593, 0x25B6, 0x25C0, 0x25BC] for ch in x)]
            if real_emojis:
                print(f'{fp}: remaining emojis ({len(real_emojis)}): {real_emojis[:10]}')

print('Emoji scan complete.')
