#!/usr/bin/env python3
"""Application tracker — manages research/applications.md as persistent state.

Usage:
    python scripts/tracker.py add --company "Anthropic" --role "Research Engineer" --score 8.9 --url "https://..."
    python scripts/tracker.py update --company "Anthropic" --role "Research Engineer" --status applied
    python scripts/tracker.py import-run <RUN_DIR>    # bulk import from a pipeline run
    python scripts/tracker.py dedup                    # deduplicate entries
    python scripts/tracker.py show                     # print current tracker
"""

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRACKER_PATH = PROJECT_ROOT / "research" / "applications.md"
STATES_PATH = PROJECT_ROOT / "templates" / "states.yml"

HEADER = "| # | Date | Company | Role | Score | Status | Archetype | URL | Notes |"
SEPARATOR = "|---|------|---------|------|-------|--------|-----------|-----|-------|"


def load_states() -> dict:
    """Load status definitions from states.yml."""
    with open(STATES_PATH) as f:
        data = yaml.safe_load(f)
    return data["statuses"]


def normalize_status(raw: str, states: dict) -> str:
    """Normalize a status string to canonical form."""
    raw_lower = raw.strip().lower()
    for key, info in states.items():
        if raw_lower == key or raw_lower == info["label"].lower():
            return key
        if raw_lower in [a.lower() for a in info.get("aliases", [])]:
            return key
    return raw_lower


def status_order(status: str, states: dict) -> int:
    """Return sort order for a status. Unknown statuses sort last."""
    if status in states:
        return states[status]["order"]
    return 99


def parse_tracker(path: Path) -> list[dict]:
    """Parse applications.md into a list of row dicts."""
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("| #") or line.startswith("|--"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 8:
            continue
        rows.append({
            "num": cells[0],
            "date": cells[1],
            "company": cells[2],
            "role": cells[3],
            "score": cells[4],
            "status": cells[5],
            "archetype": cells[6] if len(cells) > 6 else "",
            "url": cells[7] if len(cells) > 7 else "",
            "notes": cells[8] if len(cells) > 8 else "",
        })
    return rows


def write_tracker(path: Path, rows: list[dict]) -> None:
    """Write rows back to applications.md."""
    # Build status summary
    status_counts = {}
    for r in rows:
        s = r["status"]
        status_counts[s] = status_counts.get(s, 0) + 1
    summary = " | ".join(f"{s}: {c}" for s, c in status_counts.items())

    lines = [
        "# Application Tracker",
        "",
        f"Last updated: {date.today().isoformat()}",
        f"Total: {len(rows)} | {summary}" if summary else f"Total: {len(rows)}",
        "",
        HEADER,
        SEPARATOR,
    ]
    for row in rows:
        lines.append(
            f"| {row['num']} | {row['date']} | {row['company']} | {row['role']} "
            f"| {row['score']} | {row['status']} | {row['archetype']} "
            f"| {row['url']} | {row['notes']} |"
        )
    path.write_text("\n".join(lines) + "\n")


def fuzzy_role_match(a: str, b: str) -> bool:
    """Two roles match if they share 2+ words longer than 3 chars."""
    words_a = {w.lower() for w in re.findall(r"\w+", a) if len(w) > 3}
    words_b = {w.lower() for w in re.findall(r"\w+", b) if len(w) > 3}
    return len(words_a & words_b) >= 2


def find_duplicate(rows: list[dict], company: str, role: str) -> int | None:
    """Find index of existing row matching company + role. Returns None if no match."""
    comp_norm = re.sub(r"[^a-z0-9]", "", company.lower())
    for i, row in enumerate(rows):
        row_comp = re.sub(r"[^a-z0-9]", "", row["company"].lower())
        if comp_norm == row_comp and fuzzy_role_match(role, row["role"]):
            return i
    return None


def add_entry(
    rows: list[dict],
    company: str,
    role: str,
    score: str,
    url: str = "",
    archetype: str = "",
    notes: str = "",
    status: str = "evaluated",
) -> list[dict]:
    """Add or update an entry. If duplicate found with lower score, update in place."""
    dup_idx = find_duplicate(rows, company, role)
    next_num = str(max((int(r["num"]) for r in rows if r["num"].isdigit()), default=0) + 1)
    entry = {
        "num": next_num,
        "date": date.today().isoformat(),
        "company": company,
        "role": role,
        "score": score,
        "status": status,
        "archetype": archetype,
        "url": url,
        "notes": notes,
    }
    if dup_idx is not None:
        existing = rows[dup_idx]
        try:
            if float(score) > float(existing["score"]):
                entry["num"] = existing["num"]  # keep original number
                rows[dup_idx] = entry
        except ValueError:
            pass  # non-numeric scores, skip update
    else:
        rows.append(entry)
    return rows


def dedup(rows: list[dict], states: dict) -> list[dict]:
    """Deduplicate by company+role. Keep highest score, promote to most advanced status."""
    seen: dict[tuple, int] = {}
    result = []
    for row in rows:
        comp_norm = re.sub(r"[^a-z0-9]", "", row["company"].lower())
        key = None
        for existing_key, idx in seen.items():
            if existing_key[0] == comp_norm and fuzzy_role_match(
                row["role"], result[idx]["role"]
            ):
                key = existing_key
                break
        if key is not None:
            existing = result[seen[key]]
            # keep higher score
            try:
                if float(row["score"]) > float(existing["score"]):
                    row["num"] = existing["num"]
                    # promote to more advanced status
                    if status_order(row["status"], states) < status_order(
                        existing["status"], states
                    ):
                        row["status"] = existing["status"]
                    result[seen[key]] = row
                else:
                    # still promote status if the duplicate is further along
                    if status_order(row["status"], states) > status_order(
                        existing["status"], states
                    ):
                        existing["status"] = row["status"]
            except ValueError:
                pass
        else:
            new_key = (comp_norm, row["role"].lower())
            seen[new_key] = len(result)
            result.append(row)
    return result


def import_run(run_dir: Path, states: dict) -> list[dict]:
    """Import A-tier and B-tier entries from a pipeline run's ranked-opportunities.md."""
    ranked_path = run_dir / "phase-2-rank" / "ranked-opportunities.md"
    if not ranked_path.exists():
        print(f"Error: {ranked_path} not found", file=sys.stderr)
        return []

    rows = parse_tracker(TRACKER_PATH)
    content = ranked_path.read_text()
    # Parse markdown sections for A-tier and B-tier entries
    current_tier = None
    lines_list = content.splitlines()
    for idx, line in enumerate(lines_list):
        if "## A-Tier" in line or "## A-tier" in line:
            current_tier = "A"
        elif "## B-Tier" in line or "## B-tier" in line:
            current_tier = "B"
        elif "## C-Tier" in line or "## C-tier" in line or "## D-Tier" in line:
            current_tier = None

        if current_tier and line.startswith("### "):
            # Parse: ### 1. Role at Company — Score: N | ...
            # or:   ### 1. Role — Score: N | ...
            match = re.search(
                r"###\s+\d+\.\s+(.+?)\s+(?:at\s+(.+?)\s+)?—\s+Score:\s*([\d.]+)", line
            )
            if match:
                role = match.group(1).strip()
                company = match.group(2).strip() if match.group(2) else "Unknown"
                score = match.group(3)
                archetype_match = re.search(r"Archetype:\s+(.+?)(?:\s*\||$)", line)
                archetype = archetype_match.group(1).strip() if archetype_match else ""
                # Look for URL in next few lines
                url = ""
                search_window = "\n".join(lines_list[idx : idx + 15])
                url_match = re.search(
                    r"\*\*(?:Job )?URL:\*\*\s*(https?://\S+)", search_window
                )
                if url_match:
                    url = url_match.group(1)

                rows = add_entry(
                    rows,
                    company,
                    role,
                    score,
                    url=url,
                    archetype=archetype,
                    notes=f"Tier {current_tier} | Run {run_dir.name}",
                )

    rows = dedup(rows, states)
    return rows


def main():
    parser = argparse.ArgumentParser(description="Application tracker")
    sub = parser.add_subparsers(dest="command")

    add_p = sub.add_parser("add")
    add_p.add_argument("--company", required=True)
    add_p.add_argument("--role", required=True)
    add_p.add_argument("--score", required=True)
    add_p.add_argument("--url", default="")
    add_p.add_argument("--archetype", default="")
    add_p.add_argument("--notes", default="")
    add_p.add_argument("--status", default="evaluated")

    update_p = sub.add_parser("update")
    update_p.add_argument("--company", required=True)
    update_p.add_argument("--role", required=True)
    update_p.add_argument("--status", required=True)

    import_p = sub.add_parser("import-run")
    import_p.add_argument("run_dir", type=Path)

    sub.add_parser("dedup")
    sub.add_parser("show")

    args = parser.parse_args()
    states = load_states()

    if args.command == "add":
        rows = parse_tracker(TRACKER_PATH)
        rows = add_entry(
            rows,
            args.company,
            args.role,
            args.score,
            url=args.url,
            archetype=args.archetype,
            notes=args.notes,
            status=normalize_status(args.status, states),
        )
        write_tracker(TRACKER_PATH, rows)
        print(f"Added/updated: {args.company} — {args.role}")

    elif args.command == "update":
        rows = parse_tracker(TRACKER_PATH)
        idx = find_duplicate(rows, args.company, args.role)
        if idx is not None:
            rows[idx]["status"] = normalize_status(args.status, states)
            rows[idx]["date"] = date.today().isoformat()
            write_tracker(TRACKER_PATH, rows)
            print(f"Updated: {args.company} — {args.role} -> {args.status}")
        else:
            print(f"Not found: {args.company} — {args.role}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "import-run":
        run_dir = args.run_dir
        if not run_dir.is_absolute():
            run_dir = PROJECT_ROOT / run_dir
        rows = import_run(run_dir, states)
        if rows:
            # Backup before overwrite
            if TRACKER_PATH.exists():
                shutil.copy2(TRACKER_PATH, TRACKER_PATH.with_suffix(".md.bak"))
            write_tracker(TRACKER_PATH, rows)
            print(f"Imported {len(rows)} entries from {run_dir.name}")

    elif args.command == "dedup":
        rows = parse_tracker(TRACKER_PATH)
        before = len(rows)
        rows = dedup(rows, states)
        if TRACKER_PATH.exists():
            shutil.copy2(TRACKER_PATH, TRACKER_PATH.with_suffix(".md.bak"))
        write_tracker(TRACKER_PATH, rows)
        print(f"Deduped: {before} -> {len(rows)} entries")

    elif args.command == "show":
        if TRACKER_PATH.exists():
            print(TRACKER_PATH.read_text())
        else:
            print("No tracker found. Run 'import-run' first.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
