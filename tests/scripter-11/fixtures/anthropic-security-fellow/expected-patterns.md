# Expected Patterns — anthropic-security-fellow fixture

After running scripter-11 against this fixture, verify the following.

## video-script.md (v2 — deliverable)

### Length (spoken body only)
- Word count of the SPOKEN body (Hook + Proof + Ask, excluding metadata and the Intentionally Ignored section) must be in `[150, 220]` inclusive.
- The spoken body is the content between `## Hook` and the `---` separator that precedes `## Intentionally Ignored Critiques`.
- Verify with:
  ```bash
  sed -n '/^## Hook/,/^---$/p' tests/scripter-11/fixtures/anthropic-security-fellow/phase-4-pitch/ai-security-fellow/video-script.md \
    | grep -vE '^##|^---$|^\*\*|^$' \
    | wc -w
  ```
- A naive `wc -w` on the full file WILL exceed 220 because of headings, the `**Target length:**` line, and the Intentionally Ignored block. Those are not spoken content.

### Forbidden opener phrases
The Hook section must NOT start with any of:
- `I'm excited`
- `I saw your`
- `I want to`
- `Hi, I'm` or `Hey, I'm` as the literal first phrase
- `My name is`

Grep check:
```bash
grep -E "^## Hook" -A 2 .../video-script.md | grep -iE "I'm excited|I saw your|I want to|^Hi, I'm|^Hey, I'm|My name is"
```
Expected: empty output (no match).

### Forbidden corporate vocabulary
v2 must NOT contain any of (case-insensitive):
- `leveraged`
- `streamlined`
- `passionate about`
- `synergy`

These are the red-flag phrases from voice-sample.md. The agent should never emit them.

### Required structural shape
- Contains `## Hook (~10 sec)` heading
- Contains `## Proof (~40-60 sec)` heading
- Contains `## Ask (~10 sec)` heading
- Contains `## Intentionally Ignored Critiques` section (with at least "None — all critiques applied." or a list)

### Required domain signal
- Contains the exact project name `limit-break-amm` OR a specific Anthropic-published artifact reference (e.g. `Mythos`, `MCP server`, `Security Fellows`) — proves the proof-point made it through the critique round.

## video-script-critiques.md

### Required advisor headings
File must contain all 8 advisor section headings (exact text, case-sensitive):
- `### Chris Voss`
- `### Oren Klaff`
- `### Josh Braun`
- `### Patrick McKenzie`
- `### Gergely Orosz`
- `### Mr. Beast`
- `### Ali Abdaal`
- `### Seth Godin`

Grep check:
```bash
for advisor in "Chris Voss" "Oren Klaff" "Josh Braun" "Patrick McKenzie" "Gergely Orosz" "Mr. Beast" "Ali Abdaal" "Seth Godin"; do
  grep -q "^### $advisor" .../video-script-critiques.md || echo "MISSING: $advisor"
done
```
Expected: empty output (no MISSING entries).

### Quote-and-fix format
For each advisor that has critiques (not "NO ISSUE"), at least one bullet must contain both the string `v1 line:` and `Fix:`.

### NO ISSUE allowance
"NO ISSUE" as the only bullet under an advisor is valid and expected for 0-3 advisors.

## video-script-v1.md

- File exists
- Has the same section headings as v2 but without the "Intentionally Ignored" block
- Spoken-body word count also in `[150, 220]`, measured with:
  ```bash
  sed -n '/^## Hook/,$p' tests/scripter-11/fixtures/anthropic-security-fellow/phase-4-pitch/ai-security-fellow/video-script-v1.md \
    | grep -vE '^##|^\*\*|^$' \
    | wc -w
  ```

## Baseline comparison

The baseline output for this role from `composer-4` (pre-split) is preserved at
`research/runs/2026-04-21-anthropic-fellows-security/phase-4-pitch/anthropic/video-script.md`.

Manual review criterion: v2 must score better than baseline on ranked problems B (voice drift) and D (over-packed evidence). This is a judgment call — the automated assertions above catch mechanical failures only.
