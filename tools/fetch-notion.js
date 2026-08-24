#!/usr/bin/env node
// Pull a public Notion page's full block tree via the unofficial web API.
// Usage: node fetch-notion.js <pageId-with-dashes> <out.json>

const PAGE = process.argv[2];
const OUT = process.argv[3] || 'notion-blocks.json';
const fs = require('fs');

const blocks = {};

async function loadChunk(cursor, chunkNumber) {
  const res = await fetch('https://www.notion.so/api/v3/loadPageChunk', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0' },
    body: JSON.stringify({
      pageId: PAGE,
      limit: 100,
      cursor,
      chunkNumber,
      verticalColumns: false,
    }),
  });
  if (!res.ok) throw new Error(`loadPageChunk ${res.status}: ${await res.text()}`);
  return res.json();
}

async function syncRecords(ids) {
  const res = await fetch('https://www.notion.so/api/v3/syncRecordValues', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0' },
    body: JSON.stringify({
      requests: ids.map((id) => ({ pointer: { table: 'block', id, spaceId: SPACE }, version: -1 })),
    }),
  });
  if (!res.ok) throw new Error(`syncRecordValues ${res.status}: ${await res.text()}`);
  return res.json();
}

let SPACE = null;

function absorb(recordMap) {
  const bl = (recordMap && recordMap.block) || {};
  for (const [id, rec] of Object.entries(bl)) {
    if (rec && rec.value) {
      const v = rec.value.value || rec.value;
      blocks[id] = v;
      if (!SPACE && v.space_id) SPACE = v.space_id;
    }
  }
}

(async () => {
  let cursor = { stack: [] };
  let chunkNumber = 0;
  for (let i = 0; i < 60; i++) {
    const data = await loadChunk(cursor, chunkNumber);
    absorb(data.recordMap);
    if (!data.cursor || !data.cursor.stack || data.cursor.stack.length === 0) break;
    cursor = data.cursor;
    chunkNumber += 1;
  }

  // Resolve any referenced-but-unfetched children.
  for (let round = 0; round < 8; round++) {
    const missing = new Set();
    for (const b of Object.values(blocks)) {
      for (const cid of b.content || []) if (!blocks[cid]) missing.add(cid);
    }
    if (!missing.size) break;
    const ids = [...missing];
    for (let i = 0; i < ids.length; i += 80) {
      const data = await syncRecords(ids.slice(i, i + 80));
      absorb(data.recordMap || { block: data.recordMapWithRoles?.block });
      // syncRecordValues returns {recordMap:{block:{...}}}
    }
  }

  fs.writeFileSync(OUT, JSON.stringify({ root: PAGE, blocks }, null, 2));
  console.log(`blocks: ${Object.keys(blocks).length} -> ${OUT}`);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
