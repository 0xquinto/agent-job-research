# Contacts — Anthropic AI Security Fellows

Research date: 2026-04-21

## Primary Contact

- **Name:** Nicholas Carlini
- **First name:** Nicholas
- **Title:** Research Scientist, Anthropic (AI security; adversarial ML)
- **Email:** nicholas@carlini.com (published on his personal site)
- **GitHub:** @carlini
- **LinkedIn:** not present — he has explicitly said he is not on LinkedIn
- **X:** @nicholas_carlini (low-activity; email is the preferred channel)

## Why he matters

Carlini is the researcher whose [un]prompted talk ("Black-hat LLMs") directly names the validation bottleneck that the AI Security Fellows workstream is designed to address. His line — "several hundred crashes I haven't had time to validate" — is the precise problem statement. He is not the formal hiring manager for Constellation applications, but he is the domain authority whose framing defines the workstream. A direct email to Carlini, sent after the official Constellation application is submitted, is the standout supplement strategy.

## Conversation starter

His [un]prompted talk (April 2026, "Black-hat LLMs") named two concrete artifacts he found:
- Ghost CMS blind SQL injection (full credential leak)
- Linux Kernel NFSv4 heap buffer overflow (predates Git, 2003)

The method: Claude Code with `--dangerously-skip-permissions` in a VM, CTF framing, one-line "hint, look at this file" trick. His bottleneck framing: the discovery works; triage and validation don't scale.

Diego's compliance-theater paper is a formal answer to the validation-layer failure he described: LLM agents systematically self-report completing checklists they did not execute. The paper names the pattern, provides a 16-dimension trace analyzer, and publishes a formal refutation predicate (MAST FM-3.2).

## Relationship notes

Cold. He reads email if it's specific and short. Published address is `nicholas@carlini.com`. He explicitly does not want generic outreach — his talks signal that he values empirical rigor, self-criticism, and breaking your own tools in public. The compliance-theater paper does all three.

**Recommended channel:** Email only. Not LinkedIn, not X. Lead with the video (50 seconds), follow with the paper link.

**Timing constraint:** Send AFTER the official Constellation application is submitted via the Constellation portal. The video is a supplement, not a substitute.

## Secondary Contact

- **Name:** Constellation Program Office**
- **Channel:** https://www.constellation.org/programs/ai-safety-fellows (official application portal)
- **Notes:** Formal application goes here first. Carlini email is the parallel standout move, not the primary submission path.
