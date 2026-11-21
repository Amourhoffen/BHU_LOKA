with open('public/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Check _build function row innerHTML content
p3 = text.find('function _build()')
print('_build function:')
chunk = text[p3:p3+1200]
# Look for onchange
i = chunk.find('onchange')
print('onchange context in _build:')
print(chunk[max(0,i-20):i+120])
