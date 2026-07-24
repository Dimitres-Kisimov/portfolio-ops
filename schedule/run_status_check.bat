@echo off
REM ---------------------------------------------------------------------------
REM run_status_check.bat - the local 3-hourly portfolio status check.
REM Runs the read-only audit + ranked backlog and appends STATUS_LOG.md.
REM It does NOT push or modify any repo; it only measures and logs locally.
REM Register it with Task Scheduler using the opt-in command in schedule/README.md.
REM ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0.."
echo [%DATE% %TIME%] portfolio status check starting >> schedule\cron.log

REM Prefer the py launcher, fall back to python on PATH.
where py >nul 2>nul && (set PYEXE=py) || (set PYEXE=python)

%PYEXE% -m ops.audit --no-tests >> schedule\cron.log 2>&1
%PYEXE% -m ops.rank        >> schedule\cron.log 2>&1

echo [%DATE% %TIME%] portfolio status check done >> schedule\cron.log
endlocal
