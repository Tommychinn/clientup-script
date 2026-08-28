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

## Pre-call engagement flow

```bash
node tools/fetch-notion.js 49e41065-36d9-421e-8011-94d045893637 tools/precall.json
python3 tools/build-precall.py
```

That page is a picker, not a document: the rep answers a few questions about the
prospect and gets the exact messages back in order with a copy button on each.

`precall_model.py` holds the decision logic — the questions, which answers unlock
which follow-up, and which messages each complete path produces. It contains **no
message text**. Every message and every blue direction line is identified by its
opening words and resolved against the Notion block tree at build time, so the
words on the page are always the words in Notion. Reword a message in Notion and
the lookup either finds it or fails the build; it can never ship stale copy.

Placeholders (`[name]`, `[your name]`, `xyz.com`, `XYZ niche`) are filled from
inputs at the top of the page and resolved into both the on-screen text and the
copied text. Anything left blank stays in its bracketed form so a half-filled
message is obviously half-filled.

**Each sequence rule is gated on the fewest answers that actually determine its
message.** A business owner's opening message is the same whether or not they
have a website, so its rule doesn't mention the website question — it appears the
moment segment and email type are chosen. Getting this wrong doesn't break the
build, it just makes the rep answer questions before seeing a message they could
already have sent, so keep rules minimal when you add a branch.

The ecom / PPL-niche split is deliberately not a question. The source offers those
as two example openings to choose between, not as a fork in the conversation, so
both render inside one step as variants.

The page shows only what a rep uses mid-conversation: the purpose, the CRM check,
then the flow. The Message Components reference is not rendered — Notion is where
you read and edit those.

**A message that appears twice in Notion must match in both places.** Each one is
written once inside the flow and once under Message Components. The build
compares the whole message, resource list included, not just the opening line. If
the two disagree it uses the Message Components definition — the doc calls that
the canonical one — and prints a warning naming the difference. Reconcile it in
Notion rather than leaving the warning standing.

**One rule the model enforces that the source doesn't:** every path asks a
qualifier (Q1 or Q2) before it sends resources. The marketer branch for a
prospect who shares a website had no Q1 in Notion while the other three marketer
branches did; Tommy confirmed on 2026-08-28 that it should, so the model adds it.
That is the only place the page deliberately runs ahead of the source — if you
add a branch, keep the qualifier-before-resources rule.

To change the flow — a new segment, a new branch — edit `precall_model.py`. To
change what a message says, edit Notion.
