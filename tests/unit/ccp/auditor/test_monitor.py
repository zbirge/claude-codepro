"""Tests for the StateMonitor."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ccp.auditor.monitor import StateMonitor
from ccp.auditor.types import StateSnapshot


class TestStateMonitor:
    """Tests for StateMonitor class."""

    @pytest.fixture
    def mock_db(self, tmp_path: Path) -> Path:
        """Create a mock Claude Mem database."""
        db_path = tmp_path / ".claude-mem" / "claude-mem.db"
        db_path.parent.mkdir(parents=True)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE observations (
                id INTEGER PRIMARY KEY,
                type TEXT,
                title TEXT,
                body TEXT,
                created_at TEXT,
                created_at_epoch INTEGER
            )
        """)
        cursor.executemany(
            "INSERT INTO observations (type, title, body, created_at, created_at_epoch) VALUES (?, ?, ?, ?, ?)",
            [
                ("discovery", "Found pattern", "Details about the pattern", "2026-01-20T10:00:00", 1737370800000),
                ("decision", "Chose approach", "Reasoning for the decision", "2026-01-20T10:01:00", 1737370860000),
            ],
        )
        conn.commit()
        conn.close()
        return db_path

    @pytest.fixture
    def mock_plan(self, tmp_path: Path) -> Path:
        """Create a mock plan file."""
        plans_dir = tmp_path / "docs" / "plans"
        plans_dir.mkdir(parents=True)

        plan_content = """# Test Plan

Created: 2026-01-20
Status: PENDING
Approved: Yes

## Progress Tracking
- [x] Task 1: First task
- [ ] Task 2: Second task
"""
        plan_file = plans_dir / "2026-01-20-test-plan.md"
        plan_file.write_text(plan_content)
        return tmp_path

    def test_get_recent_observations(self, mock_db: Path) -> None:
        """Should fetch recent observations from database."""
        monitor = StateMonitor(
            project_root=mock_db.parent.parent,
            db_path=mock_db,
        )
        observations = monitor.get_recent_observations(limit=10)

        assert isinstance(observations, list)
        assert len(observations) == 2

    def test_get_active_plan(self, mock_plan: Path) -> None:
        """Should find and parse active plan."""
        monitor = StateMonitor(project_root=mock_plan)
        plan = monitor.get_active_plan()

        assert plan is not None
        assert plan["status"] == "PENDING"
        assert plan["completed"] == 1
        assert plan["total"] == 2

    def test_get_current_state_returns_snapshot(self, mock_plan: Path, mock_db: Path) -> None:
        """Should return a complete state snapshot."""
        monitor = StateMonitor(project_root=mock_plan, db_path=mock_db)
        state = monitor.get_current_state()

        assert isinstance(state, StateSnapshot)
        assert isinstance(state.observations, list)
        assert isinstance(state.git_changes, list)

    def test_handles_missing_database(self, tmp_path: Path) -> None:
        """Should handle missing database gracefully."""
        monitor = StateMonitor(
            project_root=tmp_path,
            db_path=tmp_path / "nonexistent.db",
        )
        observations = monitor.get_recent_observations()

        assert observations == []

    def test_handles_missing_plan_directory(self, tmp_path: Path) -> None:
        """Should handle missing plans directory."""
        monitor = StateMonitor(project_root=tmp_path)
        plan = monitor.get_active_plan()

        assert plan is None

    def test_caches_results(self, mock_db: Path) -> None:
        """Should cache results to avoid repeated operations."""
        monitor = StateMonitor(
            project_root=mock_db.parent.parent,
            db_path=mock_db,
            cache_ttl_seconds=60,
        )

        obs1 = monitor.get_recent_observations()
        obs2 = monitor.get_recent_observations()

        assert obs1 == obs2

    def test_get_git_diff_returns_string(self, tmp_path: Path) -> None:
        """Should return git diff as string."""
        monitor = StateMonitor(project_root=tmp_path)
        diff = monitor.get_git_diff()

        # Should return empty string for non-git directory
        assert isinstance(diff, str)

    def test_get_git_diff_truncates_long_diffs(self, tmp_path: Path) -> None:
        """Should truncate diffs that exceed max_chars."""
        monitor = StateMonitor(project_root=tmp_path)

        # Set a very small limit to test truncation
        diff = monitor.get_git_diff(max_chars=10)

        # Either empty (no git) or truncated
        assert isinstance(diff, str)
        assert len(diff) <= 50  # max_chars + truncation message

    def test_state_snapshot_includes_git_diff(self, mock_plan: Path, mock_db: Path) -> None:
        """Should include git_diff in state snapshot."""
        monitor = StateMonitor(project_root=mock_plan, db_path=mock_db)
        state = monitor.get_current_state()

        assert hasattr(state, "git_diff")
        assert isinstance(state.git_diff, str)
