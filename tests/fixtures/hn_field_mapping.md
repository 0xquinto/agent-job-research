# HN Algolia API Field Mapping

Source thread: "Ask HN: Who is hiring? (March 2026)"
Thread objectID: 47219668
Fetched: 2026-03-28
API endpoint used: `https://hn.algolia.com/api/v1/search?tags=comment,story_47219668&hitsPerPage=3`

---

## Top-level response fields

| Field | Type | Description |
|---|---|---|
| `hits` | array | The comment objects |
| `nbHits` | number | Total matching comments (483 for this thread) |
| `nbPages` | number | Total pages at current hitsPerPage |
| `hitsPerPage` | number | Page size requested |
| `page` | number | Current page (0-indexed) |
| `query` | string | Always empty string when filtering by tags only |
| `params` | string | URL-encoded query params echoed back |
| `processingTimeMS` | number | Server processing time |
| `exhaustive` | object | `{ nbHits: bool, typo: bool }` — result completeness flags |

---

## Per-hit fields (comment objects)

| Field | Type | Always present | Description |
|---|---|---|---|
| `objectID` | string | yes | Unique HN item ID for this comment |
| `author` | string | yes | HN username of the poster |
| `comment_text` | string | yes | The job post body as raw HTML string (see below) |
| `story_id` | number | yes | The parent thread's numeric ID (same as the thread's objectID cast to int) |
| `parent_id` | number | yes | Immediate parent item ID — key field for depth detection (see below) |
| `story_title` | string | yes | Title of the parent thread, e.g. "Ask HN: Who is hiring? (March 2026)" |
| `created_at` | string | yes | ISO 8601 timestamp, e.g. `"2026-03-16T13:48:17Z"` |
| `created_at_i` | number | yes | Unix epoch integer version of `created_at` |
| `updated_at` | string | yes | ISO 8601 — last indexed update (not last edited) |
| `children` | array of numbers | no | Child comment IDs. Present only when replies exist; absent on leaf nodes |
| `_tags` | array of strings | yes | Algolia tags: always includes `"comment"`, `"author_{username}"`, `"story_{id}"` |
| `_highlightResult` | object | yes | Algolia highlight markup for `author`, `comment_text`, `story_title` — safe to ignore in parsing |

---

## How job text is stored in `comment_text`

The value is a raw HTML string, not plain text. Key patterns:

- Paragraphs are separated by `<p>` tags (no closing `</p>`)
- Newlines (`\n`) appear within paragraphs for line breaks that don't open a new block
- Links use full anchor tags: `<a href="..." rel="nofollow">...</a>`
- Italic text uses `<i>...</i>`
- HTML entities appear for special chars: `&#x2F;` = `/`, `&#x27;` = `'`, `&amp;` = `&`
- No `<br>` tags observed; paragraph breaks are exclusively `<p>`

Example structure from fixture (hit index 1, Faqta job post):
```
"Company: Faqta\nLocation: Utrecht, Netherlands (Hybrid Tue/Thu)\n...<p>Medior Backend Developer (Node.js / TypeScript)<p>Faqta builds...<p>Tech stack:\nNode.js, TypeScript, Express\n...<p>More details and apply:\n<a href=\"...\">...</a>"
```

To extract plain text: strip HTML tags, decode entities, replace `<p>` with newlines.

---

## `parent_id` vs `story_id` — distinguishing top-level job posts from replies

This is the critical field for filtering:

| Condition | Meaning |
|---|---|
| `parent_id == story_id` | Top-level job post — direct reply to the thread root. This is a real job listing. |
| `parent_id != story_id` | Reply to another comment — a sub-thread conversation, not a job post. Filter these out. |

Concrete examples from fixture:

- **Hit 0** (`objectID: 47513830`): `parent_id=47333421`, `story_id=47219668` — these differ, so this is a reply to comment 47333421 (a conversation about a canceled interview). NOT a job post.
- **Hit 1** (`objectID: 47398997`): `parent_id=47219668`, `story_id=47219668` — these match, so this is a top-level job post. YES, parse this as a job listing.
- **Hit 2** (`objectID: 47395825`): `parent_id=47375985`, `story_id=47219668` — these differ, so this is a reply. NOT a job post.

Filter rule in code: `hit["parent_id"] == hit["story_id"]`

---

## Story-level fields (for thread discovery, not comment hits)

When searching for the thread itself via `search_by_date?tags=story,author_whoishiring`, story hits include additional fields not present on comments:

| Field | Notes |
|---|---|
| `title` | Thread title, e.g. "Ask HN: Who is hiring? (March 2026)" |
| `story_text` | Thread body HTML (the instructions post) |
| `children` | Array of all direct child comment IDs (can be 400+ entries) |
| `points` | Upvote count |
| `num_comments` | Total comment count including nested replies |

To get the latest thread: use `search_by_date` (not `search`) with `tags=story,author_whoishiring`. The first hit is the most recent.
