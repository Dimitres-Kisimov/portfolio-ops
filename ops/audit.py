"""audit.py — the engine behind the portfolio improvement routine.

For each portfolio repo it scans, it records an objective quality snapshot:
git state (is everything pushed?), lint (ruff), tests (pytest), and the presence
of the artifacts a professional repo should have (README, CI, deliverables,
business case, license). It writes one ``quality_scorecard.json`` per repo and a
single timestamped ``STATUS_LOG.md`` roll-up, and it flags concrete gaps that
feed ``AREAS_FOR_IMPROVEMENT.md``.

This is deliberately read-only: it *measures*, it does not modify the repos.
The human-in-the-loop improvement routine (see docs/IMPROVEMENT_ROUTINE.md) reads
these scorecards to decide what to build next.

    python -m ops.audit [--root C:/Users/dimik] [--repos a,b,c] [--no-tests]

Author: Dimitres Kisimov.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ASCII-only markers keep this safe on the Windows console (no UnicodeEncodeError).
OK, WARN, BAD = "[ok]", "[warn]", "[--]"

# The portfolio repos the routine watches. Kept here as the single source of
# truth; extend as new repos ship.
DEFAULT_REPOS = [
    "revops-optimizer",
    "sales-kpi-analytics",
    "distributor-intelligence-platform",
    "agentic-automation-lab",
    "agent-flow-studio",
    "doc-extract-agent",
    "automation-roi-explorer",
    "route-optimizer",
    "bio-efficient-ai",
    "ml-models-lab",
    "logistics-digital-twin",
    "wuerth-data-ai-casestudy",
    "supply-network-opt",
    "logistics-flow-studio",
    "market-basket-analysis",
    "portfolio-site",
    "retail-analytics-real",
    "predictive-maintenance",
    "fraud-detection-ops",
    "energy-demand-forecast",
    "quality-anomaly-vision",
    "quantum-explainer",
    "decision-chain",
    "chain-mcp",
]

# Artifacts we expect a shippable, professional repo to carry.
EXPECTED = {
    "readme": ["README.md"],
    "license": ["LICENSE", "LICENSE.md"],
    "ci": [".github/workflows"],
    "tests": ["tests", "test"],
    "business_case": ["docs/BUSINESS_CASE.md"],
    # a repo's exportable artifact may live in deliverables/ or paper/ (research)
    "deliverables": ["deliverables", "paper"],
}


def _run(cmd: list[str], cwd: Path, timeout: int = 300) -> tuple[int, str]:
    """Run a command, capturing combined output. Never raises on non-zero."""
    try:
        p = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace",
        )
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError as e:
        return 127, f"not found: {e}"
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s"


def _git_state(repo: Path) -> dict:
    """Is the repo clean and fully pushed? Unpushed work is the #1 loss risk."""
    if not (repo / ".git").exists():
        return {"is_git": False}
    _, branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo, 30)
    _, dirty = _run(["git", "status", "--porcelain"], repo, 30)
    _, has_remote = _run(["git", "remote"], repo, 30)
    unpushed = ""
    if has_remote.strip():
        # commits on HEAD not on any remote branch
        _, unpushed = _run(
            ["git", "log", "--branches", "--not", "--remotes", "--oneline"], repo, 30
        )
    return {
        "is_git": True,
        "branch": branch.strip(),
        "clean": not dirty.strip(),
        "dirty_files": [ln[3:] for ln in dirty.splitlines() if ln.strip()],
        "has_remote": bool(has_remote.strip()),
        "unpushed_commits": len([x for x in unpushed.splitlines() if x.strip()]),
    }


def _present(repo: Path, paths: list[str]) -> bool:
    return any((repo / p).exists() for p in paths)


def audit_repo(repo: Path, run_tests: bool = True) -> dict:
    """Produce one repo's scorecard dict."""
    sc: dict = {"repo": repo.name, "exists": repo.exists()}
    if not repo.exists():
        return sc

    sc["git"] = _git_state(repo)
    sc["artifacts"] = {k: _present(repo, v) for k, v in EXPECTED.items()}

    # lint
    rc, out = _run([sys.executable, "-m", "ruff", "check", "."], repo, 180)
    sc["ruff"] = {"clean": rc == 0, "code": rc, "tail": out.strip()[-400:]}

    # tests (optional; the slow part)
    if run_tests and _present(repo, EXPECTED["tests"]):
        rc, out = _run([sys.executable, "-m", "pytest", "-q"], repo, 420)
        # pull a passed/failed count out of pytest's summary line if present
        summary = out.strip().splitlines()[-1] if out.strip() else ""
        sc["pytest"] = {"green": rc == 0, "code": rc, "summary": summary[-160:]}
    else:
        sc["pytest"] = {"green": None, "code": None, "summary": "no tests dir / skipped"}

    sc["gaps"] = _gaps(sc)
    sc["score"] = _score(sc)
    return sc


def _gaps(sc: dict) -> list[str]:
    g = []
    a = sc.get("artifacts", {})
    for key, present in a.items():
        if not present:
            g.append(f"missing {key}")
    git = sc.get("git", {})
    if git.get("is_git"):
        if not git.get("has_remote"):
            g.append("no git remote (unpushed / not shipped)")
        if git.get("unpushed_commits"):
            g.append(f"{git['unpushed_commits']} unpushed commit(s)")
        if not git.get("clean"):
            g.append(f"{len(git.get('dirty_files', []))} uncommitted file(s)")
    else:
        g.append("not a git repo")
    if not sc.get("ruff", {}).get("clean", False):
        g.append("ruff not clean")
    if sc.get("pytest", {}).get("green") is False:
        g.append("pytest failing")
    return g


def _score(sc: dict) -> int:
    """A blunt 0-100 health score: artifacts + clean git + green gates."""
    pts = 0
    a = sc.get("artifacts", {})
    pts += sum(10 for v in a.values() if v)          # up to 60
    git = sc.get("git", {})
    if git.get("has_remote"):
        pts += 10
    if git.get("clean") and not git.get("unpushed_commits"):
        pts += 10
    if sc.get("ruff", {}).get("clean"):
        pts += 10
    if sc.get("pytest", {}).get("green") in (True, None):
        pts += 10
    return min(pts, 100)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def write_status_log(cards: list[dict], out: Path) -> None:
    """Append a timestamped roll-up to STATUS_LOG.md (newest at top of the run)."""
    lines = [f"## Status check — {_now()}", ""]
    lines.append("| repo | score | git | ruff | tests | gaps |")
    lines.append("|---|---|---|---|---|---|")
    for c in cards:
        if not c.get("exists"):
            lines.append(f"| {c['repo']} | — | not present | — | — | not built yet |")
            continue
        git = c["git"]
        gstate = (OK if git.get("has_remote") and git.get("clean")
                  and not git.get("unpushed_commits") else WARN)
        rstate = OK if c["ruff"]["clean"] else BAD
        tstate = {True: OK, None: "-", False: BAD}[c["pytest"]["green"]]
        gaps = ", ".join(c["gaps"]) or "none"
        lines.append(f"| {c['repo']} | {c['score']} | {gstate} | {rstate} "
                     f"| {tstate} | {gaps} |")
    lines.append("")
    prev = out.read_text(encoding="utf-8") if out.exists() else "# STATUS_LOG\n\n"
    out.write_text(prev.rstrip() + "\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Portfolio audit / scorecard engine")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]),
                    help="folder that contains the portfolio repos")
    ap.add_argument("--repos", default="", help="comma-separated subset")
    ap.add_argument("--no-tests", action="store_true", help="skip pytest (faster)")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1]))
    a = ap.parse_args()

    root = Path(a.root)
    repos = [r.strip() for r in a.repos.split(",") if r.strip()] or DEFAULT_REPOS
    out_dir = Path(a.out)
    (out_dir / "scorecards").mkdir(parents=True, exist_ok=True)

    cards = []
    print(f"Auditing {len(repos)} repos under {root}")
    for name in repos:
        repo = root / name
        card = audit_repo(repo, run_tests=not a.no_tests)
        cards.append(card)
        (out_dir / "scorecards" / f"{name}.json").write_text(
            json.dumps(card, indent=2), encoding="utf-8")
        score = card.get("score", "n/a")
        gaps = ", ".join(card.get("gaps", [])) or ("not present" if not card.get("exists") else "none")
        print(f"  {name:<38} score={score:<4} {gaps}")

    write_status_log(cards, out_dir / "STATUS_LOG.md")
    (out_dir / "scorecards" / "_summary.json").write_text(
        json.dumps({"generated": _now(),
                    "mean_score": round(sum(c.get("score", 0) for c in cards) / max(len(cards), 1), 1),
                    "repos": {c["repo"]: c.get("score") for c in cards}}, indent=2),
        encoding="utf-8")
    print(f"Wrote scorecards + STATUS_LOG.md under {out_dir}")


if __name__ == "__main__":
    main()
