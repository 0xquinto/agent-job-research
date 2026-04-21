# scripter-11 regression fixtures

Three fixtures exercise the scripter-11 agent against distinct role archetypes. They lock the agent's output shape when the agent or the `pitch-council` skill is edited.

## Fixtures

| Fixture | Archetype under test | Advisors exercised most |
|---|---|---|
| `anthropic-security-fellow` | Fellowship / research frontier | All 8 (real production case) |
| `mock-dev-rel-ic` | IC / conversational / dev-community | Ali Abdaal, Patrick McKenzie |
| `mock-lead-role` | Lead / seniority / single-opinion | Seth Godin, Gergely Orosz |

## Running a fixture

In an interactive Claude Code session, spawn scripter-11 via the Task tool:

```
RUN_DIR: tests/scripter-11/fixtures/<fixture-name>
Company: <company-name>
Role: <role-title>
Role slug: <role-slug>
Fit score: <score>

All output MUST be written under RUN_DIR.
```

Outputs land at `tests/scripter-11/fixtures/<fixture-name>/phase-4-pitch/<role-slug>/` and are gitignored.

## Verifying a run

Each fixture has an `expected-patterns.md` file listing automated grep assertions plus manual review criteria. Read it before running and verify each assertion after.

If a fixture fails: fix the agent or skill. Do not weaken the assertion.

## Adding a new fixture

1. Identify an archetype gap — what role shape is not covered above?
2. Create `tests/scripter-11/fixtures/<name>/phase-2-rank/ranked-opportunities.md` with one synthetic posting
3. Create `tests/scripter-11/fixtures/<name>/phase-3-contacts/<slug>/contacts.md` and `.../company-context.md`
4. Create `tests/scripter-11/fixtures/<name>/expected-patterns.md` with at least: length, forbidden-phrases, advisor-headings assertions
5. Run the fixture and iterate until assertions pass
6. Commit the fixture (outputs are gitignored)
