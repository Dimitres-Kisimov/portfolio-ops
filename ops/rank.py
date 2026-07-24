"""rank.py — turn the audit scorecards into a ranked improvement backlog.

The improvement routine is only as good as its prioritisation. This module reads
the ``scorecards/*.json`` written by :mod:`ops.audit` and produces a single
ranked list of concrete work items, weighted so the things that most hurt a
portfolio (unpushed work you could lose, failing tests, missing README) float to
the top and cosmetic gaps sink. It writes ``AREAS_FOR_IMPROVEMENT.md``.

    python -m ops.rank

Author: Dimitres Kisimov.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

# gap substring -> (priority weight, why it matters). Higher weight = do first.
WEIGHTS: dict[str, tuple[int, str]] = {
    "unpushed": (100, "risk of losing work — push immediately"),
    "no git remote": (95, "not shipped — create repo and push"),
    "uncommitted": (80, "uncommitted changes — commit so nothing is lost"),
    "pytest failing": (75, "correctness regression — fix before anything else"),
    "not a git repo": (70, "initialise version control"),
    "missing readme": (60, "no README — the first thing a reviewer reads"),
    "missing tests": (55, "no tests — add a pytest suite for confidence"),
    "ruff not clean": (50, "lint errors — quick, high-signal fix"),
    "missing ci": (45, "no CI — add a GitHub Actions gate"),
    "missing business_case": (35, "no business framing — add BUSINESS_CASE.md"),
    "missing deliverables": (30, "no exportable deliverable (PDF/Excel)"),
    "missing license": (20, "add an explicit LICENSE"),
}


def _weight(gap: str) -> tuple[int, str]:
    for key, val in WEIGHTS.items():
        if key in gap:
            return val
    return (10, "minor polish")


def rank(scorecard_dir: Path) -> list[dict]:
    items: list[dict] = []
    for f in sorted(scorecard_dir.glob("*.json")):
        if f.name.startswith("_"):
            continue
        sc = json.loads(f.read_text(encoding="utf-8"))
        for gap in sc.get("gaps", []):
            w, why = _weight(gap)
            items.append({"repo": sc["repo"], "gap": gap, "priority": w, "why": why})
    items.sort(key=lambda x: (-x["priority"], x["repo"]))
    return items


def write_markdown(items: list[dict], out: Path) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Areas for improvement (auto-ranked)",
        "",
        f"_Generated {now} by `ops.rank` from the latest audit scorecards. "
        "Highest-impact items first. This is a living backlog._",
        "",
        "| # | priority | repo | action | why |",
        "|---|---|---|---|---|",
    ]
    for i, it in enumerate(items, 1):
        lines.append(f"| {i} | {it['priority']} | {it['repo']} | {it['gap']} | {it['why']} |")
    if not items:
        lines.append("| — | — | — | nothing outstanding | all gates green |")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    sc_dir = root / "scorecards"
    if not sc_dir.exists():
        print("No scorecards yet — run `python -m ops.audit` first.")
        return
    items = rank(sc_dir)
    write_markdown(items, root / "AREAS_FOR_IMPROVEMENT.md")
    print(f"Ranked {len(items)} improvement items -> AREAS_FOR_IMPROVEMENT.md")
    for it in items[:10]:
        print(f"  [{it['priority']:>3}] {it['repo']:<34} {it['gap']}")


if __name__ == "__main__":
    main()
