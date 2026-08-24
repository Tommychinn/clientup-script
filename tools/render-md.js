#!/usr/bin/env node
// Render a fetched Notion block tree to indented markdown-ish text for reading.
const fs = require('fs');
const { root, blocks } = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));

function text(props) {
  if (!props || !props.title) return '';
  return props.title
    .map((seg) => {
      let t = seg[0] || '';
      for (const f of seg[1] || []) {
        if (f[0] === 'i') t = `_${t}_`;
        if (f[0] === 'b') t = `**${t}**`;
        if (f[0] === 'c') t = `\`${t}\``;
      }
      return t;
    })
    .join('');
}

const out = [];
function walk(id, depth) {
  const b = blocks[id];
  if (!b) { out.push(`${'  '.repeat(depth)}[missing ${id}]`); return; }
  const t = b.type;
  const label = {
    page: '# PAGE', header: '## H1', sub_header: '### H2', sub_sub_header: '#### H3',
    text: '', bulleted_list: '-', numbered_list: '1.', toggle: '▸ TOGGLE',
    quote: '>', callout: 'CALLOUT', divider: '---', to_do: '[ ]',
    column_list: 'COLUMNS', column: 'COL', table: 'TABLE', table_row: 'ROW',
    code: 'CODE', image: 'IMAGE',
  }[t];
  const pad = '  '.repeat(depth);
  const body = text(b.properties);
  if (t === 'divider') out.push(`${pad}---`);
  else if (t === 'table_row') {
    const cells = Object.values(b.properties || {}).map((c) =>
      (c || []).map((s) => s[0]).join(''));
    out.push(`${pad}| ${cells.join(' | ')} |`);
  } else out.push(`${pad}${label !== undefined ? label : '?' + t} ${body}`.trimEnd());
  for (const c of b.content || []) walk(c, depth + 1);
}
walk(root, 0);
fs.writeFileSync(process.argv[3], out.join('\n'));
console.log(`lines: ${out.length}`);
