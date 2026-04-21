# Company Context — Anthropic / AI Security Fellows

## What Anthropic is doing in security

Anthropic's security research track (Carlini's team) has publicly demonstrated LLM-assisted 0-day discovery on production software:
- Ghost CMS blind SQL injection
- Linux Kernel NFSv4 heap buffer overflow (bug predates Git, 2003)

Method: Claude Code + `--dangerously-skip-permissions`, CTF framing, one-line "look at this file" hint for thoroughness. The discovery layer works. The bottleneck is triage: "several hundred crashes I haven't had time to validate" (Carlini, [un]prompted, April 2026).

## The AI Security Fellows program

- **Operator:** Constellation (AI safety fellowship organization)
- **Duration:** 4 months
- **Structure:** Fellows are embedded with a frontier lab working on named problems
- **Anthropic workstream framing:** Validation layer — between "the model flags a potential bug" and "a confirmed, patched, reported finding"
- **Application path:** Constellation portal → July 2026 cohort
- **Carlini's explicit CTA from the talk:** "help us make the future go well... doesn't matter where, just please help... order of months"

## Recent signal

- **[un]prompted talk (April 2026):** Carlini's Black-hat LLMs talk, delivered at The AI Practitioner Conference. 25-minute session + Q&A. The validation-bottleneck framing is the most actionable sentence in the talk for Fellows applicants.
- **Exponential capability framing:** METR benchmark doubling time ~4 months. Carlini cites Winnie & Cole MATS paper — the $4.6M smart-contract finding — as the current frontier.
- **Transitionary-period thesis:** Defenders win in the long run, but the gap window (now) is where harm concentrates. The Fellows program is the near-term response.

## Domain context

The Anthropic security research team operates at the intersection of:
- Adversarial ML (Carlini's primary track: extraction attacks, membership inference, adversarial examples)
- Autonomous LLM exploitation (the new track: Claude Code as an autonomous pentester)
- Formal methods adjacent (the validation layer: what does it mean to confirm a finding rigorously?)

Fellows are expected to work on whatever the triage bottleneck looks like when they arrive. The domain is nascent — there is no established methodology for LLM-assisted vulnerability validation at scale. That ambiguity is the opportunity.

## What this role is NOT

- Not a red-team role (no adversarial attacks on Anthropic's own models)
- Not a CVE track (1 Medium finding is not a pentester credential)
- Not independent research — Fellows work on Anthropic's named problems, not their own agenda
