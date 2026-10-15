#!/usr/bin/env python3
"""Build the A5 funeral book HTML from the supplied Word document.

All wording comes from the source paragraphs (blocks.json, produced by parse_docx.py).
Nothing is rewritten; only layout, headings' casing and obvious structure are applied.
"""
import json, html, re, os, shutil, sys
from PIL import Image

S = '/tmp/claude-0/-home-user-claude-repo/b08694ae-3575-5ddf-bbbd-39938be72a83/scratchpad'
OUT = f'{S}/build'
MEDIA = f'{S}/docx_x/word/media'
B = {b['idx']: b for b in json.load(open(f'{S}/blocks.json'))}

CFG = json.load(open(f'{OUT}/config.json')) if os.path.exists(f'{OUT}/config.json') else {}
BLEED = float(CFG.get('bleed_mm', 0))
BODY_FONT = CFG.get('body_font', 'Crimson Pro')
BODY_PT = CFG.get('body_pt', 10.5)
LEADING = CFG.get('leading', 1.36)
TOC = CFG.get('toc', {})  # id -> page number (filled by second pass)
MARK = bool(CFG.get('markers', False))

os.makedirs(f'{OUT}/img', exist_ok=True)


# ---------------------------------------------------------------- text helpers
SMALL = {'a', 'an', 'and', 'at', 'by', 'for', 'in', 'of', 'on', 'or', 'the', 'to', 'from', 'with', 'as'}
KEEP = {'I', 'II', 'III', 'PH', 'ABSA', 'BBG', 'H.E', 'H.E.', 'MR.', 'MR', 'KNUST', 'FGA/OV', 'SU'}


def tc(text):
    words = re.split(r'(\s+)', text.strip())
    out, first = [], True
    for w in words:
        if not w.strip():
            out.append(w)
            continue
        core = w.strip('“”"\'’‘,:;()')
        if core in KEEP:
            out.append({'MR': 'Mr', 'MR.': 'Mr.'}.get(w, w) if core in ('MR', 'MR.') else w)
        elif core.lower() in SMALL and not first:
            out.append(w.lower())
        else:
            out.append('-'.join(p[:1].upper() + p[1:].lower() if p else p for p in w.split('-')))
        first = False
    return ''.join(out)


class TStr(str):
    def title(self):
        return TStr(tc(str(self)))


def esc(s):
    return html.escape(s, quote=False)


def plain(i):
    return TStr(''.join(r[0] for r in B[i]['runs']).strip())


def inline(i, keep_bold=True):
    parts = []
    for txt, b, it, u in B[i]['runs']:
        t = esc(txt).replace('\t', ' ')
        t = t.replace('\n', '<br>')
        if not t.strip() and '<br>' not in t:
            parts.append(t)
            continue
        if it:
            t = f'<i>{t}</i>'
        if b and keep_bold:
            t = f'<b>{t}</b>'
        parts.append(t)
    s = ''.join(parts).strip()
    s = re.sub(r'^(<br>)+|(<br>)+$', '', s)
    return s


def para(i, cls=''):
    if not plain(i):
        return ''
    c = f' class="{cls}"' if cls else ''
    return f'<p{c}>{inline(i)}</p>'


def body(a, b, skip=(), short_group=True):
    """Paragraphs a..b-1; consecutive short lines become a tight 'lines' group."""
    out, i = [], a
    skip = set(skip)
    while i < b:
        if i in skip or not plain(i) or B[i]['imgs'] and not plain(i):
            i += 1
            continue
        if short_group and len(plain(i)) <= 78 and '\n' not in plain(i):
            j = i
            run = []
            while j < b and j not in skip and plain(j) and len(plain(j)) <= 78 and '\n' not in plain(j):
                run.append(j)
                j += 1
                if j < b and not plain(j):
                    break
            # grouped only if the source lines are adjacent (no blank between)
            if len(run) >= 3:
                out.append('<div class="lines">' + ''.join(f'<p>{inline(k)}</p>' for k in run) + '</div>')
                i = j
                continue
        out.append(para(i))
        i += 1
    return '\n'.join(x for x in out if x)


def verse(idxs, cls='verse', stanza_breaks=()):
    lines = []
    for k in idxs:
        if not plain(k):
            continue
        if k in stanza_breaks:
            lines.append('</div><div class="stanza">')
        lines.append(f'<span>{inline(k)}</span>')
    return f'<div class="{cls}"><div class="stanza">' + ''.join(lines) + '</div></div>'


def img_tag(name, cls):
    src = f'{MEDIA}/{name}'
    dst = f'{OUT}/img/{name}'
    if not os.path.exists(dst):
        shutil.copy(src, dst)
    return f'<figure class="{cls}"><img src="img/{name}" alt=""></figure>'


def photo_block(i, width_mm):
    name = B[i]['imgs'][0].split('/')[-1]
    shutil.copy(f'{MEDIA}/{name}', f'{OUT}/img/{name}')
    return f'<figure class="ph-block" style="width:{width_mm}mm"><img src="img/{name}" alt=""></figure>'


def photo(i, cls=None):
    """Photo at paragraph i (name from docx rels)."""
    name = B[i]['imgs'][0].split('/')[-1]
    im = Image.open(f'{MEDIA}/{name}')
    w, h = im.size
    c = cls or ('ph-l' if w > h else 'ph-p')
    return img_tag(name, c)


# ---------------------------------------------------------------- sections
def tribute(id, kicker=None, title=None, byline=None, epi=None, inner='', cls=''):
    h = f'<section class="tribute {cls}" id="{id}" data-toc="{esc(title or kicker or id)}">'
    h += '<header class="t-head">'
    if kicker:
        h += f'<div class="kicker">{kicker}</div>'
    if title:
        h += f'<h2>{title}</h2>'
    if byline:
        h += f'<div class="byline">{byline}</div>'
    h += '<div class="orn"></div></header>'
    if epi:
        h += f'<div class="epi">{epi}</div>'
    h += inner + '</section>'
    return h


def sub(name, photo_html=''):
    return f'<h3 class="who">{esc(name)}</h3>{photo_html}'


def sig(*idxs):
    return '<div class="sig">' + ''.join(f'<p>{inline(i)}</p>' for i in idxs if plain(i)) + '</div>'


# ---- order of service tables
def parse_rows(a, b):
    rows = []
    for i in range(a, b):
        t = plain(i)
        if not t:
            continue
        t = t.replace('`', '')
        num = None
        m = re.match(r'^(\d+)\.\s*(.*)$', t, re.S)
        if m:
            num, t = m.group(1), m.group(2)
        raw = ''.join(r[0] for r in B[i]['runs']).replace('`', '').strip()
        raw = re.sub(r'^\d+\.\s*', '', raw)
        m = re.match(r'^(.*?)\s*\t[\t ]*[-:]\s*(.*)$', raw, re.S)
        if not m:
            m = re.match(r'^(.*?)\s{2,}[-:]\s*(.*)$', raw, re.S)
        if not m:
            m = re.match(r'^(.*?)\s*[-:]\s+(.*)$', raw, re.S)
        if not m:
            m = re.match(r'^(.*?)\s*[-:]\s*(.*)$', raw, re.S)
        if m:
            label, val = m.group(1).strip(), m.group(2).strip()
        else:
            label, val = raw, ''
        rows.append((label, val))
    return rows


def os_table(rows):
    h = '<table class="os"><tbody>'
    for n, (label, val) in enumerate(rows, 1):
        kind = 'hymn' if label.lower().startswith('hymn') or 'hymn' in label.lower() else ''
        h += f'<tr class="{kind}"><td class="n">{n}</td><td class="l">{esc(label)}</td><td class="v">{esc(val)}</td></tr>'
    return h + '</tbody></table>'


# ---- hymns
def hymn_block(start, end):
    title = plain(start)
    stanzas, cur = [], []
    for i in range(start + 1, end):
        t = plain(i)
        if t:
            cur.append(i)
        elif cur:
            stanzas.append(cur)
            cur = []
    if cur:
        stanzas.append(cur)
    h = f'<div class="hymn"><h4>{esc(title.title() if title.isupper() else title)}</h4>'
    for st in stanzas:
        h += '<div class="st">' + ''.join(
            f'<span class="{"turn" if plain(k).startswith("[") else ""}">{inline(k)}</span>' for k in st) + '</div>'
    return h + '</div>'


def prep_images():
    im = Image.open(f'{MEDIA}/image1.png').convert('RGB')
    w, h = im.size
    im.crop((8, 6, w - 18, h - 14)).save(f'{OUT}/img/cover.jpg', quality=95)
    for n in ('image2.png',):
        shutil.copy(f'{MEDIA}/{n}', f'{OUT}/img/{n}')
    for n in ('image8.png', 'image11.png'):
        shutil.copy(f'{MEDIA}/{n}', f'{OUT}/img/{n}')


def build_pages():
    prep_images()
    P = []

    # ---------------- 1. cover
    P.append(f'''
<section class="cover page-front">
  <div class="cover-inner">
    <div class="cover-top">A legacy that lasts a lifetime</div>
    <div class="cover-photo"><img src="img/cover.jpg" alt=""></div>
    <div class="cover-name">Daniel Kwei Ayitiah</div>
    <div class="cover-dates">11 July 1950 &nbsp;–&nbsp; 20 September 2026</div>
    <div class="cover-small">Burial and Thanksgiving Service<br>Saturday, 24th October 2026</div>
  </div>
</section>''')

    # ---------------- 2. inside cover: bookmark hymn
    lines = [f'<span>{inline(i)}</span>' for i in range(27, 43) if plain(i)]
    st1 = ''.join(lines[:8])
    st2 = ''.join(lines[8:])
    P.append(f'''
<section class="inside page-front">
  <div class="ic-wrap">
    <div class="ic-name">Daniel Kwei Ayitiah</div>
    <div class="ic-dates">11 July 1950 to 20 September 2026</div>
    <div class="orn"></div>
    <div class="ic-verse"><div class="stanza">{st1}</div><div class="stanza">{st2}</div></div>
  </div>
</section>''')

    # ---------------- 3. title page
    P.append(f'''
<section class="titlepage page-front">
  <div class="tp-wrap">
    <img class="crest" src="img/image2.png" alt="">
    <div class="tp-church">{esc(plain(64))}<br>{esc(plain(65))}</div>
    <div class="orn"></div>
    <div class="tp-prog">{esc(plain(66))}</div>
    <div class="tp-date">{esc(plain(67))}</div>
  </div>
</section>''')

    # ---------------- 4. contents (filled in second pass)
    P.append('<section class="chapter contents" id="contents"><h1 class="ch">Contents</h1><div class="orn left"></div>@@TOC@@</section>')

    # ---------------- order of service
    agents = ''.join(f'<li>{esc(plain(i))}</li>' for i in range(70, 75))
    pre = parse_rows(77, 108)
    p1 = parse_rows(116, 134)
    p2 = parse_rows(140, 149)
    # source numbers "7." twice in Part II; sequential numbering is applied by os_table
    P.append(f'''
<section class="chapter" id="order" data-toc="Order of Service">
  <h1 class="ch">{esc(plain(68).title())}</h1><div class="orn left"></div>
  <div class="agents"><div class="lab">{esc(plain(69).title())}</div><ul>{agents}</ul></div>
  <h2 class="part">{esc(plain(76).title().rstrip(':'))}</h2>
  {os_table(pre)}
  <h2 class="part">{esc(TStr(re.sub(r'\s+', ' ', plain(113))).title().replace('@', 'at'))}</h2>
  {os_table(p1)}
  <h2 class="part">{esc(TStr(re.sub(r'\s+', ' ', plain(139))).title())}</h2>
  {os_table(p2)}
</section>''')

    # ---------------- hymns
    f_starts = [156, 184, 209, 229, 252, 277]
    f_ends = f_starts[1:] + [298]
    g_starts = [299, 317, 333, 347]
    g_ends = g_starts[1:] + [366]
    fh = ''.join(hymn_block(s, e) for s, e in zip(f_starts, f_ends))
    gh = ''.join(hymn_block(s, e) for s, e in zip(g_starts, g_ends))
    P.append(f'''
<section class="chapter hymns" id="hymns" data-toc="Hymns">
  <h1 class="ch">{esc(plain(154).title())}</h1><div class="orn left"></div>
  <div class="hcols">{fh}</div>
  <h2 class="part g">{esc(plain(298).title())}</h2>
  <div class="hcols">{gh}</div>
</section>''')

    # ---------------- biography
    bio_paras = [para(i) for i in range(368, 381)]
    P.append(f'''
<section class="chapter bio" id="bio" data-toc="Biography">
  <h1 class="ch">{esc(plain(366).title().replace('Ayitiah', 'Ayitiah'))}</h1><div class="orn left"></div>
  {''.join(bio_paras[:8])}
  {''.join(bio_paras[8:])}
  <div class="remembered">{esc(plain(382))}</div>
  <p class="ataa"><i>{esc(plain(384))}</i></p>
  <div class="bio-photos">
    <figure><img src="img/image8.png" alt=""><figcaption>{esc(plain(396))}</figcaption></figure>
    <figure><img src="img/image11.png" alt=""><figcaption>{esc(plain(400))}</figcaption></figure>
  </div>
</section>''')

    # ---------------- tributes
    T = []
    T.append('<section class="chapter tributes-open" id="tributes"><h1 class="ch">Tributes</h1><div class="orn left"></div></section>')

    # wife
    T.append(tribute('wife', kicker='Tribute by his wife', title=esc(plain(407)),
                     epi=inline(408), inner=body(410, 427)))
    # children
    ch = '<div class="group">Tribute by Children</div>'
    # each photo is attached directly under its own name so it can never drift beside the next tribute
    ch += sub('Edwin', photo(446)) + body(437, 446)
    ch += sub('Ken', photo(461)) + body(450, 461)
    ch += sub('Shirley Ann', photo(466)) + body(467, 509)
    ch += sub('Nii Armah', photo(538)) + body(514, 538)
    T.append(tribute('children', inner=ch, cls='group-t'))
    # children in law
    cl = '<div class="group">Tribute by Children-in-Law</div>'
    cl += sub('Dorothy', photo(545)) + body(546, 553)
    cl += sub('Korkor', photo(555)) + body(557, 567)
    cl += (f'<h3 class="who">{esc(plain(568).title())}</h3><div class="sublab">{esc(plain(569))}</div>'
           f'<div class="epi small">{inline(570)}</div>' + body(572, 581, skip=()) +
           verse([581, 582, 583, 584]) + body(585, 588))
    cl += sub('Selma', photo(595)) + f'<div class="sublab">{esc(plain(596).title().replace("In-Law(Daddy)", "In-Law (Daddy)"))}</div>' + body(597, 604)
    T.append(tribute('inlaws', inner=cl, cls='group-t'))
    # grandchildren
    gc = '<div class="group">Tribute by Grandchildren</div>'
    for nm, a, b_ in [('Naa Ode', 608, 612), ('Dona', 612, 615), ('Korkoi', 615, 619), ('Armah', 619, 623), ('Daniel', 623, 629)]:
        gc += sub(nm) + body(a + 1, b_)
    gc += photo_block(629, 78)
    T.append(tribute('grandchildren', inner=gc, cls='group-t'))
    # siblings
    sb = '<div class="group">Tribute by Siblings</div>' + body(633, 637) + sub('Zena') + body(638, 643)
    T.append(tribute('siblings', inner=sb, cls='group-t'))
    # cousins (title, scripture ref and quote are one paragraph in the source)
    c_lines = [x.strip() for x in plain(643).split('\n') if x.strip()]
    T.append(tribute('cousins', title=esc(c_lines[0].title()), epi=esc(c_lines[1]) + '<br>' + esc(' '.join(c_lines[2:])),
                     inner=body(645, 648)))
    # nephews/nieces
    T.append(tribute('nephews', kicker='Tribute by Nephews and Nieces', epi=inline(653),
                     inner=body(655, 665) + sig(665, 666)))
    # church
    T.append(tribute('church', kicker='Tribute by the Church', title=esc(plain(671).title().replace('Mr.', 'Mr.')),
                     byline=esc(plain(672)), epi=f'<b>{inline(673, keep_bold=False)}</b>',
                     inner=body(674, 682) +
                     verse([682, 683, 684, 685, 687, 688, 689, 690], stanza_breaks=(687,)) +
                     body(691, 695) + photo_block(695, 78)))
    # governing board
    T.append(tribute('board', title=esc(plain(699).title().replace('-', '–')), inner=body(700, 710)))
    # staff
    T.append(tribute('staff', title=esc(plain(711).title()), byline=esc(plain(712).title()),
                     epi='<i>' + '<br>'.join(esc(plain(i)) for i in (713, 714, 715)) + '</i><br>' + esc(plain(716)),
                     inner=body(717, 752) + '<div class="closing-caps">' + ''.join(f'<p>{esc(plain(i))}</p>' for i in (752, 753, 754)) + '</div>'))
    # ABSA
    T.append(tribute('absa', kicker='Tribute by ABSA Bank (formerly Barclays Bank)', title=esc(plain(760).title()),
                     epi=inline(761), inner=body(762, 773)))
    # Osu Salem (source is in capitals; kept as supplied)
    T.append(tribute('osu', kicker='Tribute by Osu Salem', title=esc(plain(777)), inner=body(778, 793, short_group=False), cls='caps-body'))
    # Wellington
    T.append(tribute('wellington', title=esc(plain(796)), byline=esc(plain(798)), epi=inline(800), inner=body(802, 838)))
    # Nortey
    T.append(tribute('nortey', title=esc(plain(841).title()), epi='<i>' + '<br>'.join(esc(plain(i)) for i in range(842, 850)) + '</i><br><span class="by">' + esc(plain(850)) + '</span>',
                     inner=body(851, 858)))
    # Fleischer
    T.append(tribute('fleischer', title='A Tribute to a Dear Friend and Brother', byline='By T. C. Fleischer',
                     inner=body(862, 875)))
    # Solo
    T.append(tribute('solo', title=esc(plain(877).title().replace('Kwei Ayitiah', 'Kwei Ayitiah')), epi=inline(879),
                     inner=body(880, 899) + sig(899)))
    # Johnson family
    T.append(tribute('johnson', title=esc(plain(901).title()), byline=esc(plain(902).replace('BYTHE', 'BY THE')),
                     epi='<i>' + '<br>'.join(esc(plain(i)) for i in (904, 905, 906, 907, 908, 909) if plain(i)) + '</i>',
                     inner=body(911, 926)))
    # Gilbert Ayisi Addo
    T.append(tribute('addo', title=esc(plain(936).title()), inner=body(937, 941)))
    # Adjei
    T.append(tribute('adjei', title=esc(plain(947).title().replace('H.E', 'H.E.')), epi=inline(948),
                     inner=body(950, 958) + verse(range(959, 965)) + body(965, 967)))
    # Mensah
    T.append(tribute('mensah', title=esc(plain(977)), byline=esc(plain(978)), epi=inline(979), inner=body(980, 987)))
    # Ababio
    T.append(tribute('ababio', title=esc(plain(990)), inner=body(991, 1019)))
    # Samuel
    T.append(tribute('samuel', title=esc(plain(1029).title()), inner=body(1031, 1078) + sig(1078, 1080)))
    P.append('\n'.join(T))

    # ---------------- gallery + closing
    P.append(f'''
<section class="chapter gallery plate" id="gallery" data-toc="Family Photographs">
  <h1 class="ch">Family Photographs</h1><div class="orn left"></div>
  <div class="plate-body">{photo_block(1084, 78)}</div>
</section>
<section class="plate plate2"><div class="plate-body">{photo_block(1089, 119)}</div></section>''')

    P.append(f'''
<section class="closing page-closing">
  <div class="cl-wrap">
    <div class="orn"></div>
    <div class="cl-name">Daniel Kwei Ayitiah</div>
    <div class="cl-dates">11 July 1950 to 20 September 2026</div>
    <div class="cl-line">Rest in perfect peace</div>
  </div>
</section>''')

    P.append(f'''
<section class="backcover page-front">
  <div class="back-inner">
    <img class="crest" src="img/image2.png" alt="">
    <div class="back-line">{esc(plain(64))}<br>{esc(plain(65))}</div>
    <div class="back-tag">A legacy that lasts a lifetime</div>
  </div>
</section>''')
    return '\n'.join(P)


# ---------------------------------------------------------------- TOC
def toc_html():
    items = [
        ('order', 'Order of Service'), ('hymns', 'Hymns'), ('bio', 'Biography'),
        ('tributes', 'Tributes'),
    ]
    trib = [
        ('wife', 'Tribute by his wife'), ('children', 'Tribute by Children'),
        ('inlaws', 'Tribute by Children-in-Law'), ('grandchildren', 'Tribute by Grandchildren'),
        ('siblings', 'Tribute by Siblings'), ('cousins', 'Tribute from Cousins'),
        ('nephews', 'Tribute by Nephews and Nieces'), ('church', 'Calvary Congregation, Haatso'),
        ('board', 'The Light Academy Governing Board'), ('staff', 'The Light Academy Staff'),
        ('absa', 'ABSA Bank and Retired Staff Association'), ('osu', 'Osu Salem Classmates'),
        ('wellington', 'Professor H. Nii-Adziri Wellington'), ('nortey', 'Rev. Alfred Nortey'),
        ('fleischer', 'T. C. Fleischer'), ('solo', 'Solo'), ('johnson', 'The Johnson Family'),
        ('addo', 'Gilbert Ayisi Addo'), ('adjei', 'H.E. Edwin Nii Adjei'), ('mensah', 'George Alfred Mensah'),
        ('ababio', 'Felix Crabbe Ababio'), ('samuel', 'Samuel Greyham'),
    ]
    def row(id, label, cls=''):
        pg = TOC.get(id, '')
        return f'<li class="{cls}"><span class="t">{esc(label)}</span><span class="d"></span><span class="p">{pg}</span></li>'
    h = '<ul class="toc">'
    h += row('order', 'Order of Service', 'main') + row('hymns', 'Hymns', 'main') + row('bio', 'Biography', 'main') + row('tributes', 'Tributes', 'main')
    for id, label in trib:
        h += row(id, label, 'sub')
    h += row('gallery', 'Family Photographs', 'main')
    return h + '</ul>'


W, H = 148 + 2 * BLEED, 210 + 2 * BLEED
FONTCSS = re.sub(r'url\(([\w]+\.woff2)\)', r'url(../fonts/\1)', open(f'{S}/fonts/fonts_local.css').read() + open(f'{S}/fonts/fonts2_local.css').read() + open(f'{S}/fonts/fonts3_local.css').read())
CSS = open(f'{OUT}/book.css').read().replace('@PW@', f'{W:g}').replace('@PH@', f'{H:g}').replace('@BLEED@', f'{BLEED:g}')
doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Daniel Kwei Ayitiah — A Legacy That Lasts a Lifetime</title>
<style>
{FONTCSS}
:root {{
  --bleed: {BLEED}mm; --pw: {W}mm; --ph: {H}mm;
  --body-font: "{BODY_FONT}", "Gentium Book Plus", Georgia, serif; --body-pt: {BODY_PT}pt; --leading: {LEADING};
}}
{CSS}
</style></head><body>
{build_pages().replace("@@TOC@@", toc_html())}
</body></html>'''
if MARK:
    doc = re.sub(r'(<section class="(?:chapter|tribute)[^"]*" id="(\w+)"[^>]*>)', r'\1<span class="mk">MK_\2_MK</span>', doc)
    doc = doc.replace('</style>', '.mk{position:absolute;font-size:2px;color:#fefefe}</style>', 1)
open(f'{OUT}/book.html', 'w').write(doc)
print('wrote book.html', len(doc))
