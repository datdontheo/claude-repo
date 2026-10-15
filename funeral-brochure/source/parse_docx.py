import re,html,json,sys
base='/tmp/claude-0/-home-user-claude-repo/b08694ae-3575-5ddf-bbbd-39938be72a83/scratchpad/docx_x/word/'
x=open(base+'document.xml',encoding='utf8').read()
rels=open(base+'_rels/document.xml.rels',encoding='utf8').read()
rid={}
for m in re.finditer(r'<Relationship [^>]*>',rels):
    s=m.group(0)
    i=re.search(r'Id="([^"]+)"',s); t=re.search(r'Target="([^"]+)"',s)
    if i and t: rid[i.group(1)]=t.group(1)
paras=re.findall(r'<w:p[ >].*?</w:p>',x,flags=re.S)
def runs_of(p):
    out=[]
    for r in re.findall(r'<w:r[ >].*?</w:r>',p,flags=re.S):
        rpr=re.search(r'<w:rPr>(.*?)</w:rPr>',r,flags=re.S)
        rp=rpr.group(1) if rpr else ''
        b=bool(re.search(r'<w:b/>|<w:b w:val="(1|true)"',rp))
        i=bool(re.search(r'<w:i/>|<w:i w:val="(1|true)"',rp))
        u=bool(re.search(r'<w:u ',rp))
        txt=''
        for m in re.finditer(r'<w:t(?: [^>]*)?>([^<]*)</w:t>|(<w:tab/>)|(<w:br[^>]*/>)',r):
            if m.group(1) is not None: txt+=html.unescape(m.group(1))
            elif m.group(2): txt+='\t'
            else: txt+='\n'
        if txt: out.append((txt,b,i,u))
    return out
blocks=[]
for idx,p in enumerate(paras):
    ppr=re.search(r'<w:pPr>(.*?)</w:pPr>',p,flags=re.S)
    pp=ppr.group(1) if ppr else ''
    jc=re.search(r'<w:jc w:val="(\w+)"',pp)
    style=re.search(r'<w:pStyle w:val="([^"]+)"',pp)
    imgs=[rid.get(r) for r in re.findall(r'r:embed="(rId\d+)"',p)]
    runs=runs_of(p)
    blocks.append(dict(idx=idx,jc=jc.group(1) if jc else None,style=style.group(1) if style else None,imgs=imgs,runs=runs))
json.dump(blocks,open('blocks.json','w'))
if __name__=='__main__':
    for b in blocks:
        t=''.join(r[0] for r in b['runs']).strip()
        if not t or b['idx']<366: continue
        allb=all(r[1] for r in b['runs'] if r[0].strip())
        alli=all(r[2] for r in b['runs'] if r[0].strip())
        if len(t)<130 and (allb or b['jc']=='center' or b['style']):
            print(b['idx'],('B' if allb else '-')+('I' if alli else '-')+(b['jc'] or '-')[:1],b['style'] or '',t[:90])
