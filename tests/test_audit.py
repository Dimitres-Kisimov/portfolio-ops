"""Tests for the audit + rank engines. No network, no other repos touched —
we build a tiny throwaway repo in a tmp dir and audit that."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ops import audit, rank


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), check=True,
                   capture_output=True, text=True)


@pytest.fixture()
def tiny_repo(tmp_path: Path) -> Path:
    r = tmp_path / "demo-repo"
    r.mkdir()
    (r / "README.md").write_text("# demo\n", encoding="utf-8")
    (r / "mod.py").write_text("x = 1\n", encoding="utf-8")
    try:
        _git(r, "init", "-q")
        _git(r, "add", "-A")
        _git(r, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init")
    except Exception:
        pytest.skip("git not available")
    return r


def test_audit_repo_scores_and_finds_gaps(tiny_repo: Path):
    card = audit.audit_repo(tiny_repo, run_tests=False)
    assert card["exists"] is True
    assert card["artifacts"]["readme"] is True
    assert card["artifacts"]["license"] is False
    # no remote -> should be flagged
    assert any("remote" in g for g in card["gaps"])
    assert 0 <= card["score"] <= 100


def test_audit_missing_repo(tmp_path: Path):
    card = audit.audit_repo(tmp_path / "nope", run_tests=False)
    assert card["exists"] is False


def test_score_monotonic_with_artifacts(tiny_repo: Path):
    low = audit.audit_repo(tiny_repo, run_tests=False)["score"]
    (tiny_repo / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (tiny_repo / "tests").mkdir()
    high = audit.audit_repo(tiny_repo, run_tests=False)["score"]
    assert high >= low


def test_rank_orders_by_priority(tmp_path: Path):
    import json
    (tmp_path / "a.json").write_text(json.dumps(
        {"repo": "a", "gaps": ["missing license", "2 unpushed commit(s)"]}),
        encoding="utf-8")
    ranked = rank.rank(tmp_path)
    assert ranked[0]["gap"].endswith("unpushed commit(s)")  # highest weight first
    assert ranked[-1]["gap"] == "missing license"


def test_weight_lookup_defaults():
    w, why = rank._weight("some unknown gap")
    assert w == 10
    assert isinstance(why, str)
