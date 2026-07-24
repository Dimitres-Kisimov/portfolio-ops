# autohelper — safe automation for the portfolio's GitHub chores

I looked hard at "AI that controls the cursor/GUI" before building this, and I
deliberately did **not** build an autonomous cursor agent. Here's the honest
reasoning, and what I built instead.

## What I found researching computer-use / GUI agents
- **Scripted desktop automation** (PyAutoGUI, AutoHotkey, SikuliX) is reliable
  only as long as nothing on screen moves; it's brittle to layout, DPI and timing.
- **Browser automation** (Playwright, Selenium — Apache-2.0) is genuinely robust
  for *web* flows and is the right tool when a task is web-only.
- **LLM computer-use agents** (open: UI-TARS, Agent-S, Open Interpreter,
  self-operating-computer; proprietary: Anthropic Computer Use, OpenAI Operator,
  Gemini Computer Use) are improving fast but still land roughly in the ~40–72%
  end-to-end success range on the OSWorld benchmark, versus a ~72% human baseline.
  They also carry a real **prompt-injection** attack surface when they read live
  screens/pages. That is not something I want pointed at a GitHub account
  unattended.

**Conclusion:** for *these* tasks the API beats the cursor. GitHub is fully
covered by a REST API, so there is no reason to simulate clicks. Anything that is
outward-facing or hard to reverse (accepting a repo transfer, changing settings)
stays a human decision.

## What this helper does
`python -m autohelper.github_tasks --owner Dimitres-Kisimov`

- **Read-only.** Lists the chores only you can finish: repos missing an About
  description/topics, and a reminder to accept pending transfer invitations.
- Gets its token from `git credential` (or `GITHUB_TOKEN`) and **never prints or
  stores it**.
- Never accepts a transfer, never changes a setting, never force-pushes, never
  deletes — by design. It tells you exactly what to click.

## What it intentionally does NOT do
- No unattended mouse/keyboard control.
- No destructive git operations.
- No credential exfiltration or logging.

## If you ever want web-GUI automation
The safe pattern is a **Playwright** script for a *specific, reviewed* web flow,
run attended, with no secrets in the script. That's a deliberate, opt-in choice —
not a default of this toolkit.

Author: Dimitres Kisimov.
