import os

repo = r'C:\Users\ljpri\OneDrive\Desktop\Learning Pathways\LearningPathways\Bhu Loka - भूलोक'
for p in ['bhu_loka_leafmap_interactive.html', 'public/bhu_loka_leafmap_interactive.html']:
    fp = os.path.join(repo, p)
    with open(fp, 'r', encoding='utf-8') as f:
        c = f.read()
    old_fetch = """        try {
          const [issRes, resRes] = await Promise.all([
            fetch('https://api.wheretheiss.at/v1/satellites/25544'),
            fetch('https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle')
          ]);"""
    new_fetch = """        try {
          const ctrl2 = new AbortController();
          const tid2 = setTimeout(() => ctrl2.abort(), 1200);
          const [issRes, resRes] = await Promise.all([
            fetch('https://api.wheretheiss.at/v1/satellites/25544', { signal: ctrl2.signal }).catch(() => ({ ok: false })),
            fetch('https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle', { signal: ctrl2.signal }).catch(() => ({ ok: false }))
          ]);
          clearTimeout(tid2);"""
    if old_fetch in c:
        c = c.replace(old_fetch, new_fetch)
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(c)
        print(f'Added fetch timeout to {p}')
