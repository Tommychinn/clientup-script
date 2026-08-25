#!/usr/bin/env python3
"""Build pitch-a/index.html from a fetched Notion block tree.

    node tools/fetch-notion.js 0dae5998-6672-4a27-9c93-a9026201443a tools/clientup.json
    python3 tools/build-pitch-a.py

Renders sections 5 to 9 only. Every spoken string comes straight out of the
Notion source — nothing is retyped here, so a re-sync can never drift.

Classification (the shared library convention: black = say aloud, blue = context):
  * struck-through blocks are dropped (superseded copy)
  * a line that is entirely italic is a direction to the rep      -> blue block
  * a bold+italic lead-in followed by more text is a cue          -> blue inline, rest black
  * anything else is spoken                                        -> black
  * BRANCH_LABELS are spoken-by-nobody scale branches             -> blue block
"""
import json, html, re, os, sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC      = os.path.join(ROOT_DIR, 'tools', 'clientup.json')
TEMPLATE = os.path.join(ROOT_DIR, 'tools', 'page-template.html')
OUT      = os.path.join(ROOT_DIR, 'pitch-a', 'index.html')

FIRST_SECTION = '5.'
STOP_SECTION  = '10.'
# Tommy renamed this section; the Notion heading still says "High level context".
TITLE_OVERRIDES = {'5.': '5. A High-Level Context'}
BRANCH_LABELS = {'9 or 10:', '7 or 8:', '6 or below:'}

d = json.load(open(SRC))
B, ROOT = d['blocks'], d['root']


def segs(b):
    t = (b.get('properties') or {}).get('title') or []
    return [(s[0], set(f[0] for f in (s[1] or [])) if len(s) > 1 else set()) for s in t]


def esc(x):
    return html.escape(x, quote=False)


def render_inline(sg):
    """-> (html, is_context_block). Empty html means: skip this block."""
    live = [(t, f) for t, f in sg if 's' not in f]          # drop struck copy
    if not ''.join(t for t, _ in live).strip():
        return '', False
    plain = ''.join(t for t, _ in live).strip()
    if plain in BRANCH_LABELS:
        return '<strong>%s</strong>' % esc(plain), True

    visible = [(t, f) for t, f in live if t.strip()]

    def marked(t, f):
        s = esc(t)
        if 'b' in f:
            return '<strong>%s</strong>' % s
        return s

    # bold+italic cue, then the line the rep actually says
    if len(visible) > 1 and {'i', 'b'} <= visible[0][1]:
        cue = visible[0]
        rest = live[live.index(cue) + 1:]
        return ('<span class="ctx">%s</span> %s' % (
            esc(cue[0].strip()),
            ''.join(marked(t, f) for t, f in rest).strip())).strip(), False

    # whole line italic -> a direction, never read out
    if all('i' in f for t, f in visible):
        return ''.join(marked(t, f) for t, f in live).strip(), True

    out = []
    for t, f in live:
        if 'b' in f:
            out.append('<strong>%s</strong>' % esc(t))
        elif 'i' in f:
            out.append('<span class="ctx">%s</span>' % esc(t))
        else:
            out.append(esc(t))
    return ''.join(out).strip(), False


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


flat = []
def walk(bid, depth):
    b = B.get(bid)
    if not b:
        return
    flat.append((depth, b.get('type'), b))
    for c in b.get('content') or []:
        walk(c, depth + 1)
walk(ROOT, 0)

start = end = None
for i, (_, t, b) in enumerate(flat):
    head = ''.join(s for s, _ in segs(b)).strip()
    if t == 'header' and head.startswith(FIRST_SECTION):
        start = i
    if t == 'header' and head.startswith(STOP_SECTION):
        end = i
if start is None or end is None:
    sys.exit('could not locate section %s / %s in the source' % (FIRST_SECTION, STOP_SECTION))

body, toc, stack = [], [], []


def close_lists():
    while stack:
        body.append('</li></ul>')
        stack.pop()


for depth, t, b in flat[start:end]:
    sg = segs(b)
    raw = ''.join(s for s, _ in sg).strip()

    if t in ('header', 'sub_header', 'sub_sub_header'):
        close_lists()
        label = TITLE_OVERRIDES.get(raw[:2], raw)
        sid = slug(label)
        # 6.4 sits a level deeper in Notion than 6.1-6.3 but is numbered as their
        # peer, so every numbered sub-section renders at the same level.
        tag = 'h2' if t == 'header' else 'h3'
        body.append('<%s id="%s">%s</%s>' % (tag, sid, esc(label), tag))
        toc.append(('l1' if t == 'header' else 'l2', sid, label))
        continue

    inner, is_ctx = render_inline(sg)
    if not inner:
        continue
    cls = ' class="ctx-block"' if is_ctx else ''

    if t == 'bulleted_list':
        while stack and depth < stack[-1]:
            body.append('</li></ul>')
            stack.pop()
        if stack and depth == stack[-1]:
            body.append('</li><li%s>' % cls)
        else:
            body.append('<ul><li%s>' % cls)
            stack.append(depth)
        body.append(inner)
    else:
        close_lists()
        body.append('<p%s>%s</p>' % (cls, inner))

close_lists()
body_html = '\n'.join(body)

# Section 9 used to repeat section 8's opening line word for word. Tommy removed it
# from the source on 2026-08-25. If it ever comes back, flag it on the page rather
# than dropping it, so nobody asks the same question twice on a live call.
dup = 'Ok, well that’s everything in terms of how it works. What questions do you have specifically in relation to the process?'
h9 = [t for t in toc if t[0] == 'l1' and t[2].startswith('9.')][0]
anchor = '<h2 id="%s">%s</h2>\n<p>%s</p>' % (h9[1], esc(h9[2]), dup)
if anchor in body_html:
    body_html = body_html.replace(anchor, (
        '<h2 id="%s">%s</h2>\n'
        '<p class="ctx-block">Build note: the source repeats section 8’s opening line here '
        'verbatim. Shown below as written — don’t ask it twice.</p>\n'
        '<p>%s</p>') % (h9[1], esc(h9[2]), dup))
    print('note: section 9 still duplicates section 8’s opener — flagged on the page')

nav = '\n'.join(
    '    <a class="toc-%s" href="#%s">%s</a>' % (lvl, sid, html.escape(label))
    for lvl, sid, label in toc)

page = open(TEMPLATE).read().replace('{{NAV}}', nav).replace('{{BODY}}', body_html)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w').write(page)
print('wrote %s (%d blocks, %d nav entries)' % (OUT, len(body), len(toc)))
