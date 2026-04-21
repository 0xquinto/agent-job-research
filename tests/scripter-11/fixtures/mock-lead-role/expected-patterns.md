# Expected Patterns — mock-lead-role fixture

Archetype under test: seniority-signal / positioning / one-confident-opinion. Seth Godin + Gergely Orosz advisors should fire hardest.

## video-script.md

### Length (spoken body only)
- Spoken-body word count (Hook + Proof + Ask) in `[150, 220]`. Exclude metadata and the Intentionally Ignored section.
- Verify with:
  ```bash
  sed -n '/^## Hook/,/^---$/p' tests/scripter-11/fixtures/mock-lead-role/phase-4-pitch/ai-platform-lead/video-script.md \
    | grep -vE '^##|^---$|^\*\*|^$' \
    | wc -w
  ```

### Single-promise constraint
Proof section must contain exactly ONE named project or platform-shipped artifact. Multi-promise scripts (two or three comma-separated capabilities) must be flagged by Seth Godin in critiques and trimmed in v2.

Manual grep check (the engineer reviews):
```bash
sed -n '/^## Proof/,/^## Ask/p' .../video-script.md
```
Review: is there one project named, or multiple? Fail if multiple.

### Required opinion signal
Hook or Proof must contain one of these phrases (or a close paraphrase demonstrating an opinion, not a capability list):
- `the real problem is`
- `the wrong question is`
- `the thing I'd do first`
- `here's where I'd bet`
- `I'd stop prototyping and`

The Morgan-Chen conversation starter explicitly rewards an opinion. An opinion-less script fails the hiring-manager POV test.

### Forbidden phrases
- `I'm excited about your company`  (Morgan's explicit trigger)
- `passionate about`
- `leveraged`
- `multiple years of experience`

### Structural shape
- Contains `## Hook`, `## Proof`, `## Ask`, `## Intentionally Ignored Critiques`

## video-script-critiques.md

- 8 advisor headings present
- Gergely Orosz section: critique fires on any company-praise language
- Seth Godin section: fires if multi-promise
