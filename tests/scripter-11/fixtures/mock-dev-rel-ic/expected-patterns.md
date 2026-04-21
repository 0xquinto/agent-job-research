# Expected Patterns — mock-dev-rel-ic fixture

Archetype under test: IC / conversational / dev-community. Ali Abdaal + Patrick McKenzie advisors should fire hardest.

## video-script.md

### Length (spoken body only)
- Spoken-body word count (Hook + Proof + Ask) in `[150, 220]`. Exclude metadata and the Intentionally Ignored section.
- Verify with:
  ```bash
  sed -n '/^## Hook/,/^---$/p' tests/scripter-11/fixtures/mock-dev-rel-ic/phase-4-pitch/dev-rel-ic/video-script.md \
    | grep -vE '^##|^---$|^\*\*|^$' \
    | wc -w
  ```

### Required conversational markers
At least ONE of these must appear in Hook or Ask:
- A contraction (`I'm`, `you're`, `it's`, `let's`, `we're`, `don't`, `can't`)
- A conversational beat (`look`, `here's the thing`, `so`, `honestly`)

Grep check:
```bash
grep -cE "I'm|you're|it's|let's|we're|don't|can't|look,|here's the thing|^so |honestly" .../video-script.md
```
Expected: count ≥ 1.

### Forbidden formal register
Must NOT contain:
- `I would welcome the opportunity`
- `please do not hesitate`
- `I am writing to`
- `dear`

### Forbidden corporate vocabulary
Same list as fixture 1: `leveraged`, `streamlined`, `passionate about`, `synergy`.

### Structural shape
- Contains `## Hook (~10 sec)`, `## Proof (~40-60 sec)`, `## Ask (~10 sec)`
- Contains `## Intentionally Ignored Critiques`

## video-script-critiques.md

- 8 advisor headings present
- Ali Abdaal section should have ≥ 1 critique OR explicit NO ISSUE
- Patrick McKenzie section should have ≥ 1 critique OR explicit NO ISSUE
