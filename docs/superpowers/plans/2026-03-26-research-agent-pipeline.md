# Research Agent Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 4-phase job research pipeline (scrape, filter, find contacts, generate pitch) orchestrated by a Claude Code lead agent that spawns specialized subagents.

**Architecture:** A lead agent runs as main thread via `claude --agent research-lead` and sequentially orchestrates 4 phases. Phases 1-2 run foreground (blocking). Phases 3-4 fan out N parallel background workers per top company. All subagents write verbose output to files and return only summaries. MCP servers (JobSpy, Exa) scoped inline per subagent.

**Tech Stack:** Claude Code subagents (markdown + YAML frontmatter), JobSpy MCP Server (python-jobspy), Exa MCP (people/company search), Claude in Chrome (browser automation), WebSearch/WebFetch (fallback).

**Spec:** `research-agent-plan.md` in project root.

---

### Task 1: Update settings.local.json and install dependencies

**Files:**
- Modify: `.claude/settings.local.json`

- [ ] **Step 1: Replace settings with pre-approved permissions**

Write to `.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Write",
      "Edit",
      "Glob",
      "Grep",
      "WebSearch",
      "WebFetch",
      "Bash(mkdir *)",
      "Bash(pip install *)",
      "Bash(python *)",
      "mcp__jobspy__*",
      "mcp__exa__*",
      "mcp__claude-in-chrome__*"
    ]
  }
}
```

- [ ] **Step 2: Verify JSON is valid**

```bash
python3 -c "import json; json.load(open('.claude/settings.local.json')); print('Valid JSON')"
```

Expected: `Valid JSON`

- [ ] **Step 3: Install python-jobspy and MCP server**

```bash
pip install python-jobspy
```

Then check if the MCP server module is available:

```bash
python -c "import jobspy; print('jobspy available')"
```

Expected: `jobspy available`

If `jobspy_mcp_server` is a separate package:

```bash
pip install jobspy-mcp-server 2>/dev/null || pip install git+https://github.com/chinpeerapat/jobspy-mcp-server.git
```

- [ ] **Step 4: Verify Exa and Chrome MCP are available**

Exa must be configured at session/user level so `contact-finder` can reference it by name. Check with:

```bash
claude mcp list 2>/dev/null || echo "Check MCP servers interactively with /mcp"
```

If Exa is not listed: `claude mcp add exa --scope user`

Chrome MCP auto-connects when the Chrome extension is active — no action needed.

- [ ] **Step 5: Commit**

```bash
git add .claude/settings.local.json
git commit -m "feat: configure permissions for research pipeline"
```

---

### Task 2: Create the job-scraper subagent

**Files:**
- Create: `.claude/agents/job-scraper.md`

- [ ] **Step 1: Create agents directory**

```bash
mkdir -p .claude/agents
```

- [ ] **Step 2: Write job-scraper agent definition**

Write to `.claude/agents/job-scraper.md`:

```markdown
---
name: job-scraper
description: Scrapes job postings from multiple job boards using JobSpy MCP and Chrome. Use for Phase 1 of the research pipeline to collect postings with salary data.
tools: Read, Write, Bash, WebSearch, WebFetch
model: sonnet
mcpServers:
  - jobspy:
      type: stdio
      command: python
      args: ["-m", "jobspy_mcp_server"]
  - claude-in-chrome
---

You are a job scraping specialist. Your job is to collect job postings with salary data from multiple boards.

## Your task

When invoked, you receive a list of search queries and target job boards. For each query:

1. Call `scrape_jobs_tool` with the query across all supported boards (indeed, linkedin, glassdoor, google, zip_recruiter)
2. Use parameters: `results_wanted: 50`, `hours_old: 720` (30 days), `is_remote: true`, `linkedin_fetch_description: true`
3. For boards JobSpy doesn't cover (Wellfound, RemoteOK), use Chrome to browse and extract postings
4. Write results directly to `research/phase-1-scrape/all-postings.md` — append as you go, do NOT accumulate in context

Before writing, run: `mkdir -p research/phase-1-scrape`

## Output format per posting (markdown key:value)

```
---
title: [Job Title]
company: [Company Name]
company_url: [URL]
location: [City, State or Remote]
is_remote: [true/false]
salary_min: [number or "unlisted"]
salary_max: [number or "unlisted"]
salary_currency: [USD/EUR/etc]
salary_interval: [yearly/monthly/hourly]
job_url: [URL to posting]
date_posted: [YYYY-MM-DD]
job_type: [fulltime/contract/parttime]
description_summary: [2-3 sentence summary of key requirements]
---
```

## After scraping all queries

1. Read `research/phase-1-scrape/all-postings.md`
2. Deduplicate by job_url and title+company combination
3. Rewrite the file with only unique postings

## What to return to the lead agent

Return ONLY a 1-2 sentence summary: total postings found, unique after dedup, boards scraped.
Example: "Found 312 postings across 5 boards + 2 Chrome sources, 247 unique after deduplication. Wrote to research/phase-1-scrape/all-postings.md"

NEVER return the full posting data in your response. It goes in the file.
```

- [ ] **Step 3: Verify frontmatter**

```bash
head -10 .claude/agents/job-scraper.md
```

Expected: YAML frontmatter with name, description, tools, model, mcpServers.

- [ ] **Step 4: Commit**

```bash
git add .claude/agents/job-scraper.md
git commit -m "feat: add job-scraper subagent for Phase 1"
```

---

### Task 3: Create the fit-scorer subagent

**Files:**
- Create: `.claude/agents/fit-scorer.md`

- [ ] **Step 1: Write fit-scorer agent definition**

Write to `.claude/agents/fit-scorer.md`:

```markdown
---
name: fit-scorer
description: Scores and ranks job postings against Diego's skills inventory. Use for Phase 2 of the research pipeline to filter best-fit opportunities.
tools: Read, Write, Grep, Glob
model: sonnet
---

You are a job fit analysis specialist. Your job is to score job postings against a candidate's skills and rank them.

## Your task

1. Read `skills-inventory.md` to understand Diego's complete skill set
2. Read `resume-diego-gomez-ops-ai.md` to understand his experience positioning
3. Read `research/phase-1-scrape/all-postings.md` to get all scraped postings

## Scoring dimensions (weighted)

For each posting, score 0-100 across these dimensions:

| Dimension | Weight | How to score |
|-----------|--------|-------------|
| Salary | 30% | 100 if >$150K, 80 if $120-150K, 60 if $90-120K, 40 if $60-90K, 20 if <$60K or unlisted |
| Skills match | 30% | % of required skills Diego has (match against skills-inventory.md categories) |
| Experience match | 20% | How well Diego's 2+ years ops + AI projects align with requirements |
| Growth potential | 10% | Does the role offer career growth, learning, interesting problems? |
| Remote/location fit | 10% | 100 if fully remote, 80 if hybrid-friendly, 40 if in-office US timezone, 0 if incompatible |

**Final score** = weighted sum. **Grade:** A (80-100), B (60-79), C (40-59), D (0-39).

## Output format

Run: `mkdir -p research/phase-2-rank`

Write to `research/phase-2-rank/ranked-opportunities.md`:

```
# Ranked Opportunities

Generated: [date]
Total scored: [N]
A-tier: [N] | B-tier: [N] | C-tier: [N] | D-tier: [N]

---

## A-Tier

### 1. [Role] at [Company] — Score: [N] | Salary: $[min]-[max]
- **Skills match (N/100):** [which skills match, which are gaps]
- **Experience match (N/100):** [alignment details]
- **Growth (N/100):** [reasoning]
- **Remote fit (N/100):** [reasoning]
- **Why pursue:** [1-2 sentences]
- **Job URL:** [link]

## B-Tier
[same format]

## C-Tier (one-line summaries only)
- [Role] at [Company] — Score: [N] — [reason for C]

## D-Tier (count only)
[N] postings scored below 40. Skipped.
```

## What to return to the lead agent

Return ONLY: count per tier and the names of A-tier + top B-tier companies.
Example: "Scored 247 postings: 5 A-tier, 8 B-tier, 34 C-tier, 200 D-tier. Top: Anthropic (95), Stripe (88), Vercel (84). Wrote to research/phase-2-rank/ranked-opportunities.md"

NEVER return full scoring details in your response. It goes in the file.
```

- [ ] **Step 2: Verify frontmatter has no mcpServers**

```bash
head -7 .claude/agents/fit-scorer.md
```

Expected: Frontmatter ends at `model: sonnet` — no mcpServers field.

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/fit-scorer.md
git commit -m "feat: add fit-scorer subagent for Phase 2"
```

---

### Task 4: Create the contact-finder subagent

**Files:**
- Create: `.claude/agents/contact-finder.md`

- [ ] **Step 1: Write contact-finder agent definition**

Write to `.claude/agents/contact-finder.md`:

```markdown
---
name: contact-finder
description: Finds hiring managers and team leads on LinkedIn and X for a specific company and role. Use for Phase 3 of the research pipeline.
tools: Read, Write, WebSearch, WebFetch
model: sonnet
mcpServers:
  - exa
  - claude-in-chrome
---

You are a contact research specialist. Your job is to find the right person to DM at a specific company for a specific role.

## Your task

You receive: a company name, role title, and job URL. Find the hiring manager, team lead, or recruiter.

## Search strategy (in order)

1. **Exa people search:** Search for "[Company] [Department] Manager OR Lead OR Director OR Head"
2. **LinkedIn via Chrome:** Browse company page > People tab > filter by relevant department
3. **X via Chrome:** Search "[Company] hiring" or browse company followers in relevant roles
4. **Company website:** Check /team, /about, /leadership pages via WebFetch

## Also gather company context

- Recent news (last 3 months) — product launches, funding, partnerships
- Company culture signals from careers page, blog, social media
- Tech stack from job postings or engineering blog
- Team size and growth trajectory

## Output format

Run: `mkdir -p research/phase-3-contacts/[company-slug]`

Write contact data to `research/phase-3-contacts/[company-slug]/contacts.md`:

```
# Contacts: [Company Name]

## Primary Contact
- Name: [Full Name]
- Title: [Job Title]
- LinkedIn: [URL]
- X: [@handle or "not found"]
- Recent activity:
  - [Date]: [Post/share summary — for conversation starters]
  - [Date]: [Post/share summary]
  - [Date]: [Post/share summary]
- Shared interests with Diego: [any overlap]
- Recommended channel: [LinkedIn DM / X DM / email]

## Alternative Contacts
- [Name] — [Title] — [LinkedIn URL]
- [Name] — [Title] — [LinkedIn URL]
```

Write company context to `research/phase-3-contacts/[company-slug]/company-context.md`:

```
# Company Context: [Company Name]

## Overview
[2-3 sentences about what they do]

## Recent News
- [Date]: [News item]
- [Date]: [News item]

## Culture Signals
[Key observations from careers page, blog, social media]

## Tech Stack
[Technologies mentioned in job postings or engineering blog]

## Team Size & Growth
[What you found about company size, hiring velocity]
```

## What to return to the lead agent

Return ONLY: primary contact name + title + recommended channel.
Example: "Found Jane Doe, VP Engineering at Acme Corp. Recommended: LinkedIn DM. Wrote to research/phase-3-contacts/acme-corp/"

NEVER return full contact profiles or company context in your response.
```

- [ ] **Step 2: Verify mcpServers references exa and chrome**

```bash
grep -A2 "mcpServers:" .claude/agents/contact-finder.md
```

Expected: `- exa` and `- claude-in-chrome`

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/contact-finder.md
git commit -m "feat: add contact-finder subagent for Phase 3"
```

---

### Task 5: Create the pitch-generator subagent

**Files:**
- Create: `.claude/agents/pitch-generator.md`

- [ ] **Step 1: Write pitch-generator agent definition**

Write to `.claude/agents/pitch-generator.md`:

```markdown
---
name: pitch-generator
description: Generates tailored video pitch scripts and DM drafts for a specific company and role. Use for Phase 4 of the research pipeline.
tools: Read, Write, Glob
model: opus
---

You are a personalized outreach specialist. Your job is to create authentic, tailored pitch materials for Diego's job applications.

## Your task

You receive: a company name, role title, and fit score. Use all available research to generate pitch materials.

## Inputs to read

1. `research/phase-2-rank/ranked-opportunities.md` — for the specific posting details and fit analysis
2. `research/phase-3-contacts/[company-slug]/contacts.md` — for target contact and conversation starters
3. `research/phase-3-contacts/[company-slug]/company-context.md` — for company-specific details
4. `resume-diego-gomez-ops-ai.md` — for positioning and evidence
5. `skills-inventory.md` — for specific technical evidence
6. `vocaroo-script.md` — for voice and tone reference

## Voice guidelines

- Sound like Diego, not a bot — conversational, direct, confident without being arrogant
- Reference SPECIFIC projects with REAL numbers (limit-break-amm: 14K lines, autoresearch-trading: 40GB/day)
- Show you understand THEIR problem, not just your own skills
- Keep it short — respect their time

## Output: Video Script

Run: `mkdir -p research/phase-4-pitch/[company-slug]`

Write to `research/phase-4-pitch/[company-slug]/video-script.md`:

A 30-40 second script (roughly 80-100 words) with three sections:

```
# Video Pitch: [Role] at [Company]

## Opening (5 sec)
"Hey [Contact first name], I'm Diego — [one-line hook referencing their company]"

## Value Prop (15-20 sec)
[Map Diego's specific experience to their specific need. Name the project, the numbers.]

## Close (10 sec)
"I'd love to chat about how I can help [specific thing].
My resume's linked below — happy to jump on a quick call."
```

## Output: DM Draft

Write to `research/phase-4-pitch/[company-slug]/dm-draft.md`:

A short DM (under 100 words):

```
# DM to [Contact Name] — [Platform]

Hey [Name],

[1 sentence referencing their recent post/company news — shows you did homework]

I saw the [Role] opening and it lines up with what I've been building —
[1 specific example mapped to their need].

I recorded a quick intro: [video link]
Resume: [link]

Would love to connect if you're open to it.

— Diego
```

## Output: Status Tracker

Write to `research/phase-4-pitch/[company-slug]/status.md`:

```
# Outreach Status: [Company] — [Role]

- Status: drafted
- Contact: [Name] via [Platform]
- Video: [ ] recorded
- DM: [ ] sent
- Response: [ ] pending
- Follow-up date: [1 week from today]
```

## What to return to the lead agent

Return ONLY: confirmation that materials were generated.
Example: "Generated video script (95 words) + DM draft + status tracker for Acme Corp. Wrote to research/phase-4-pitch/acme-corp/"

NEVER return the full script or DM in your response.
```

- [ ] **Step 2: Verify frontmatter has no mcpServers**

```bash
head -7 .claude/agents/pitch-generator.md
```

Expected: Frontmatter ends at `model: opus` — no mcpServers field.

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/pitch-generator.md
git commit -m "feat: add pitch-generator subagent for Phase 4"
```

---

### Task 6: Create the research-lead agent

**Files:**
- Create: `.claude/agents/research-lead.md`

- [ ] **Step 1: Write research-lead agent definition**

Write to `.claude/agents/research-lead.md`:

```markdown
---
name: research-lead
description: Orchestrates the 4-phase job research pipeline. Run as main thread with claude --agent research-lead.
tools: Agent(job-scraper, fit-scorer, contact-finder, pitch-generator), Read, Write, Glob, Grep
model: opus
initialPrompt: "Read skills-inventory.md and resume-diego-gomez-ops-ai.md, then ask what search queries and job boards to target."
---

You are the research pipeline orchestrator. You run 4 phases sequentially, spawning specialized subagents for each.

## CRITICAL CONSTRAINTS

1. **You are the main thread.** Only YOU can spawn subagents. Subagents cannot spawn other subagents.
2. **Subagents return summaries only.** All verbose data goes to files. You read files for details, not subagent responses.
3. **Phases 1-2 run foreground** (blocking). Phases 3-4 run background (parallel per company).
4. **Never accumulate raw posting data in your context.** Read from files when needed.

## Phase 1: Scrape

Spawn `job-scraper` in **foreground** with:
- The list of search queries (confirm with user or use defaults below)
- Target boards: indeed, linkedin, glassdoor, google, zip_recruiter + Chrome for wellfound, remoteok

Wait for completion. Read the summary (posting count, board breakdown).

## Phase 2: Filter & Rank

Spawn `fit-scorer` in **foreground** with:
- Instruction to read `research/phase-1-scrape/all-postings.md`
- Instruction to score against `skills-inventory.md`

Wait for completion. Read the summary (tier counts, top company names).
Then read `research/phase-2-rank/ranked-opportunities.md` to extract the A-tier + top B-tier company list.

## Phase 3: Find Contacts

For EACH top company (A-tier + top B-tier), spawn a `contact-finder` in **background** with:
- Company name
- Role title
- Job URL

Spawn all in parallel. Wait for all to complete.

## Phase 4: Generate Pitches

For EACH top company, spawn a `pitch-generator` in **background** with:
- Company name
- Role title
- Fit score

Spawn all in parallel. Wait for all to complete.

## Phase 5: Summary

After all phases complete, write `research/pipeline-summary.md` with:
- Date run
- Total postings scraped
- Tier breakdown
- Per-company summary: role, score, contact found, materials generated
- Links to all output files

Then present the summary to the user.

## Default search queries

If the user doesn't specify, use these:
1. "Operations Manager AI"
2. "AI Operations Lead"
3. "Business Operations AI Integration"
4. "AI Process Automation Manager"
5. "Technical Operations Manager"
6. "AI Agent Developer"
7. "Developer Relations"
```

- [ ] **Step 2: Verify agent can spawn the right subagents**

```bash
grep "^tools:" .claude/agents/research-lead.md
```

Expected: `tools: Agent(job-scraper, fit-scorer, contact-finder, pitch-generator), Read, Write, Glob, Grep`

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/research-lead.md
git commit -m "feat: add research-lead orchestrator agent"
```

---

### Task 7: Create CLAUDE.md project instructions

**Files:**
- Create: `.claude/CLAUDE.md`

- [ ] **Step 1: Write project CLAUDE.md**

Write to `.claude/CLAUDE.md`:

```markdown
# HireBoost Research Pipeline

## What this project is

A 4-phase job research pipeline that scrapes job postings, scores them against Diego's skills, finds hiring managers, and generates personalized pitch materials. Anti-mass-apply: quality over quantity.

## Running the pipeline

```
claude --agent research-lead
```

## Directory conventions

- `research/phase-1-scrape/` — Scraped postings (created at runtime)
- `research/phase-2-rank/` — Scored and tiered opportunities
- `research/phase-3-contacts/[company-slug]/` — Contact profiles + company context
- `research/phase-4-pitch/[company-slug]/` — Video scripts + DM drafts + outreach status

## Key input files

- `skills-inventory.md` — Diego's complete skills inventory (input to Phase 2)
- `resume-diego-gomez-ops-ai.md` — Tailored resume (input to Phase 4)
- `vocaroo-script.md` — Voice/tone reference for pitch scripts

## Subagent output contract

ALL subagents MUST:
1. Write verbose output to `research/` files
2. Return ONLY 1-2 sentence summaries to the lead agent
3. NEVER return raw data in responses

## Forbidden patterns

- Never mass-apply or auto-submit applications
- Never send DMs automatically (human-in-the-loop always)
- Never fabricate skills or experience in pitch materials
- Never accumulate large data in agent context (write to files)
```

- [ ] **Step 2: Verify file**

```bash
head -3 .claude/CLAUDE.md
```

Expected: `# HireBoost Research Pipeline`

- [ ] **Step 3: Commit**

```bash
git add .claude/CLAUDE.md
git commit -m "feat: add CLAUDE.md project instructions"
```

---

### Task 8: Validate and smoke test

**Files:**
- No files created (validation only)

- [ ] **Step 1: Verify all agent files exist and parse**

```bash
for f in .claude/agents/*.md; do echo "=== $(basename $f) ==="; head -3 "$f"; echo; done
```

Expected: 5 files (contact-finder.md, fit-scorer.md, job-scraper.md, pitch-generator.md, research-lead.md), each starting with `---` and `name:`.

- [ ] **Step 2: Cross-check agent tool access and MCP scoping**

```bash
for f in .claude/agents/*.md; do echo "=== $(basename $f) ==="; grep -E "^(tools|model|mcpServers):" "$f" || echo "(no match)"; echo; done
```

Expected:
| Agent | tools | model | mcpServers |
|-------|-------|-------|------------|
| job-scraper | Read, Write, Bash, WebSearch, WebFetch | sonnet | jobspy (inline) + chrome |
| fit-scorer | Read, Write, Grep, Glob | sonnet | (none) |
| contact-finder | Read, Write, WebSearch, WebFetch | sonnet | exa + chrome |
| pitch-generator | Read, Write, Glob | opus | (none) |
| research-lead | Agent(...), Read, Write, Glob, Grep | opus | (none) |

- [ ] **Step 3: Verify data handoff paths are consistent**

```bash
grep -n "all-postings.md\|ranked-opportunities.md\|phase-3-contacts\|phase-4-pitch" .claude/agents/*.md
```

Check:
- job-scraper writes `research/phase-1-scrape/all-postings.md`
- fit-scorer reads `research/phase-1-scrape/all-postings.md` (match)
- fit-scorer writes `research/phase-2-rank/ranked-opportunities.md`
- lead reads `research/phase-2-rank/ranked-opportunities.md` to extract top companies (match)
- contact-finder writes `research/phase-3-contacts/[company-slug]/`
- pitch-generator reads `research/phase-3-contacts/[company-slug]/` (match)

- [ ] **Step 4: Test launching research-lead**

```bash
echo "List your 4 worker subagents and confirm you can read skills-inventory.md" | claude --agent research-lead --max-turns 3 2>&1 | head -20
```

Expected: Mentions job-scraper, fit-scorer, contact-finder, pitch-generator. Confirms skills-inventory.md is readable.

- [ ] **Step 5: Commit any fixes**

```bash
git diff --stat
```

If changes were needed:

```bash
git add .claude/
git commit -m "fix: correct agent definitions after validation"
```

---

## Post-Implementation

Run the pipeline:

```bash
claude --agent research-lead
```

The lead agent will:
1. Ask to confirm search queries
2. Scrape all boards (Phase 1)
3. Score and rank (Phase 2)
4. Find contacts for top companies (Phase 3, parallel)
5. Generate pitch materials (Phase 4, parallel)
6. Present summary

Diego reviews, edits for authenticity, records videos, sends DMs personally.
