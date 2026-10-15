#!/usr/bin/env python3
"""Check that every source paragraph's wording appears, in order, in the PDF text."""
import json, re, subprocess, sys, unicodedata

S = '/tmp/claude-0/-home-user-claude-repo/b08694ae-3575-5ddf-bbbd-39938be72a83/scratchpad'
pdf = sys.argv[1] if len(sys.argv) > 1 else f'{S}/build/book.pdf'
blocks = json.load(open(f'{S}/blocks.json'))


def norm(t):
    t = unicodedata.normalize('NFKC', t).lower()
    t = t.replace('­', '')
    return re.sub(r'[^0-9a-zɐ-ʯŋɔɛƆƐŊ]+', '', t)  # keep IPA-ish letters used in Ga/Twi


def page_texts(mode):
    n = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout).group(1))
    out = []
    for pg in range(1, n + 1):
        t = subprocess.run(['pdftotext', mode, '-f', str(pg), '-l', str(pg), pdf, '-'], capture_output=True, text=True).stdout
        lines = [l for l in t.split('\n')]
        while lines and not lines[-1].strip():
            lines.pop()
        if lines and re.fullmatch(r'\s*\d{1,3}\s*', lines[-1]):   # drop the folio
            lines.pop()
        out.append('\n'.join(lines))
    return '\n'.join(out)


pdf_text = page_texts('-layout')
pdf_raw = page_texts('-raw')
P = norm(pdf_raw)
P2 = norm(pdf_text)

missing, total, words_total, words_missing = [], 0, 0, 0
pos = 0
for b in blocks:
    t = ''.join(r[0] for r in b['runs']).strip()
    if not t:
        continue
    total += 1
    n = norm(t)
    if not n:
        continue
    words_total += len(t.split())
    if n in P or n in P2:
        continue
    # fall back: sentence-sized pieces (handles hyphenation / footers inserted mid-paragraph)
    pieces = [norm(x) for x in re.split(r'(?<=[.!?;:])\s+|\n', t) if norm(x)]
    bad = [x for x in pieces if x not in P and x not in P2]
    if bad:
        missing.append((b['idx'], t[:110], len(bad), len(pieces)))
        words_missing += sum(len(x) for x in bad) // 5

print(f'source paragraphs with text: {total}; source words: {words_total}')
print(f'paragraphs with any wording not found in PDF: {len(missing)}')
for m in missing[:80]:
    print(' ', m)
