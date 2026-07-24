# portfolio-ops

This is the small toolkit that keeps my Data & AI portfolio honest and improving
instead of drifting. It's the machinery behind a single command I run —
"run the improvement routine" — and behind a lightweight recurring status check.

I built it because a portfolio of a dozen repos is easy to let rot: a test breaks,
a repo never gets pushed, a README goes stale, and you don't notice until someone
is looking at it. This measures all of that objectively and tells me (and only me)
what to fix next.

## What's here
- **`ops/audit.py`** — a read-only scan of every portfolio repo: git state (clean?
  pushed? unpushed commits?), `ruff`, `pytest`, and whether the repo has the
  artifacts a shippable project should (README, CI, tests, business case,
  deliverables, license). Writes `scorecards/<repo>.json` + a timestamped
  `STATUS_LOG.md`.
- **`ops/rank.py`** — turns the scorecard gaps into one weighted backlog
  (`AREAS_FOR_IMPROVEMENT.md`), with loss-risk and correctness at the top.
- **`autohelper/`** — a *safe, read-only, API-first* helper for the GitHub chores
  only I can finish. It deliberately does **not** drive the cursor — see
  `autohelper/README.md` for the research and reasoning behind that choice.
- **`docs/IMPROVEMENT_ROUTINE.md`** — the full loop and its safety rules.

## Run it
```bash
python -m ops.audit          # scorecards + STATUS_LOG.md
python -m ops.rank           # AREAS_FOR_IMPROVEMENT.md
python -m ops.audit --no-tests --repos revops-optimizer,sales-kpi-analytics
python -m autohelper.github_tasks --owner Dimitres-Kisimov   # read-only chore list
```
By default it looks for the sibling repos in the parent folder; override with
`--root`.

## Safety, by design
Read-only measurement · never touches the finished flagship repo · no destructive
git · bounded parallelism · human-in-the-loop for anything outward-facing · no
overclaims and all synthetic data labelled. The full list is in the routine doc.

Author: Dimitres Kisimov.
