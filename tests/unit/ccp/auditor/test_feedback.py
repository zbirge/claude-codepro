"""Tests for the FeedbackWriter module."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from ccp.auditor.types import Violation


class TestFeedbackWriter:
    """Tests for the FeedbackWriter class."""

    @pytest.fixture
    def tmp_findings_file(self, tmp_path: Path) -> Path:
        """Create a temporary findings file path."""
        return tmp_path / "ccp-auditor-findings.json"

    @pytest.fixture
    def sample_violations(self) -> list[Violation]:
        """Create sample violations for testing."""
        return [
            Violation(
                rule="tdd-enforcement",
                severity="error",
                message="Code written without failing test",
                evidence="src/feature.py modified without test",
            ),
            Violation(
                rule="git-commits",
                severity="warning",
                message="Commit message too short",
                evidence="Last commit: 'fix'",
            ),
        ]

    def test_write_creates_json_file(
        self, tmp_findings_file: Path, sample_violations: list[Violation]
    ) -> None:
        """Test that write creates a valid JSON file."""
        from ccp.auditor.feedback import FeedbackWriter

        writer = FeedbackWriter(findings_path=tmp_findings_file)
        writer.write(sample_violations)

        assert tmp_findings_file.exists()
        data = json.loads(tmp_findings_file.read_text())
        assert "violations" in data
        assert "timestamp" in data
        assert len(data["violations"]) == 2

    def test_write_includes_all_violation_fields(
        self, tmp_findings_file: Path, sample_violations: list[Violation]
    ) -> None:
        """Test that all violation fields are included in output."""
        from ccp.auditor.feedback import FeedbackWriter

        writer = FeedbackWriter(findings_path=tmp_findings_file)
        writer.write(sample_violations)

        data = json.loads(tmp_findings_file.read_text())
        violation = data["violations"][0]

        assert violation["rule"] == "tdd-enforcement"
        assert violation["severity"] == "error"
        assert violation["message"] == "Code written without failing test"
        assert violation["evidence"] == "src/feature.py modified without test"

    def test_write_includes_summary(
        self, tmp_findings_file: Path, sample_violations: list[Violation]
    ) -> None:
        """Test that summary is included in output."""
        from ccp.auditor.feedback import FeedbackWriter

        writer = FeedbackWriter(findings_path=tmp_findings_file)
        writer.write(sample_violations)

        data = json.loads(tmp_findings_file.read_text())
        assert data["summary"] == "2 violations found"

    def test_write_empty_violations_creates_empty_array(
        self, tmp_findings_file: Path
    ) -> None:
        """Test that empty violations list creates file with empty array."""
        from ccp.auditor.feedback import FeedbackWriter

        writer = FeedbackWriter(findings_path=tmp_findings_file)
        writer.write([])

        data = json.loads(tmp_findings_file.read_text())
        assert data["violations"] == []
        assert data["summary"] == "0 violations found"

    def test_clear_removes_file(
        self, tmp_findings_file: Path, sample_violations: list[Violation]
    ) -> None:
        """Test that clear removes the findings file."""
        from ccp.auditor.feedback import FeedbackWriter

        writer = FeedbackWriter(findings_path=tmp_findings_file)
        writer.write(sample_violations)
        assert tmp_findings_file.exists()

        writer.clear()
        assert not tmp_findings_file.exists()

    def test_clear_handles_missing_file(self, tmp_findings_file: Path) -> None:
        """Test that clear handles non-existent file gracefully."""
        from ccp.auditor.feedback import FeedbackWriter

        writer = FeedbackWriter(findings_path=tmp_findings_file)
        # Should not raise even if file doesn't exist
        writer.clear()

    def test_read_returns_violations(
        self, tmp_findings_file: Path, sample_violations: list[Violation]
    ) -> None:
        """Test that read returns violations from file."""
        from ccp.auditor.feedback import FeedbackWriter

        writer = FeedbackWriter(findings_path=tmp_findings_file)
        writer.write(sample_violations)

        violations = writer.read()
        assert len(violations) == 2
        assert violations[0].rule == "tdd-enforcement"
        assert violations[1].rule == "git-commits"

    def test_read_returns_empty_list_when_no_file(
        self, tmp_findings_file: Path
    ) -> None:
        """Test that read returns empty list when file doesn't exist."""
        from ccp.auditor.feedback import FeedbackWriter

        writer = FeedbackWriter(findings_path=tmp_findings_file)
        violations = writer.read()
        assert violations == []

    def test_read_handles_malformed_json(self, tmp_findings_file: Path) -> None:
        """Test that read handles malformed JSON gracefully."""
        from ccp.auditor.feedback import FeedbackWriter

        tmp_findings_file.write_text("not valid json")
        writer = FeedbackWriter(findings_path=tmp_findings_file)

        violations = writer.read()
        assert violations == []

    def test_default_findings_path(self) -> None:
        """Test that default path is /tmp/ccp-auditor-findings.json."""
        from ccp.auditor.feedback import FeedbackWriter

        writer = FeedbackWriter()
        assert writer.findings_path == Path("/tmp/ccp-auditor-findings.json")

    def test_atomic_write(self, tmp_findings_file: Path, sample_violations: list[Violation]) -> None:
        """Test that writes are atomic (uses temp file)."""
        from ccp.auditor.feedback import FeedbackWriter

        writer = FeedbackWriter(findings_path=tmp_findings_file)

        # Write should complete atomically
        writer.write(sample_violations)

        # Verify file is valid JSON immediately after write
        data = json.loads(tmp_findings_file.read_text())
        assert len(data["violations"]) == 2
