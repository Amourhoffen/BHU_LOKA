with open('public/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

p = text.find('GLOBAL TIME MACHINE')
print('time machine anchor at:', p)
if p != -1:
    print(text[p:p+600])
else:
    print('TM not found by anchor - try alternative')
    p2 = text.find('tm-slider')
    print('tm-slider at:', p2)
    if p2 != -1:
        print(text[max(0,p2-500):p2+300])
