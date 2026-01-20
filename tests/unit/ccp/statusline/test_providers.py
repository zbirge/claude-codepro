"""Tests for status line providers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ccp.statusline.providers import MemoryProvider


class TestMemoryProvider:
    """Tests for MemoryProvider."""

    @pytest.fixture
    def mock_db(self, tmp_path: Path) -> Path:
        """Create a mock SQLite database with test observations."""
        db_path = tmp_path / "claude-mem.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                title TEXT,
                created_at TEXT NOT NULL,
                created_at_epoch INTEGER NOT NULL
            )
        """)
        test_obs = [
            ("discovery", "Test observation 1", "2026-01-19T10:00:00", 1737280800000),
            ("decision", "Test decision", "2026-01-19T11:00:00", 1737284400000),
            ("bugfix", "Fixed a bug", "2026-01-19T12:00:00", 1737288000000),
        ]
        cursor.executemany(
            "INSERT INTO observations (type, title, created_at, created_at_epoch) VALUES (?, ?, ?, ?)",
            test_obs,
        )
        conn.commit()
        conn.close()
        return db_path

    def test_get_observations_returns_list(self, mock_db: Path) -> None:
        """Should return a list of observations."""
        provider = MemoryProvider(db_path=mock_db)
        observations = provider.get_observations()
        assert isinstance(observations, list)
        assert len(observations) == 3

    def test_get_observations_with_limit(self, mock_db: Path) -> None:
        """Should respect the limit parameter."""
        provider = MemoryProvider(db_path=mock_db)
        observations = provider.get_observations(limit=2)
        assert len(observations) == 2

    def test_get_observations_ordered_by_time_desc(self, mock_db: Path) -> None:
        """Should return observations ordered by time descending."""
        provider = MemoryProvider(db_path=mock_db)
        observations = provider.get_observations()
        epochs = [o["created_at_epoch"] for o in observations]
        assert epochs == sorted(epochs, reverse=True)

    def test_get_observation_count(self, mock_db: Path) -> None:
        """Should return total count of observations."""
        provider = MemoryProvider(db_path=mock_db)
        count = provider.get_observation_count()
        assert count == 3

    def test_handles_missing_database(self, tmp_path: Path) -> None:
        """Should return empty list if database doesn't exist."""
        provider = MemoryProvider(db_path=tmp_path / "nonexistent.db")
        observations = provider.get_observations()
        assert observations == []
        assert provider.get_observation_count() == 0

    def test_observation_contains_expected_fields(self, mock_db: Path) -> None:
        """Should include expected fields in observation dict."""
        provider = MemoryProvider(db_path=mock_db)
        observations = provider.get_observations(limit=1)
        assert len(observations) == 1
        obs = observations[0]
        assert "id" in obs
        assert "type" in obs
        assert "title" in obs
        assert "created_at" in obs
        assert "created_at_epoch" in obs

    def test_uses_default_db_path_when_none_provided(self) -> None:
        """Should use default database path when none provided."""
        provider = MemoryProvider()
        expected_path = Path.home() / ".claude-mem" / "claude-mem.db"
        assert provider.db_path == expected_path

    def test_handles_corrupted_database(self, tmp_path: Path) -> None:
        """Should handle corrupted database gracefully."""
        db_path = tmp_path / "corrupted.db"
        db_path.write_text("not a valid sqlite database")

        provider = MemoryProvider(db_path=db_path)
        observations = provider.get_observations()
        assert observations == []
        assert provider.get_observation_count() == 0
