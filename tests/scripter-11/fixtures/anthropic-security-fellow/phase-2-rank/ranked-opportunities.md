# Ranked Opportunities — anthropic-security-fellow fixture

Generated: 2026-04-21
Run: 2026-04-21-anthropic-fellows-security
Target: AI Security Fellows (Constellation / Anthropic)

---

## A-tier

### Anthropic — AI Security Fellows (Constellation Program)

- **Company slug:** ai-security-fellow
- **Role title:** AI Security Fellow — Validation & Triage Workstream
- **Fit score:** A (92)
- **URL:** https://www.constellation.org/programs/ai-safety-fellows
- **Archetype:** Fellowship / research-frontier / empirical-security

**JD summary:** Four-month funded fellowship for technical AI safety work embedded with a frontier lab. Anthropic's track specifically targets candidates who can close the gap between LLM-assisted vulnerability discovery and validated, actionable findings. The bottleneck is triage and validation — not discovery. Fellows work on problems named by the lab's researchers, not on open-ended independent projects.

**Stated needs:**
- Deep hands-on experience with LLM-assisted security workflows (Claude Code in particular)
- Ability to evaluate model-generated findings: replicate, confirm, or formally refute
- Published work that demonstrates rigorous methodology under adversarial conditions
- Comfort operating at the intersection of formal verification and empirical security research
- Willingness to own the validation bottleneck — the part that is less glamorous than finding 0-days

**Fit analysis:** Diego's 9-agent audit harness (Limit Break AMM, 369 commits, 283 tests, 24 experiment runs) maps directly to the validation workstream. Published compliance-theater paper formalizes a failure mode (LLM agents self-reporting completed checklists they did not execute) and provides a refutation predicate — the exact methodology the validation bottleneck demands. VLIW kernel benchmark (114.97× improvement, outperforming all listed Claude results) demonstrates ability to push Claude tooling past published limits. Archetype signal: research-frontier; must demonstrate a single defensible empirical claim, not a portfolio of capabilities.

**Conversation anchor:** Nicholas Carlini's [un]prompted talk explicitly names "several hundred crashes I haven't had time to validate" as the bottleneck. The compliance-theater paper is a direct formal answer to that problem statement.
