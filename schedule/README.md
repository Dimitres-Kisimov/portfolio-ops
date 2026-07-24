# The 3-hourly status check (local option)

This folder makes the recurring status check real on your machine **without me
changing anything on your system** — registering the scheduled task is a single
opt-in command you run.

`run_status_check.bat` runs the **read-only** audit + ranked backlog every time it
fires and appends to `STATUS_LOG.md` (and `schedule/cron.log`). It never pushes,
never modifies a repo — it only measures and logs.

## Enable it (one command, your choice)

Open PowerShell and register a task that runs every 3 hours:

```powershell
schtasks /Create /SC HOURLY /MO 3 /TN "PortfolioStatusCheck" ^
  /TR "C:\Users\dimik\portfolio-ops\schedule\run_status_check.bat" /F
```

Check it / run it once now / remove it:

```powershell
schtasks /Query  /TN "PortfolioStatusCheck"
schtasks /Run    /TN "PortfolioStatusCheck"
schtasks /Delete /TN "PortfolioStatusCheck" /F
```

(There's also `PortfolioStatusCheck.xml` here if you prefer
`schtasks /Create /XML PortfolioStatusCheck.xml /TN "PortfolioStatusCheck"`.)

## Or use the cloud option instead
If you'd rather it run in the cloud against the pushed repos (no need for this PC
to be on), tell me and I'll set up a scheduled cloud routine instead. Cloud runs
only see what's pushed — which is why the improvement routine pushes every
milestone.

## Notes
- The machine must be on and logged in for the local task to fire.
- The check is intentionally cheap and read-only, so running it often is safe.
- `cron.log` is git-ignored; `STATUS_LOG.md` is committed so the trail is visible.
