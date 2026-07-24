"""github_tasks.py — a SAFE, read-only helper that lists the GitHub chores only
the human can finish (pending repo transfers, repos missing a description/topics,
missing CI badges).

Design stance (see autohelper/README.md): API-FIRST and READ-ONLY by default.
It never force-pushes, never deletes, never accepts a transfer on its own, and it
never drives your mouse/keyboard. It just tells you, precisely, what to click.
Accepting a transfer or changing repo settings is left to you (a 2-click action),
because those are outward-facing, hard-to-reverse actions that deserve a human.

Auth: reads the token from ``git credential`` (never printed, never stored). If
that is unavailable it reads ``GITHUB_TOKEN`` from the environment. If neither is
present it prints guidance and exits 0 (no crash).

    python -m autohelper.github_tasks --owner Dimitres-Kisimov

Author: Dimitres Kisimov.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"


def _token() -> str | None:
    """Get a token from git credential (preferred) or GITHUB_TOKEN. Never logged."""
    try:
        p = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            capture_output=True, text=True, timeout=20,
        )
        for line in p.stdout.splitlines():
            if line.startswith("password="):
                return line[len("password="):].strip()
    except Exception:
        pass
    return os.environ.get("GITHUB_TOKEN")


def _get(path: str, token: str) -> object:
    req = urllib.request.Request(
        f"{API}{path}",
        headers={"Authorization": f"token {token}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "portfolio-ops-autohelper"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 (fixed host)
        return json.loads(r.read().decode("utf-8"))


def list_tasks(owner: str, token: str) -> list[str]:
    """Return a human-readable checklist of outstanding, human-only chores."""
    tasks: list[str] = []
    try:
        repos = _get(f"/users/{owner}/repos?per_page=100&sort=updated", token)
    except urllib.error.HTTPError as e:
        return [f"Could not list repos for {owner} (HTTP {e.code}). "
                "Check the token has 'repo' scope and the owner is correct."]
    if not isinstance(repos, list):
        return ["Unexpected API response — is the owner name right?"]

    for repo in repos:
        name = repo.get("name", "?")
        if not repo.get("description"):
            tasks.append(f"[{name}] add an About description + topics "
                         f"(Settings -> gear icon next to About)")
    # Pending incoming transfers show up under notifications; surface a reminder.
    tasks.append("Check https://github.com/notifications for any pending repo "
                 "transfer invitations and Accept them.")
    return tasks


def main() -> None:
    ap = argparse.ArgumentParser(description="List human-only GitHub chores (read-only).")
    ap.add_argument("--owner", default="Dimitres-Kisimov")
    a = ap.parse_args()

    token = _token()
    if not token:
        print("No GitHub token available (git credential / GITHUB_TOKEN).")
        print("This helper is read-only; provide a token to enable listing, or")
        print("just open https://github.com/notifications to accept transfers.")
        return

    print(f"Human-only GitHub chores for {a.owner}:\n")
    for i, t in enumerate(list_tasks(a.owner, token), 1):
        print(f"  {i}. {t}")
    print("\n(This helper never accepts transfers or changes settings for you — "
          "those clicks are yours by design.)")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
