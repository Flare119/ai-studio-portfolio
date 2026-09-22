#!/usr/bin/env python3
"""Gắn data-t="tNNN" + xuất i18n/en.json.
Tag ở cấp PHẦN TỬ: element nào mà bên trong chỉ có text + thẻ inline (em/strong/br/span/a/code)
thì tag cả element và lưu innerHTML. Nhờ vậy bắt được tiêu đề có <em>, đoạn có <strong>…"""
import re, json, io

SRC = 'index.html'
INLINE_OK = r'(?:em|strong|b|i|br|span|a|code|sup|sub|u|small)'
SKIP_TAGS = {'script', 'style', 'code', 'pre', 'svg', 'canvas', 'iframe', 'video', 'source'}

html = io.open(SRC, encoding='utf-8').read()
head_end = html.find('<body')  # LƯU Ý: có <style> lồng trong body (#capabilities) nên không dùng rfind('</style>')
head, body = html[:head_end], html[head_end:]

scripts = []
def stash(m):
    scripts.append(m.group(0)); return f'@@SCRIPT{len(scripts)-1}@@'
body = re.sub(r'<script\b.*?</script>', stash, body, flags=re.S)
body = re.sub(r'<style\b.*?</style>', stash, body, flags=re.S)

counter = [0]; strings = {}

# nội dung hợp lệ: text + thẻ inline lồng 1 tầng
INNER = r'(?:[^<>]|<' + INLINE_OK + r'\b[^<>]*>|</' + INLINE_OK + r'>)+'
TARGET = re.compile(
    r'(<(h1|h2|h3|h4|h5|p|li|dt|dd|summary|figcaption|button|a|span|div)\b[^<>]*>)'
    r'(' + INNER + r')'
    r'(</\2>)', re.S)

def repl(m):
    open_tag, tag, inner, close_tag = m.group(1), m.group(2), m.group(3), m.group(4)
    if tag in SKIP_TAGS or 'data-t=' in open_tag:
        return m.group(0)
    text_only = re.sub(r'<[^>]+>', '', inner).strip()
    if not text_only or not re.search(r'[A-Za-zÀ-ỹ]', text_only):
        return m.group(0)
    if len(text_only) < 2:
        return m.group(0)
    counter[0] += 1
    key = f't{counter[0]:03d}'
    strings[key] = inner.strip()
    new_open = re.sub(r'^<\s*([a-zA-Z0-9]+)', r'<\1 data-t="%s"' % key, open_tag, count=1)
    return new_open + inner + close_tag

prev = None
while prev != body:          # lặp để bắt cả phần tử lồng nhau chưa được tag
    prev = body
    body = TARGET.sub(repl, body)

for i, sc in enumerate(scripts):
    body = body.replace(f'@@SCRIPT{i}@@', sc)

io.open(SRC, 'w', encoding='utf-8').write(head + body)
io.open('i18n/en.json', 'w', encoding='utf-8').write(json.dumps(strings, ensure_ascii=False, indent=1))
print(f'tagged {counter[0]} strings -> i18n/en.json')
