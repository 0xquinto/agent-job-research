---
name: pitch-council
description: Use when critiquing or drafting short-form 1:1 cold-pitch content — video scripts, outreach DMs, cover letters — where hook strength, medium-fit, authenticity, and ruthless cutting matter. Provides an 8-advisor critique framework covering tactical empathy, pitch frames, cold outreach, engineer sensibility, hiring-manager POV, hook mechanics, IC-to-IC warmth, and positioning.
---

# Pitch Council

## Overview

An 8-advisor critique framework for short-form 1:1 cold-pitch content. Each advisor catches one specific failure mode. Critiques follow a fixed format: quote the offending line verbatim, state the fix.

Use when a draft exists and you want multi-lens critique before shipping. The council is not a replacement for the writer's voice — advisors propose; the writer disposes. Any critique that would damage authentic voice must be listed as "Intentionally Ignored" with a rationale.

## Quick reference

| Advisor | Catches | Red-flag phrases |
|---|---|---|
| Chris Voss | Self-centered openings, missing labels | "I'm excited / I want / I think" |
| Oren Klaff | Information-dumping, chaser frame | Multi-clause credentials before the prize |
| Josh Braun | Pressure asks, problem-last order | "Quick call?", "15 min of your time" |
| Patrick McKenzie | Corporate vocabulary, unquantified claims | "leveraged / streamlined / passionate" |
| Gergely Orosz | Generic praise, no role-fit proof | "Love what you're doing at X" |
| Mr. Beast | Weak first 3 seconds, no pattern interrupt | "Hey, I'm Diego and I want..." |
| Ali Abdaal | Formal register, transactional tone | No contractions, no conversational beats |
| Seth Godin | Multiple promises, vague positioning | Lists of 3+ value props, "helping teams to..." |

## Advisor principles

### Chris Voss — tactical empathy

Openers should make the reader feel understood, not pitched at. Labels ("It seems like X is the real problem") outperform statements ("I can solve X"). "No"-bait questions ("Would it be ridiculous to...") open more doors than "yes"-asks.

Failure modes: "I'm excited" openers, missing labels, pitching before listening.

Sample critique:
```
- v1 line: "I built something analogous and want to take it further."
  Fix: starts with you. Try a label: "Your page frames this as a research frontier, not a hiring problem — is that the real ask?"
```

### Oren Klaff — pitch frames

Prize-frame rule: the listener should feel evaluated, not sold to. Intrigue ("there's a thing I can't unsee") beats information dumps. Hot cognition, not cold logic.

Failure modes: chaser frame (eager, explaining), info-dumping credentials early, no intrigue hook.

Sample critique:
```
- v1 line: "Over 17 experiments, quality went from 39.8 to 112.5."
  Fix: cold info. Try intrigue: "I ran this as a real experiment — 17 iterations later, one surprising thing stuck. Want to see it?"
```

### Josh Braun — cold outreach

Problem-first, offer-second. Never ask for time. Never say "quick call". Offer value before asking for anything.

Failure modes: "quick call?" CTAs, problem-last ordering, any pressure language.

Sample critique:
```
- v1 line: "happy to jump on a quick call."
  Fix: pressure language. Try: "If this resonates, I've got a 3-minute Loom on the approach."
```

### Patrick McKenzie — engineer sensibility

Specificity beats polish. Real numbers beat adjectives. An engineer's BS detector fires on the first corporate word. Strip adjectives; keep nouns and numbers.

Failure modes: "leveraged / streamlined / passionate about", unquantified claims, polished-empty sentences.

Sample critique:
```
- v1 line: "passionate about building agent systems."
  Fix: "passionate" loses the reader. Try: "I've shipped three agent systems; the last one ran in prod for 4 months at [company]."
```

### Gergely Orosz — hiring-manager POV

Hiring managers read inbound pitches with one question: "Can this person do the job tomorrow?" Praise the company = skip signal. Proof-of-role-fit = continue signal.

Failure modes: generic company praise, no proof of the role's actual day-to-day, volume-signal phrasing.

Sample critique:
```
- v1 line: "love what you're doing at Anthropic."
  Fix: skip signal. Replace with a specific artifact: "I reproduced your published MCP server and extended it with [specific thing]."
```

### Mr. Beast — hook mechanics

First 3 seconds decide the next 27. Pattern interrupt beats introduction. Earn the next sentence with the one before it.

Failure modes: "Hey, I'm X" openers, no pattern interrupt, a promise the rest doesn't pay off.

Sample critique:
```
- v1 opener: "Hey Nicholas, I'm Diego — I want to take it further."
  Fix: weak opener. Try: "Your fellowship page cites a $4.6M AI-security finding. I replicated the structure of that exact win. Here's how."
```

### Ali Abdaal — IC-to-IC warmth

Two engineers at a coffee shop, not a vendor pitching a buyer. Contractions. Asides. The occasional "here's the thing" or "look". You're talking with, not at.

Failure modes: formal register, no contractions, transactional CTAs, zero conversational beats.

Sample critique:
```
- v1 line: "I would welcome the opportunity to discuss this further."
  Fix: formal, transactional. Try: "happy to jam on this if you're up for it."
```

### Seth Godin — positioning

One promise. One idea. One person. A pitch that tries to serve three personas serves none.

Failure modes: multi-promise pitches, vague "helping teams to...", list-of-three value props.

Sample critique:
```
- v1 line: "research + engineering + operations experience."
  Fix: three promises = zero. Pick the one that matters for this specific role; cut the other two.
```

## Critique output template

For each advisor, produce 0-4 bullets in this exact shape:

```markdown
### {Advisor name} — {domain}
- v1 line: "{exact quote from draft}"
  Fix: {what to try instead — one sentence}
```

If an advisor has no issue with the draft, write:

```markdown
### {Advisor name} — {domain}
- NO ISSUE
```

Never manufacture critiques to fill a quota. An advisor with nothing to say is a signal, not a failure.

## Common mistakes when using this council

- **Applying all 8 critiques mechanically.** The voice-anchor always wins. If a critique would make the draft sound less like the writer, list it as "Intentionally Ignored" with a one-line rationale.
- **Writing critiques in the advisor's voice.** Quote the original line; state the fix directly. Don't ventriloquize.
- **Skipping NO ISSUE.** An advisor with no critique is valuable signal. Say so explicitly.
- **Over-polishing until the draft sounds like no one.** If every advisor approves and the script sounds AI-written, the voice-anchor was ignored — restart from v1.
