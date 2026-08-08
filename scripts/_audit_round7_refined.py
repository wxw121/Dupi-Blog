from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "scripts" / "reports" / "audit"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
NUM_RE = re.compile(r'^(\d+)\.')
STRICT_MARKER_RE = re.compile(r'<!--\s*topup-batch|TODO|TBD|待补|待重制|图片 prompt|替换正文占位|等待生成 PNG|生成 PNG 后|全系列配图约定|系列配图 prompts 已就绪|请完成本篇|配图 prompts 已就绪', re.I)
HEADING_RE = re.compile(r'^(#{2,6})\s+(.+)$')
PROSE_EXCLUDE_RE = re.compile(r'^(#{1,6})\s+|^\|.*\|\s*$|^-\s+|^\d+\.\s+|^!\[|^>|^---$')

def article_number(path):
    return int(NUM_RE.match(path.name).group(1))

def is_prose(line):
    return bool(line) and not PROSE_EXCLUDE_RE.match(line)

def scan(path):
    text = path.read_text(encoding='utf-8', errors='replace')
    lines = text.splitlines()
    headings=[]; markers=[]; empty=[]; weak=[]; code_starts=[]; mermaid=0; fences=0; images=[]
    in_fence=False
    for i,line in enumerate(lines, 1):
        if line.startswith('```'):
            if line.strip() == '```mermaid': mermaid += 1
            if not in_fence: code_starts.append(i)
            in_fence = not in_fence
            fences += 1
            continue
        if in_fence: continue
        if STRICT_MARKER_RE.search(line): markers.append(f'L{i}: {line.strip()}')
        m=HEADING_RE.match(line)
        if m: headings.append({'line':i,'level':len(m.group(1)),'text':m.group(2).strip()})
        if re.match(r'^!\[.*?\]\(.*?\)', line): images.append(i)
    for h in headings:
        if h['text'] == '目录': continue
        nxt = next((x for x in headings if x['line'] > h['line'] and x['level'] <= h['level']), None)
        end = nxt['line'] - 1 if nxt else len(lines)
        content = 0; has_prose=False; inf=False
        for j in range(h['line'], end):
            t=lines[j].strip()
            if t.startswith('```'):
                inf = not inf; continue
            if inf or not t: continue
            content += 1
            if is_prose(t): has_prose=True
        if content == 0: empty.append(f"L{h['line']}: {h['text']}")
        elif not has_prose: weak.append(f"L{h['line']}: {h['text']}")
    # duplicate exact visible paragraphs
    paras=[]; buf=[]; inf=False
    for line in lines:
        t=line.strip()
        if t.startswith('```'):
            inf = not inf; continue
        if inf: continue
        if not t or PROSE_EXCLUDE_RE.match(t):
            if buf:
                p=' '.join(buf).strip()
                if len(p) >= 45: paras.append(p)
                buf=[]
        else:
            buf.append(t)
    if buf:
        p=' '.join(buf).strip()
        if len(p) >= 45: paras.append(p)
    counts={}
    for p in paras: counts[p]=counts.get(p,0)+1
    dup_paras=[f'{c}x {p[:120]}' for p,c in sorted(counts.items(), key=lambda kv:-kv[1]) if c>1][:5]
    # only exact duplicate full heading text; not 1.1/1.2 shared parent number
    seen={}
    for h in headings:
        if h['text'] != '目录': seen.setdefault(h['text'],[]).append(h['line'])
    dup_heads=[f'{k} x{len(v)} @ {",".join(map(str,v[:5]))}' for k,v in seen.items() if len(v)>1]
    code_no_intro=[]; code_no_after=[]
    for start in code_starts:
        if lines[start-1].strip() == '```mermaid': continue
        prev=[]
        for j in range(start-2, max(-1,start-8), -1):
            t=lines[j].strip()
            if not t: continue
            prev.append(t)
            if len(prev)>=4: break
        if not any(is_prose(x) and not x.startswith('```') for x in prev): code_no_intro.append(f'L{start}')
        close=None
        for j in range(start, len(lines)):
            if lines[j].startswith('```'):
                close=j+1; break
        if close:
            nxt=[]
            for j in range(close, min(len(lines), close+7)):
                t=lines[j].strip()
                if not t: continue
                nxt.append(t)
                if len(nxt)>=4: break
            if not any(is_prose(x) and not x.startswith('```') for x in nxt): code_no_after.append(f'L{start}')
    n=article_number(path)
    hanzi=len(re.sub(r'[^\u4e00-\u9fff]', '', text))
    code_blocks=max(0, fences//2 - mermaid)
    tables=sum(1 for line in lines if re.match(r'^\|.+\|\s*$', line.strip()))
    flags=[]; score=0
    if markers: flags.append('strict-marker'); score += 6
    if fences % 2: flags.append('odd-code-fence'); score += 8
    if empty: flags.append('empty-section'); score += min(6, len(empty)*3)
    if weak: flags.append('weak-heading'); score += min(5, len(weak))
    if dup_paras: flags.append('duplicate-paragraph'); score += 4
    if dup_heads: flags.append('duplicate-heading'); score += 3
    if code_no_intro: flags.append('code-no-intro'); score += min(3, len(code_no_intro))
    if code_no_after: flags.append('code-no-after'); score += min(2, len(code_no_after))
    if n >= 156 and hanzi < 1800: flags.append('thin-late-article'); score += 2
    if n >= 156 and code_blocks == 0: flags.append('no-code-late-practical'); score += 1
    if n >= 179 and mermaid == 0 and not images and tables < 8: flags.append('low-visual-structure'); score += 1
    if not score: return None
    return {
        'file': path.name, 'score': score, 'flags': flags, 'hanzi': hanzi,
        'codeBlocks': code_blocks, 'mermaid': mermaid, 'images': len(images), 'tables': tables,
        'markers': markers[:5], 'emptySections': empty[:8], 'weakHeadings': weak[:10],
        'duplicateHeadings': dup_heads[:5], 'duplicateParagraphs': dup_paras[:5],
        'codeNoIntro': code_no_intro[:8], 'codeNoAfter': code_no_after[:8]
    }

files=sorted([p for p in ROOT.glob('*.md') if NUM_RE.match(p.name) and article_number(p) >= 50], key=article_number)
rows=[r for p in files if (r:=scan(p))]
rows.sort(key=lambda r:(-r['score'], r['file']))
report_path = REPORT_DIR / 'audit-round7-refined-report.json'
report_path.write_text(json.dumps({'file_count':len(files), 'issue_count':len(rows), 'top':rows[:120]}, ensure_ascii=False, indent=2), encoding='utf-8')
for r in rows[:50]:
    print(f"{r['score']:>2} {r['file']} :: {','.join(r['flags'])}")
    for k in ('markers','emptySections','weakHeadings','duplicateParagraphs','codeNoIntro','codeNoAfter'):
        vals=r.get(k) or []
        if vals:
            print('   '+k+': '+ ' || '.join(vals[:3]))
