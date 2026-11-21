import os

repo = r'C:\Users\ljpri\OneDrive\Desktop\Learning Pathways\LearningPathways\Bhu Loka - भूलोक'
for p in ['bhu_loka_leafmap_interactive.html', 'public/bhu_loka_leafmap_interactive.html']:
    fp = os.path.join(repo, p)
    with open(fp, 'r', encoding='utf-8') as f:
        c = f.read()
    target = "if (qp.get('sar') === '1' || qp.get('mode') === 'sar') {"
    addition = """if (qp.get('state')) {
        setTimeout(function() {
          selectSovereignState(qp.get('state'));
          if (qp.get('districts') === '1') {
            toggleCurrentStateDistricts();
          }
        }, 200);
      }
      """
    if target in c and "qp.get('state')" not in c:
        c = c.replace(target, addition + target)
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(c)
        print(f'Added state query param handling to {p}')
