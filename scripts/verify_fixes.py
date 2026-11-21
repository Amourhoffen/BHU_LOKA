with open('public/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

checks = {
    'bhu-time-machine HTML': 'id="bhu-time-machine"' in text,
    'TM CSS hide removed': 'BHU TIME MACHINE' in text,
    'bhuSetLayer bridge': 'Bridge to real 3D engine functions' in text,
    'color-decoder fixed class': 'fixed top-16 right-5' in text,
    'auto-open removed': 'Color decoder: not auto-opened on load' in text,
    'emoji clock replaced': 'fa-regular fa-clock' in text,
    'neon dot changed': 'bg-cyan-500 shrink-0 mt-0.5' in text,
    'AI header fixed': 'flex-wrap min-w-0' in text,
    'TM slider in HTML': 'id="tm-slider"' in text,
}
for k, v in checks.items():
    print('[PASS]' if v else '[FAIL]', k)
