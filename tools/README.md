# tools

Re-sync the pages here from the source Notion doc.

```bash
node tools/fetch-notion.js 0dae5998-6672-4a27-9c93-a9026201443a tools/clientup.json
python3 tools/build-pitch-a.py
```

`fetch-notion.js` pulls a **public** Notion page's full block tree through Notion's
unauthenticated web API — no token needed, but it only works while the page is
shared publicly. `render-md.js` turns that JSON into readable text if you want to
eyeball the source or diff it against a previous pull.

`build-pitch-a.py` generates `pitch-a/index.html` straight from the block tree, so
every spoken line on the page is the Notion text character for character. Nothing
is retyped by hand — that is the point. If a line looks wrong on the page, fix it
in Notion and re-run, don't edit the HTML.

It renders **sections 5 to 9 only** (`FIRST_SECTION` / `STOP_SECTION` at the top of
the script). To add the rest of the pitch, widen that range.

## Conventions the build enforces

- **Black text is said aloud. Blue text is backing context and is never read out.**
- Struck-through blocks in Notion are treated as superseded and dropped.
- A fully italic line is a direction to the rep, so it renders blue.
- A bold+italic lead-in like *(if they're already running creatives)* renders blue
  inline, and the rest of the line stays black because the rep says it.
- The 1–10 branch labels (`9 or 10:` etc.) render blue — they're signposts, not script.
- Section 5's heading is renamed to "A High-Level Context" via `TITLE_OVERRIDES`;
  the Notion source still calls it "High level context".
- Section 6.4 sits one level deeper than 6.1–6.3 in Notion but is numbered as their
  peer, so all numbered sub-sections render at the same heading level.
- Section 9 repeats section 8's opening line word for word. It stays on the page
  with a blue build note so nobody asks it twice. The build fails loudly if that
  line stops matching, rather than silently dropping the note.
