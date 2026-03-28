# HireBoost Pipeline Summary

**Date:** 2026-03-27
**Pipeline Duration:** ~30 minutes (4 phases, 27 subagents)

---

## Phase 1: Scrape

- **Total Postings:** 174 (remote-only, deduplicated)
- **Boards:** Indeed (89), LinkedIn (65), Wellfound (13), RemoteOK (7)
- **Failed:** Glassdoor (errored all queries), Google (0 results), ZipRecruiter (0 results)
- **Queries:** 7 default queries across operations, AI, and developer relations
- **Output:** `research/phase-1-scrape/all-postings.md`

---

## Phase 2: Rank

- **Total Scored:** 174
- **A-Tier (80-100):** 8
- **B-Tier (60-79):** 22
- **C-Tier (40-59):** 41
- **D-Tier (0-39):** 103
- **Output:** `research/phase-2-rank/ranked-opportunities.md`

---

## Phase 3 & 4: Per-Company Results

### A-Tier

| # | Company | Role | Score | Salary | Contact Found | Materials |
|---|---------|------|-------|--------|---------------|-----------|
| 1 | Grafana Labs | Senior AI Engineer - Ops, AI/ML | 88 | ~$160K-$200K (est.) | Amy Wang Morales (Recruiter), Tom Wilkie (CTO) | Done |
| 2 | Grafana Labs | SSE - AI and Automation, Data & Analytics | 87 | $154K-$185K | Bob Samuels (Dir Analytics & Data Eng), Manoj Acharya (VP Eng) | Done |
| 3 | NXLog | Agent Lead Developer (Rust/C & AI Orchestration) | 85 | ~$90K-$130K (est.) | Botond Botyanszki (Founder & CTO) | Done |
| 4 | OneDigital | AI Builder - Remote | 82 | $90K-$115K | Vinay Gidwaney (CPO), Shannon Kearins (Recruiter) | Done |
| 5 | Flock Safety | Director, IT AI/Integrations | 82 | $170K-$190K + equity | Stacey Moore (SVP IT) | Done |
| 6 | Mercor | Operations Manager - Remote | 81 | $90-$110/hr (contract, 3-4 wks) | Sid Potdar (Head of Ops), Kuai Yu (posting contact) | Done |
| 7 | OutSystems | Manager, Expert Services | 80 | $150K-$182K | Goncalo Santos (Dir Expert Services) | Done |
| 8 | CACI International | AI Engineer | 80 | $99K-$207K (wide range) | Patrick Medina (Dir AI/ML) | Done |

### Top B-Tier

| # | Company | Role | Score | Salary | Contact Found | Materials |
|---|---------|------|-------|--------|---------------|-----------|
| 9 | DraftKings | Manager, Regulatory Compliance | 72 | $106K-$133K | Alex Walder (Dir Regulatory Compliance) | Done |
| 10 | General Motors | Staff Data Engineer | 70 | $160K-$246K | Jordan Cheeks (Sr Data Eng Manager) | Done |
| 11 | Correlation One | Embedded AI Solutions Engineer (Contract) | 70 | ~$80-$120/hr (est.) | Joseph Novak (SVP Engineering & Data) | Done |
| 12 | Rippling | Scaled Operations & Success Specialist | 70 | $82K-$143K | Kimberly Gordon (GTM Recruiting), Stephanie Ho (SVP CX) | Done |
| 13 | Rocket Money | Business Operations Manager - Deposit Products | 69 | $120K-$160K | Kirsten Klotz (VP/GM Rocket Card) | Done |

---

## Key Insights

1. **Strongest matches are technical AI roles** — Grafana Labs (x2) and NXLog score highest because they directly match Diego's inference engineering, multi-agent orchestration, and Python/Rust skills.

2. **Highest salary potential:** GM Staff Data Engineer ($160K-$246K), Flock Safety Director ($170K-$190K + equity), CACI AI Engineer (up to $207K), OutSystems Manager ($150K-$182K).

3. **Best risk-adjusted opportunities:** Grafana Labs SSE AI & Automation (87 score, $154K-$185K confirmed salary, remote-first) and Flock Safety Director (82 score, $170K-$190K + equity).

4. **Watch out:** Mercor is a short-term contract (3-4 weeks), not full-time. CACI may require security clearance. Correlation One is also contract.

5. **Unique angle:** NXLog's Rust + AI Orchestration combo is exceptionally rare in the market — Diego is one of very few candidates who can credibly claim both.

---

## File Index

### Phase 1
- `research/phase-1-scrape/all-postings.md`

### Phase 2
- `research/phase-2-rank/ranked-opportunities.md`

### Phase 3 — Contacts
- `research/phase-3-contacts/grafana-labs-ai-engineer/contacts.md`
- `research/phase-3-contacts/grafana-labs-sse-ai/contacts.md`
- `research/phase-3-contacts/nxlog/contacts.md`
- `research/phase-3-contacts/onedigital/contacts.md`
- `research/phase-3-contacts/flock-safety/contacts.md`
- `research/phase-3-contacts/mercor/contacts.md`
- `research/phase-3-contacts/outsystems/contacts.md`
- `research/phase-3-contacts/caci/contacts.md`
- `research/phase-3-contacts/draftkings/contacts.md`
- `research/phase-3-contacts/gm/contacts.md`
- `research/phase-3-contacts/correlation-one/contacts.md`
- `research/phase-3-contacts/rippling/contacts.md`
- `research/phase-3-contacts/rocket-money/contacts.md`

### Phase 4 — Pitch Materials
- `research/phase-4-pitch/grafana-labs-ai-engineer/` (video-script.md, dm-drafts.md, outreach-status.md)
- `research/phase-4-pitch/grafana-labs-sse-ai/` (video-script.md, dm-drafts.md, outreach-status.md)
- `research/phase-4-pitch/nxlog/` (video-script.md, dm-drafts.md, outreach-status.md)
- `research/phase-4-pitch/onedigital/` (video-script.md, dm-drafts.md, outreach-status.md)
- `research/phase-4-pitch/flock-safety/` (video-script.md, dm-drafts.md, outreach-status.md)
- `research/phase-4-pitch/mercor/` (video-script.md, dm-drafts.md, outreach-status.md)
- `research/phase-4-pitch/outsystems/` (video-script.md, dm-drafts.md, outreach-status.md)
- `research/phase-4-pitch/caci/` (video-script.md, dm-drafts.md, outreach-status.md)
- `research/phase-4-pitch/draftkings/` (video-script.md, dm-drafts.md, outreach-status.md)
- `research/phase-4-pitch/gm/` (video-script.md, dm-drafts.md, outreach-status.md)
- `research/phase-4-pitch/correlation-one/` (video-script.md, dm-drafts.md, outreach-status.md)
- `research/phase-4-pitch/rippling/` (video-script.md, dm-drafts.md, outreach-status.md)
- `research/phase-4-pitch/rocket-money/` (video-script.md, dm-drafts.md, outreach-status.md)

---

## Recommended Priority Order

1. **Grafana Labs SSE AI & Automation** — Best risk-adjusted (87, confirmed $154K-$185K, remote-first)
2. **Grafana Labs Senior AI Engineer** — Top score (88), apply to both Grafana roles
3. **Flock Safety Director** — Highest confirmed salary ($170K-$190K + equity), slight seniority stretch
4. **NXLog Agent Lead Developer** — Rarest skills match (Rust + AI orchestration), salary TBD
5. **OutSystems Manager Expert Services** — Strong salary ($150K-$182K), agentic AI delivery context
6. **OneDigital AI Builder** — Best role-title match for Diego's builder profile, lower salary
7. **CACI AI Engineer** — Strong match, verify clearance requirement first
8. **GM Staff Data Engineer** — Exceptional salary range, leverage data engineering portfolio
9. **Mercor Operations Manager** — Short-term contract only, good for cash flow
10. **DraftKings Manager Compliance** — Leverage compliance scoring framework angle
11. **Correlation One AI Solutions Engineer** — Contract, good for portfolio building
12. **Rocket Money Business Ops Manager** — Solid fintech ops role, $120K-$160K
13. **Rippling Scaled Ops** — Strong company, lower salary range for this role
