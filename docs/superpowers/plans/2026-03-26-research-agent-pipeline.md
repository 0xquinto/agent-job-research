# Research Agent Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 4-phase job research pipeline (scrape, filter, find contacts, generate pitch) orchestrated by a Claude Code lead agent that spawns specialized subagents.

**Architecture:** A lead agent runs as main thread via `claude --agent lead-0` and sequentially orchestrates 4 phases. Phases 1-2 run foreground (blocking). Phases 3-4 fan out N parallel background workers per top company. All subagents write verbose output to files and return only summaries. MCP servers configured at project level; subagents access them via tools field inheritance.

**Tech Stack:** Claude Code subagents (markdown + YAML frontmatter), JobSpy MCP Server (python-jobspy), Exa MCP (people/company search), Claude in Chrome (browser automation), WebSearch/WebFetch (fallback).

**Spec:** `research-agent-plan.md` in project root.

**Agent naming convention:** Non-descriptive names to prevent Claude from inferring default behaviors that override custom prompts ([source](https://codewithseb.com/blog/claude-code-sub-agents-multi-agent-systems-guide)).

| Phase | Agent Name | Role |
|-------|-----------|------|
| Orchestrator | `lead-0` | Pipeline orchestrator |
| Phase 1: Scrape | `scout-1` | Job board scraping |
| Phase 2: Filter | `ranker-7` | Fit scoring + ranking |
| Phase 3: Find | `recon-3` | Contact research |
| Phase 4: Pitch | `composer-4` | Pitch material generation |

---

### Task 1: Configure MCP servers and install dependencies

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

```bash
python -c "import jobspy; print('jobspy available')"
```

Expected: `jobspy available`

If `jobspy_mcp_server` is a separate package:

```bash
pip install jobspy-mcp-server 2>/dev/null || pip install git+https://github.com/chinpeerapat/jobspy-mcp-server.git
```

- [ ] **Step 4: Add JobSpy MCP server at project scope**

```bash
claude mcp add jobspy --scope project -- python -m jobspy_mcp_server
```

This registers JobSpy so subagents can access its tools via the `tools` field.

- [ ] **Step 5: Verify Exa MCP is configured**

```bash
claude mcp list 2>/dev/null || echo "Check MCP servers interactively with /mcp"
```

If Exa is not listed:

```bash
claude mcp add exa --scope user
```

Chrome MCP auto-connects when the Chrome extension is active — no action needed.

- [ ] **Step 6: Commit**

```bash
git add .claude/settings.local.json
git commit -m "feat: configure permissions and MCP servers for research pipeline"
```

---

### Task 2: Create scout-1 (Phase 1: job scraper)

**Files:**
- Create: `.claude/agents/scout-1.md`

- [ ] **Step 1: Create agents directory**

```bash
mkdir -p .claude/agents
```

- [ ] **Step 2: Write scout-1 agent definition**

Write to `.claude/agents/scout-1.md`:

```markdown
---
name: scout-1
description: Scrapes job postings with salary data from multiple boards using JobSpy MCP and Chrome. Use for Phase 1 of the research pipeline.
tools: Read, Write, Bash, WebSearch, WebFetch, mcp__jobspy__scrape_jobs_tool, mcp__jobspy__get_supported_sites, mcp__jobspy__get_supported_countries, mcp__jobspy__get_job_search_tips, mcp__claude-in-chrome__navigate, mcp__claude-in-chrome__get_page_text, mcp__claude-in-chrome__read_page, mcp__claude-in-chrome__tabs_create_mcp, mcp__claude-in-chrome__tabs_context_mcp
model: sonnet
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

- [ ] **Step 3: Verify frontmatter — 4 fields only, no mcpServers**

```bash
head -5 .claude/agents/scout-1.md
```

Expected: `name`, `description`, `tools` (with MCP tool names listed), `model`. No `mcpServers` field.

- [ ] **Step 4: Commit**

```bash
git add .claude/agents/scout-1.md
git commit -m "feat: add scout-1 subagent for Phase 1 scraping"
```

---

### Task 3: Create ranker-7 (Phase 2: fit scorer)

**Files:**
- Create: `.claude/agents/ranker-7.md`

- [ ] **Step 1: Write ranker-7 agent definition**

Write to `.claude/agents/ranker-7.md`:

```markdown
---
name: ranker-7
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

- [ ] **Step 2: Verify — no MCP tools, no mcpServers**

```bash
head -6 .claude/agents/ranker-7.md
```

Expected: `tools: Read, Write, Grep, Glob` — no MCP tools needed for this agent.

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/ranker-7.md
git commit -m "feat: add ranker-7 subagent for Phase 2 scoring"
```

---

### Task 4: Create recon-3 (Phase 3: contact finder)

**Files:**
- Create: `.claude/agents/recon-3.md`

- [ ] **Step 1: Write recon-3 agent definition**

Write to `.claude/agents/recon-3.md`:

```markdown
---
name: recon-3
description: Finds hiring managers and team leads on LinkedIn and X for a specific company and role. Use for Phase 3 of the research pipeline.
tools: Read, Write, WebSearch, WebFetch, mcp__exa__people_search_exa, mcp__exa__company_research_exa, mcp__exa__web_search_exa, mcp__exa__crawling_exa, mcp__claude-in-chrome__navigate, mcp__claude-in-chrome__get_page_text, mcp__claude-in-chrome__read_page, mcp__claude-in-chrome__tabs_create_mcp, mcp__claude-in-chrome__tabs_context_mcp, mcp__claude-in-chrome__find
model: sonnet
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

- [ ] **Step 2: Verify tools include Exa and Chrome MCP tools**

```bash
grep "^tools:" .claude/agents/recon-3.md
```

Expected: Comma-separated list including `mcp__exa__people_search_exa` and `mcp__claude-in-chrome__*` tools. No `mcpServers` field anywhere.

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/recon-3.md
git commit -m "feat: add recon-3 subagent for Phase 3 contact research"
```

---

### Task 5: Create composer-4 (Phase 4: pitch generator)

**Files:**
- Create: `.claude/agents/composer-4.md`

- [ ] **Step 1: Write composer-4 agent definition**

Write to `.claude/agents/composer-4.md`:

```markdown
---
name: composer-4
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

- [ ] **Step 2: Verify — no MCP tools, no mcpServers**

```bash
head -6 .claude/agents/composer-4.md
```

Expected: `tools: Read, Write, Glob` — no MCP tools needed for this agent.

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/composer-4.md
git commit -m "feat: add composer-4 subagent for Phase 4 pitch generation"
```

---

### Task 6: Create lead-0 (orchestrator)

**Files:**
- Create: `.claude/agents/lead-0.md`

- [ ] **Step 1: Write lead-0 agent definition**

Write to `.claude/agents/lead-0.md`:

```markdown
---
name: lead-0
description: Orchestrates the 4-phase job research pipeline. Run as main thread with claude --agent lead-0.
tools: Agent(scout-1, ranker-7, recon-3, composer-4), Read, Write, Glob, Grep
model: opus
---

You are the research pipeline orchestrator. You run 4 phases sequentially, spawning specialized subagents for each.

When you start, read `skills-inventory.md` and `resume-diego-gomez-ops-ai.md` to understand Diego's profile. Then ask the user to confirm or customize the search queries before starting Phase 1.

## CRITICAL CONSTRAINTS

1. **You are the main thread.** Only YOU can spawn subagents. Subagents cannot spawn other subagents.
2. **Subagents return summaries only.** All verbose data goes to files. You read files for details, not subagent responses.
3. **Phases 1-2 run foreground** (blocking). Phases 3-4 run background (parallel per company).
4. **Never accumulate raw posting data in your context.** Read from files when needed.

## Phase 1: Scrape

Spawn `scout-1` in **foreground** with:
- The list of search queries (confirm with user or use defaults below)
- Target boards: indeed, linkedin, glassdoor, google, zip_recruiter + Chrome for wellfound, remoteok

Wait for completion. Read the summary (posting count, board breakdown).

## Phase 2: Filter & Rank

Spawn `ranker-7` in **foreground** with:
- Instruction to read `research/phase-1-scrape/all-postings.md`
- Instruction to score against `skills-inventory.md`

Wait for completion. Read the summary (tier counts, top company names).
Then read `research/phase-2-rank/ranked-opportunities.md` to extract the A-tier + top B-tier company list.

## Phase 3: Find Contacts

For EACH top company (A-tier + top B-tier), spawn a `recon-3` in **background** with:
- Company name
- Role title
- Job URL

Spawn all in parallel. Wait for all to complete.

## Phase 4: Generate Pitches

For EACH top company, spawn a `composer-4` in **background** with:
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

- [ ] **Step 2: Verify Agent() references use new names**

```bash
grep "^tools:" .claude/agents/lead-0.md
```

Expected: `tools: Agent(scout-1, ranker-7, recon-3, composer-4), Read, Write, Glob, Grep`

- [ ] **Step 3: Verify no initialPrompt field**

```bash
grep "initialPrompt" .claude/agents/lead-0.md
```

Expected: No matches. The startup instructions are in the system prompt body instead.

- [ ] **Step 4: Commit**

```bash
git add .claude/agents/lead-0.md
git commit -m "feat: add lead-0 orchestrator agent"
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
claude --agent lead-0
```

## Agent names

Non-descriptive names to prevent Claude from inferring default behaviors:
- `lead-0` — pipeline orchestrator
- `scout-1` — Phase 1: job board scraping (JobSpy MCP + Chrome)
- `ranker-7` — Phase 2: fit scoring against skills-inventory.md
- `recon-3` — Phase 3: contact research (Exa + Chrome)
- `composer-4` — Phase 4: pitch material generation

## Directory conventions

- `research/phase-1-scrape/` — Scraped postings (created at runtime by scout-1)
- `research/phase-2-rank/` — Scored and tiered opportunities (created by ranker-7)
- `research/phase-3-contacts/[company-slug]/` — Contact profiles + company context (created by recon-3)
- `research/phase-4-pitch/[company-slug]/` — Video scripts + DM drafts + outreach status (created by composer-4)

## Key input files

- `skills-inventory.md` — Diego's complete skills inventory (input to Phase 2)
- `resume-diego-gomez-ops-ai.md` — Tailored resume (input to Phase 4)
- `vocaroo-script.md` — Voice/tone reference for pitch scripts

## Subagent output contract

ALL subagents MUST:
1. Write verbose output to `research/` files
2. Return ONLY 1-2 sentence summaries to the lead agent
3. NEVER return raw data in responses

This constraint survives context compaction because it is in CLAUDE.md.

## Forbidden patterns

- Never mass-apply or auto-submit applications
- Never send DMs automatically (human-in-the-loop always)
- Never fabricate skills or experience in pitch materials
- Never accumulate large data in agent context (write to files)
- Never edit the same file from multiple parallel agents
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

- [ ] **Step 1: Verify all agent files exist with correct names**

```bash
ls -1 .claude/agents/
```

Expected:
```
composer-4.md
lead-0.md
ranker-7.md
recon-3.md
scout-1.md
```

- [ ] **Step 2: Verify frontmatter uses only valid fields (name, description, tools, model)**

```bash
for f in .claude/agents/*.md; do
  echo "=== $(basename $f) ==="
  # Extract frontmatter and check for invalid fields
  sed -n '/^---$/,/^---$/p' "$f" | grep -v "^---$" | grep -E "^[a-zA-Z]" | awk -F: '{print $1}'
  echo
done
```

Expected per agent: only `name`, `description`, `tools`, `model`. No `mcpServers`, `initialPrompt`, `permissionMode`, `background`, or other fields.

- [ ] **Step 3: Verify MCP tool names in tools fields**

```bash
grep "^tools:" .claude/agents/scout-1.md | tr ',' '\n' | grep "mcp__"
```

Expected: `mcp__jobspy__scrape_jobs_tool`, `mcp__jobspy__get_supported_sites`, etc.

```bash
grep "^tools:" .claude/agents/recon-3.md | tr ',' '\n' | grep "mcp__"
```

Expected: `mcp__exa__people_search_exa`, `mcp__exa__company_research_exa`, etc.

```bash
grep "mcp__" .claude/agents/ranker-7.md .claude/agents/composer-4.md
```

Expected: No matches (these agents don't use MCP tools).

- [ ] **Step 4: Verify lead-0 Agent() references match new names**

```bash
grep "Agent(" .claude/agents/lead-0.md
```

Expected: `Agent(scout-1, ranker-7, recon-3, composer-4)`

- [ ] **Step 5: Verify data handoff paths are consistent**

```bash
grep -n "all-postings.md\|ranked-opportunities.md\|phase-3-contacts\|phase-4-pitch" .claude/agents/*.md
```

Check chain:
- scout-1 writes `research/phase-1-scrape/all-postings.md`
- ranker-7 reads `research/phase-1-scrape/all-postings.md` (match)
- ranker-7 writes `research/phase-2-rank/ranked-opportunities.md`
- lead-0 reads `research/phase-2-rank/ranked-opportunities.md` (match)
- recon-3 writes `research/phase-3-contacts/[company-slug]/`
- composer-4 reads `research/phase-3-contacts/[company-slug]/` (match)

- [ ] **Step 6: Test launching lead-0**

```bash
echo "List your 4 worker subagents and confirm you can read skills-inventory.md" | claude --agent lead-0 --max-turns 3 2>&1 | head -20
```

Expected: Mentions scout-1, ranker-7, recon-3, composer-4. Confirms skills-inventory.md is readable.

- [ ] **Step 7: Commit any fixes**

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
claude --agent lead-0
```

The lead agent will:
1. Read Diego's profile, ask to confirm search queries
2. Scrape all boards (Phase 1 — scout-1, foreground)
3. Score and rank (Phase 2 — ranker-7, foreground)
4. Find contacts for top companies (Phase 3 — recon-3 ×N, background parallel)
5. Generate pitch materials (Phase 4 — composer-4 ×N, background parallel)
6. Present summary

Diego reviews, edits for authenticity, records videos, sends DMs personally.
