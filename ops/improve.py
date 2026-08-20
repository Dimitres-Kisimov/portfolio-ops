"""Boot-time improvement engine.

Runs WITHOUT an AI session: measures, ranks and drafts the next phase so a
session starts working instead of re-discovering state. It does NOT write
features - that needs a session (see HUMAN_TASKS.md decision B).

    python -m ops.improve            # full pass
    python -m ops.improve --quick    # skip test suites
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\dimik")
OPS = ROOT / "portfolio-ops"
SKIP = {"3DpicToIFCModeling", "portfolio-ops", "startup", "slotpilot", "bewerbung"}

QUOTES = chr(34) + chr(39)  # " and ' without a literal apostrophe in source
SECRET_PATTERNS = [
    (r"gh[pousr]_[A-Za-z0-9]{16,}", "GitHub token"),
    (r"sk-ant-[A-Za-z0-9_\-]{20,}", "Anthropic key"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "private key"),
    (r"(?i)password\s*[:=]\s*[" + QUOTES + r"][^" + QUOTES + r"]{6,}", "hardcoded password"),
]
RISK_PATTERNS = [
    (r"\beval\s*\(", "eval()"),
    (r"\bexec\s*\(", "exec()"),
    (r"shell\s*=\s*True", "shell=True"),
    (r"verify\s*=\s*False", "TLS verify disabled"),
    (r"pickle\.loads?\(", "pickle load"),
]
GAP_MARKERS = ["not modelled", "not modeled", "future work", "would be next",
               "TODO", "FIXME", "does not yet", "not implemented",
               "out of scope", "still missing", "remains a gap"]
BIN_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".xlsx", ".pptx",
           ".ico", ".zip", ".woff", ".woff2", ".webp", ".mp4"}


def sh(cmd, cwd=None, timeout=900):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           timeout=timeout, errors="replace")
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:  # noqa: BLE001 - a failed probe must never stop the pass
        return 1, str(e)


def repos():
    for d in sorted(ROOT.iterdir()):
        if d.is_dir() and d.name not in SKIP and (d / ".git").exists():
            yield d


def git_state(repo):
    _, br = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo, 60)
    _, st = sh(["git", "status", "--porcelain"], repo, 60)
    _, un = sh(["git", "log", "--branches", "--not", "--remotes", "--oneline"], repo, 60)
    return {"branch": br.strip(),
            "dirty": len([x for x in st.splitlines() if x.strip()]),
            "unpushed": len([x for x in un.splitlines() if x.strip()])}


def scan(repo):
    rc, files = sh(["git", "ls-files"], repo, 120)
    secrets, risks, gaps = [], [], []
    if rc != 0:
        return secrets, risks, gaps
    for rel in files.splitlines():
        rel = rel.strip()
        if not rel or Path(rel).suffix.lower() in BIN_EXT:
            continue
        f = repo / rel
        try:
            if f.stat().st_size > 2_000_000:
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat, label in SECRET_PATTERNS:
            if re.search(pat, text):
                secrets.append(rel + ": " + label)
        for pat, label in RISK_PATTERNS:
            if re.search(pat, text):
                risks.append(rel + ": " + label)
        if rel.lower().endswith(".md"):
            low = text.lower()
            for m in GAP_MARKERS:
                if m.lower() in low:
                    for line in text.splitlines():
                        if m.lower() in line.lower() and 30 < len(line) < 300:
                            gaps.append(rel + ": " + line.strip()[:200])
                            break
    return secrets, risks, gaps


def tests(repo, quick):
    if quick:
        return {"ran": False, "green": None, "summary": "skipped (--quick)"}
    tdir = next((repo / n for n in ("tests", "test") if (repo / n).exists()), None)
    if not tdir:
        return {"ran": False, "green": None, "summary": "no test dir"}
    if any(tdir.rglob("test_*.py")):
        rc, out = sh([sys.executable, "-m", "pytest", "-q"], repo, 900)
        line = next((x for x in reversed(out.splitlines())
                     if re.search(r"\d+ (passed|failed|error)", x)), "")
        return {"ran": True, "green": rc == 0, "summary": line[-160:]}
    runner = tdir / "run-all.mjs"
    cmd = ["node", str(runner)] if runner.exists() else ["node", "--test"]
    rc, out = sh(cmd, repo, 900)
    line = next((x for x in reversed(out.splitlines())
                 if "PASS" in x or "fail" in x.lower()), "")
    return {"ran": True, "green": rc == 0, "summary": ("node: " + line)[-160:]}


def main():
    quick = "--quick" in sys.argv
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report, backlog = [], []
    for repo in repos():
        g = git_state(repo)
        secrets, risks, gaps = scan(repo)
        t = tests(repo, quick)
        report.append({"repo": repo.name, "git": g, "secrets": secrets,
                       "risks": risks[:5], "gaps": len(gaps), "tests": t})
        for s in secrets:
            backlog.append((100, repo.name, "SECRET in tracked file - " + s))
        if t["green"] is False:
            backlog.append((90, repo.name, "test suite RED - " + t["summary"]))
        if g["unpushed"]:
            backlog.append((70, repo.name, str(g["unpushed"]) + " unpushed commit(s)"))
        if g["dirty"]:
            backlog.append((60, repo.name, str(g["dirty"]) + " uncommitted file(s)"))
        for r in risks[:3]:
            backlog.append((40, repo.name, "review risky shape - " + r))
        for gp in gaps[:4]:
            backlog.append((20, repo.name, "acknowledged gap - " + gp))
    backlog.sort(key=lambda x: -x[0])
    OPS.mkdir(exist_ok=True)
    (OPS / "improve_report.json").write_text(
        json.dumps({"generated": stamp, "repos": report}, indent=2), encoding="utf-8")
    red = [r for r in report if r["tests"]["green"] is False]
    sec = [r for r in report if r["secrets"]]
    dirty = [r for r in report if r["git"]["dirty"] or r["git"]["unpushed"]]
    L = ["# NEXT PHASE - auto-drafted by the boot engine",
         "*Generated " + stamp + ". Deterministic measurement; no AI ran.*", "",
         "## Health",
         "- Repos scanned: **" + str(len(report)) + "**",
         "- Test suites red: **" + str(len(red)) + "**"
         + ((" - " + ", ".join(r["repo"] for r in red)) if red else " OK"),
         "- Secrets in tracked files: **" + str(len(sec)) + "**" + (" STOP" if sec else " OK"),
         "- Uncommitted/unpushed: **" + str(len(dirty)) + "**"
         + ((" - " + ", ".join(r["repo"] for r in dirty)) if dirty else " OK"),
         "", "## Ranked backlog (top 25)", "",
         "| # | Pri | Repo | Item |", "|---|---|---|---|"]
    for i, (p, r, item) in enumerate(backlog[:25], 1):
        L.append("| " + str(i) + " | " + str(p) + " | `" + r + "` | "
                 + item.replace("|", "/") + " |")
    L += ["", "## Phase rules",
          "1. Priority >= 90 is fixed before any new feature.",
          "2. Every change ships gates-green and pushed the same session.",
          "3. A phase ends by drafting the next - this file regenerates each boot.",
          "4. Human-only items go to HUMAN_TASKS.md, never silently dropped.",
          "5. Judge every app against portfolio-ops/EVALUATION_CRITERIA.md.", "",
          "*Full data: portfolio-ops/improve_report.json*"]
    (ROOT / "PHASE_PLAN.md").write_text("\n".join(L), encoding="utf-8")
    print("[improve] " + str(len(report)) + " repos | red=" + str(len(red))
          + " secrets=" + str(len(sec)) + " dirty=" + str(len(dirty))
          + " | backlog=" + str(len(backlog)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
