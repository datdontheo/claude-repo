#!/usr/bin/env python3
"""Two-pass build: pass 1 finds the page of each section; pass 2 writes the real Contents."""
import json, subprocess, re, sys, os

D = os.path.dirname(os.path.abspath(__file__))


def build(cfg, pdf):
    json.dump(cfg, open(f'{D}/config.json', 'w'))
    subprocess.run(['python3', '-I', f'{D}/book.py'], check=True, cwd=D)
    subprocess.run(['node', f'{D}/render.js', f'{D}/book.html', pdf], check=True)


def pages(pdf):
    out = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout
    return int(re.search(r'Pages:\s+(\d+)', out).group(1))


base = json.load(open(f'{D}/base_config.json')) if os.path.exists(f'{D}/base_config.json') else {}
build(dict(base, markers=True, toc={}), f'{D}/pass1.pdf')
n = pages(f'{D}/pass1.pdf')
toc = {}
for pg in range(1, n + 1):
    t = subprocess.run(['pdftotext', '-f', str(pg), '-l', str(pg), f'{D}/pass1.pdf', '-'], capture_output=True, text=True).stdout
    for m in re.findall(r'MK_(\w+)_MK', t):
        toc.setdefault(m, pg)
out = sys.argv[1] if len(sys.argv) > 1 else f'{D}/book.pdf'
build(dict(base, markers=False, toc=toc), out)
print('pass1 pages', n, '| final pages', pages(out))
print('toc', toc)
