# EVALUATION CRITERIA — how every app in this portfolio is judged
*The rubric the improvement engine and any agent scores against. Score each dimension 0–5; a repo is "competitive" at ≥ 4 on all of 1–5 and ≥ 3 on 6–8.*

## The eight dimensions

### 1. Measured, not asserted (weight ×2)
Every headline number is reproducible by a command printed in the README. No figure exists in prose that the code cannot regenerate.
- **5** — every number regenerable; a test fails if the committed figure drifts from what the code produces.
- **3** — numbers regenerable but not drift-guarded.
- **0** — numbers typed by hand.
*Portfolio exemplars: `ml-models-lab` (drift-guard test recomputes the whole leaderboard), `decision-chain` (17 identities re-checked).* 

### 2. Fair baseline (weight ×2)
The comparison is against the *strongest simple* alternative, never a straw man.
- **5** — the baseline is deliberately strong and named (seasonal-naive over a worse naive; PCA over a random reconstructor; MILP vs a *good* greedy), and the repo says so.
- **0** — no baseline, or one chosen to lose.

### 3. Honest limits, incl. a finding against the headline (weight ×2)
- **5** — the README states what the project is *not*, **and** at least one measured finding cuts against its own story.
- **0** — only flattering results.
*Exemplars: energy (only the first 100 kWh pays back), predictive-maintenance (the calendar rule beat its own detector), bio-efficient-ai (published a partial refutation of its earlier claim), fraud (the most common alert reason is less predictive than average).*

### 4. Reproducible / deterministic
Fixed seeds, no wall-clock or RNG in outputs, artifacts byte-identical across two runs (documented exceptions only: matplotlib/openpyxl embedded timestamps).
- **5** — byte-identity proven by test; exceptions named.

### 5. Tested for real
- **5** — hand-computed expectations, edge cases, collapse-to-base-case, determinism, and a test that would fail if the feature silently broke.
- **2** — smoke tests that only prove it runs.

### 6. Operational reality
The feature answers a question a practitioner actually asks — "what changed since last run", "which move do I ship", "how many spares", "who staffs the queue" — not a metric for its own sake.

### 7. Presentation
Subject-true design (a warehouse looks like concrete and steel, not a blueprint); WCAG AA on text; colour is never the only channel; no dual-axis charts; palettes validated for colour-vision deficiency, not eyeballed; charts rasterized and inspected before shipping.

### 8. Security & hygiene
No secrets in tracked files; `eval`/`exec`/`shell=True`/`verify=False` justified or absent; licence correct (proprietary, never MIT); no unpushed or uncommitted work at rest; docs agree with the code (no stale test counts).

---

## Per-app target state
Each app is judged against what *it* is for. The business problem and goal for every repo are in `C:\Users\dimik\AGENT_BRIEF.md` §3 — that table is the source of truth for "what is this app trying to be".

| Band | Meaning | Action |
|---|---|---|
| **Complete** | ≥4 on 1–5, ≥3 on 6–8, and its own docs list no unaddressed gap | Maintain only; do not add features for their own sake |
| **Competitive** | ≥4 on 1–5 but a documented gap remains | Next feature = the gap the repo's own docs name |
| **Needs work** | any of 1–5 below 4 | Fix the dimension before adding anything |
| **Blocked** | red suite, secret, or unpushed work | Priority ≥90 in `PHASE_PLAN.md`; fix before all else |

## How the engine uses this
`ops/improve.py` measures dimensions 4, 5 and 8 automatically (determinism proxies, suite state, secret/risk scan, git hygiene) and harvests each repo's own acknowledged gaps into the ranked backlog. Dimensions 1, 2, 3, 6 and 7 need judgement — they are scored by a session against this rubric, and the result belongs in the phase record.

## The rule that outranks the rubric
A high score obtained by removing an inconvenient finding is a failure, not a pass. **Nothing in this portfolio is ever made to look better by changing a number.** If a feature's honest result is unflattering, the honest result ships.
