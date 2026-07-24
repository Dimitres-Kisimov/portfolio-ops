# The improvement routine

This is the repeatable loop that keeps the whole portfolio getting better instead
of rotting. It's designed to be run by me on demand ("run the improvement
routine") or on a schedule, and to be **idempotent and resumable** — if a run is
interrupted, the next one picks up from the scorecards with zero lost state.

## One cycle

1. **Audit** — `python -m ops.audit`
   Read-only scan of every portfolio repo: git state (clean? pushed? unpushed
   commits?), `ruff` lint, `pytest`, and the presence of README / CI / tests /
   business case / deliverables / license. Writes `scorecards/<repo>.json` and a
   timestamped roll-up in `STATUS_LOG.md`.

2. **Rank** — `python -m ops.rank`
   Turn the scorecard gaps into a single weighted backlog in
   `AREAS_FOR_IMPROVEMENT.md`. Weights put *loss risk* (unpushed work) and
   *correctness* (failing tests) at the top; cosmetics at the bottom.

3. **Improve** — take the top item and build it to the quality bar. Where a change
   is a genuine fork (e.g. two forecasting methods, two packing heuristics), build
   an **A/B variant** and keep the winner by the metric, not by taste.

4. **Re-gate** — re-run `ruff` + `pytest`, rebuild any deliverables, confirm the
   app/CLI still boots. A change isn't done until the gates are green again.

5. **Record** — regenerate the scorecard for that repo, append `HUMAN_INPUT.md`
   with anything only the human can do (screenshots, Power BI import, accepting a
   transfer), and update the backlog.

6. **Ship** — commit (author `Dimitres Kisimov`, no AI trailer) and push each
   milestone so nothing waits unpushed. Tick the item in `PROGRAM.md`.

## Safety rules baked into the routine
- **Read-only audit.** The measuring step never modifies a repo.
- **Never touches the finished flagship** (`3DpicToIFCModeling`) — it's excluded.
- **No destructive git** — no force-push, no history rewrite, no tag force-move,
  without explicit per-instance consent.
- **Bounded parallelism** — at most a few build agents at once, to keep quality
  high and usage predictable.
- **Honesty** — no "superhuman/SOTA/patented" claims; synthetic data and estimates
  are always labelled; benchmarks are fair and reproducible with fixed seeds.
- **Human-in-the-loop** for anything outward-facing or hard to reverse.

## Scheduling (the 3-hourly check + daily improvement)
The routine is a *run*, not a daemon — a scheduler fires it and it resumes from
the scorecards. Two options (the human picks one):
- **Local** — a Windows Task Scheduler entry + a small `.bat` that runs the audit
  and, if configured, kicks the improvement step.
- **Cloud** — a scheduled routine that runs against the pushed repos. Cloud runs
  only see what's pushed, which is why the routine pushes every milestone.

`STATUS_LOG.md` is the durable trail of every check; `AREAS_FOR_IMPROVEMENT.md`
is always the current top of the backlog.
