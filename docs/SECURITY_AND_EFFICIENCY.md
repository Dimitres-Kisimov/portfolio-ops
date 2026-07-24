# Security & efficiency review (portfolio standard)

An honest pass over how the portfolio handles secrets, data, dependencies and
compute. It's written as a review, not a marketing page — where something is a
deliberate limitation, it says so.

## Security posture

**Secrets never live in code.**
- GitHub tokens are read from the OS `git credential` store at run time and are
  **never printed, logged, or committed**. The one helper that touches the API
  (`autohelper/github_tasks.py`) reads the token, uses it, and never echoes it.
- `.gitignore` in every repo excludes `.env`, caches, and build output. No API
  keys, connection strings, or credentials are checked in.
- The LLM-facing demos (agentic-automation-lab, doc-extract-agent) default to a
  **key-free mock**; a real key is opt-in via an environment variable, never a
  file in the repo.

**Least privilege & human-in-the-loop for anything outward-facing.**
- The autohelper is **read-only by design** — it lists the chores a human must do
  (accept a transfer, set a repo description) and refuses to do them itself,
  because those are hard-to-reverse, account-level actions.
- No unattended cursor/GUI automation (see `autohelper/README.md` for the
  reliability + prompt-injection reasoning behind that choice).

**Data privacy.**
- Every dataset in the portfolio is **synthetic and seeded** — there is no real
  customer, employee, or company PII anywhere. Company references (Würth, Schwarz)
  are independent analysis of **public** information, explicitly disclaimed, using
  no internal data.

**Supply-chain / dependency hygiene.**
- Small, well-known dependency sets (numpy, scipy, matplotlib, flask, openpyxl,
  OR-Tools, PyTorch). No obscure transitive-heavy packages. Static sites are
  **dependency-free and offline** (no CDN scripts/fonts) — which also removes a
  whole class of third-party-script risk.
- CI pins Python and installs from `requirements.txt`; linting (`ruff`) runs on
  every push.

**Known limitations (stated, not hidden).**
- No auth layer on the Flask demos — they're single-user local dashboards, not
  internet-exposed services. Adding an auth stub + rate limiting is the documented
  next step before any real deployment.
- CI does not yet run a dependency-vulnerability scanner (e.g. `pip-audit`); that's
  a reasonable addition and is noted in the backlog.

## Efficiency posture

**Everything runs on a laptop, fast, offline.**
- All models are the **smallest credible version** that still demonstrates the
  method — seconds-to-minutes on CPU, no GPU required, no data download at run
  time. The bio-efficient-ai work is *about* efficiency (fly-hash retrieval at
  4–16 bits; a ~32-neuron CfC beating a larger GRU on params).
- Expensive computations in the platform are **computed once at startup and
  cached**; only the light, parameterised optimisers run per request, so the
  dashboard stays responsive.
- Charts and sites are **hand-built (Canvas/SVG)** and render offline — no heavy
  front-end framework, no network round-trips.
- Determinism (fixed seeds) means results are reproducible and cache-friendly, and
  the audit engine is **read-only** so a status check never mutates a repo.

## Efficiency/security both: the audit engine
`ops/audit.py` is intentionally read-only and bounded (per-command timeouts, no
network), so running the 3-hourly check is cheap and can never damage a repo. The
improvement routine caps concurrent build work to keep usage predictable.

*Author: Dimitres Kisimov. This is a living review — items under "known
limitations" are tracked in `AREAS_FOR_IMPROVEMENT.md`.*
