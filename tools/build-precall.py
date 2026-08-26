#!/usr/bin/env python3
"""Build pre-call-engagement/index.html from the Pre-Call Engagement Process doc.

    node tools/fetch-notion.js 49e41065-36d9-421e-8011-94d045893637 tools/precall.json
    python3 tools/build-precall.py

The page is a picker, not a document: the rep answers a few questions about the
prospect and the exact messages to send come back in order, ready to copy.

Every word of every message comes out of the Notion block tree at build time.
`precall-model.py` holds only the decision logic and the leading words used to
find each block — if Tommy rewords a message in Notion, the lookup either finds
the new text or fails the build. It can never ship stale copy.
"""
import json, html, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from precall_model import (MESSAGES, NOTES, QUESTIONS, SEQUENCE,
                           NEEDS_NICHE, NEEDS_SITE)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC      = os.path.join(ROOT_DIR, 'tools', 'precall.json')
OUT      = os.path.join(ROOT_DIR, 'pre-call-engagement', 'index.html')

d = json.load(open(SRC))
B, ROOT = d['blocks'], d['root']


def segs(b):
    """Text segments of a block as [(text, {formats})]."""
    t = (b.get('properties') or {}).get('title') or []
    return [(s[0], set(f[0] for f in (s[1] or [])) if len(s) > 1 else set()) for s in t]


def plain(b):
    return ''.join(t for t, _ in segs(b))


def marked(b):
    """Plain text with ** around bold runs — matches how the model keys blocks."""
    out = []
    for t, f in segs(b):
        out.append('**%s**' % t if 'b' in f else t)
    return ''.join(out)


def norm(s):
    """Loose compare: curly quotes, dashes and runs of whitespace don't count."""
    s = s.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    s = s.replace('—', '-').replace('–', '-').replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', s).strip().lower()


def find_block(lead, types):
    """The single block of one of `types` whose text starts with `lead`."""
    want = norm(lead)
    hits = [b for b in B.values()
            if b.get('type') in types and norm(marked(b)).startswith(want)]
    if len(hits) == 1:
        return hits[0]
    # Quotes repeat verbatim across branches in the source (R5 appears three
    # times). Identical duplicates are fine — differing ones are not.
    if hits and len({norm(marked(h)) for h in hits}) == 1:
        return hits[0]
    sys.exit('lookup failed for %r — matched %d blocks%s' % (
        lead, len(hits),
        '' if not hits else ':\n  ' + '\n  '.join(norm(marked(h))[:90] for h in hits)))


# ---------------------------------------------------------------------------
# Message assembly: a quote block plus its children become one pasteable message
# ---------------------------------------------------------------------------
def seg_list(b):
    return [{'t': t, **({'b': 1} if 'b' in f else {})} for t, f in segs(b) if t]


def split_lines(b):
    """A quote may hold hard newlines; each becomes its own paragraph."""
    lines, cur = [], []
    for t, f in segs(b):
        parts = t.split('\n')
        for i, p in enumerate(parts):
            if i:
                lines.append(cur)
                cur = []
            if p:
                cur.append({'t': p, **({'b': 1} if 'b' in f else {})})
    lines.append(cur)
    return [l for l in lines if l]


def build_message(mid, lead):
    q = find_block(lead, ('quote',))
    body = [{'type': 'p', 'segs': l} for l in split_lines(q)]
    items = []
    for cid in q.get('content') or []:
        c = B.get(cid)
        if not c:
            continue
        if c.get('type') == 'numbered_list':
            items.append(seg_list(c))
        else:
            if items:
                body.append({'type': 'ol', 'items': items})
                items = []
            if plain(c).strip():
                body.append({'type': 'p', 'segs': seg_list(c)})
    if items:
        body.append({'type': 'ol', 'items': items})
    return {'id': mid, 'body': body}


messages = {mid: build_message(mid, lead) for mid, lead in MESSAGES.items()}
notes = {nid: ''.join(t for t, _ in segs(find_block(lead, ('text',))))
         for nid, lead in NOTES.items()}

# The direction lines are written to introduce the message that follows, so they
# end in a colon. On this page the message sits in its own card directly below,
# which makes the colon read as a dangling fragment.
notes = {k: re.sub(r'\s*:\s*$', '', v).strip() for k, v in notes.items()}

DATA = {
    'questions': QUESTIONS,
    'sequence': [{'match': r['match'], 'steps': [list(s) for s in r['steps']]}
                 for r in SEQUENCE],
    'messages': messages,
    'notes': notes,
    'needsNiche': NEEDS_NICHE,
    'needsSite': NEEDS_SITE,
}

# ---------------------------------------------------------------------------
# Static sections rendered straight from the source
# ---------------------------------------------------------------------------
def esc(x):
    return html.escape(x, quote=False)


def inline(b):
    out = []
    for t, f in segs(b):
        s = esc(t)
        if 'b' in f:
            s = '<strong>%s</strong>' % s
        elif 'i' in f:
            s = '<em>%s</em>' % s
        out.append(s)
    return ''.join(out).strip()


def render_children(bid, skip_types=()):
    """Render a block's children as nested lists / paragraphs."""
    out, stack = [], None
    for cid in B[bid].get('content') or []:
        c = B.get(cid)
        if not c or c.get('type') in skip_types or not plain(c).strip():
            continue
        t = c.get('type')
        if t in ('bulleted_list', 'numbered_list'):
            tag = 'ul' if t == 'bulleted_list' else 'ol'
            if stack != tag:
                if stack:
                    out.append('</%s>' % stack)
                out.append('<%s>' % tag)
                stack = tag
            out.append('<li>%s%s</li>' % (inline(c), render_children(cid)))
        else:
            if stack:
                out.append('</%s>' % stack)
                stack = None
            out.append('<p>%s</p>' % inline(c))
    if stack:
        out.append('</%s>' % stack)
    return ''.join(out)


def find_header(prefix, types=('header', 'sub_header', 'sub_sub_header')):
    hits = [(bid, b) for bid, b in B.items()
            if b.get('type') in types and norm(plain(b)).startswith(norm(prefix))]
    if len(hits) != 1:
        sys.exit('header lookup failed for %r — matched %d' % (prefix, len(hits)))
    return hits[0]


# Purpose callout
callout = [b for b in B.values() if b.get('type') == 'callout']
if len(callout) != 1:
    sys.exit('expected exactly one purpose callout, found %d' % len(callout))
callout_id = [bid for bid, b in B.items() if b is callout[0]][0]
purpose_html = render_children(callout_id)

# Step 1 — CRM Check: the numbered list that follows that header, at page level
page_children = B[ROOT].get('content') or []
h1_id, _ = find_header('Step 1')
h2_id, _ = find_header('Step 2')
i1, i2 = page_children.index(h1_id), page_children.index(h2_id)
crm_html = []
stack = None
for cid in page_children[i1 + 1:i2]:
    c = B.get(cid)
    if not c or not plain(c).strip():
        continue
    if c.get('type') == 'numbered_list':
        if stack != 'ol':
            crm_html.append('<ol>')
            stack = 'ol'
        crm_html.append('<li>%s%s</li>' % (inline(c), render_children(cid)))
    else:
        if stack:
            crm_html.append('</%s>' % stack)
            stack = None
        crm_html.append('<p>%s</p>' % inline(c))
if stack:
    crm_html.append('</%s>' % stack)
crm_html = ''.join(crm_html)

# Message Components reference
comp_hdr_id, _ = find_header('Message Components', ('header',))
ci = page_children.index(comp_hdr_id)
comp_html = []
for cid in page_children[ci + 1:]:
    c = B.get(cid)
    if not c:
        continue
    t = c.get('type')
    if t == 'sub_header':
        comp_html.append('<h3 id="cmp-%s">%s</h3>' % (
            re.sub(r'[^a-z0-9]+', '-', plain(c).lower()).strip('-'), inline(c)))
    elif t == 'quote':
        lines = ''.join('<p>%s</p>' % ''.join(
            ('<strong>%s</strong>' % esc(s['t'])) if s.get('b') else esc(s['t']) for s in l)
            for l in split_lines(c))
        comp_html.append('<div class="msg static">%s%s</div>' % (lines, render_children(cid)))
    elif plain(c).strip():
        comp_html.append('<p class="ctx-block">%s</p>' % inline(c))
comp_html = ''.join(comp_html)

# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------
tpl = open(os.path.join(ROOT_DIR, 'tools', 'precall-template.html')).read()
page = (tpl
        .replace('{{PURPOSE}}', purpose_html)
        .replace('{{CRM}}', crm_html)
        .replace('{{COMPONENTS}}', comp_html)
        .replace('{{DATA}}', json.dumps(DATA, ensure_ascii=False, separators=(',', ':'))))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w').write(page)
print('wrote %s — %d messages, %d notes, %d questions, %d sequence rules' % (
    OUT, len(messages), len(notes), len(QUESTIONS), len(SEQUENCE)))
