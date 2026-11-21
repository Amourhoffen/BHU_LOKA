import os

repo = r'C:\Users\ljpri\OneDrive\Desktop\Learning Pathways\LearningPathways\Bhu Loka - भूलोक'
for p in ['bhu_loka_cyber_dashboard.html', 'public/bhu_loka_cyber_dashboard.html', 'index.html', 'public/index.html']:
    fp = os.path.join(repo, p)
    if not os.path.exists(fp):
        continue
    with open(fp, 'r', encoding='utf-8') as f:
        c = f.read()
    target = "if (qp.get('cropModal') === 'true') {"
    addition = """if (qp.get('view') === 'studio' || qp.get('view') === 'land') {
        window.skipBhuIntro();
        var splash = document.getElementById('bhu-intro-overlay');
        if (splash) splash.style.display = 'none';
        if (typeof openUrbanStudio === 'function') openUrbanStudio('hussain_sagar');
        setTimeout(function() {
          if (window.UrbanIntelligenceController && typeof window.UrbanIntelligenceController.switchTopTab === 'function') {
            window.UrbanIntelligenceController.switchTopTab('site_ai');
          }
        }, 300);
      }
      """
    if target in c and "qp.get('view') === 'studio'" not in c:
        c = c.replace(target, addition + target)
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(c)
        print(f'Added studio query param to {p}')
