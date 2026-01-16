"""Unit tests for migrated helper module."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest


class TestMigratedHelperContextFunctions:
    """Tests for context monitoring functions."""

    def test_get_context_percentage_returns_float(self, tmp_path: Path) -> None:
        """get_context_percentage returns a float percentage."""
        from ccp.helper import get_context_percentage

        # Create mock session file with usage data
        session_id = "test-session-123"
        history_file = tmp_path / ".claude" / "history.jsonl"
        history_file.parent.mkdir(parents=True)
        history_file.write_text(json.dumps({"sessionId": session_id}) + "\n")

        projects_dir = tmp_path / ".claude" / "projects" / "test-project"
        projects_dir.mkdir(parents=True)
        session_file = projects_dir / f"{session_id}.jsonl"

        # Write assistant message with usage data (100k tokens = 50%)
        usage_data = {
            "type": "assistant",
            "message": {
                "usage": {
                    "input_tokens": 50000,
                    "cache_creation_input_tokens": 25000,
                    "cache_read_input_tokens": 25000,
                }
            },
        }
        session_file.write_text(json.dumps(usage_data) + "\n")

        with patch.object(Path, "home", return_value=tmp_path):
            percentage = get_context_percentage()

        assert isinstance(percentage, float)
        assert 49.0 <= percentage <= 51.0  # ~50%

    def test_check_context_returns_ok_below_threshold(self) -> None:
        """check_context returns 'OK' when below threshold."""
        from ccp.helper import check_context

        with patch("ccp.helper.get_context_percentage", return_value=50.0):
            result = check_context(threshold=95)

        assert result == "OK"

    def test_check_context_returns_clear_needed_above_threshold(self) -> None:
        """check_context returns 'CLEAR_NEEDED' when above threshold."""
        from ccp.helper import check_context

        with patch("ccp.helper.get_context_percentage", return_value=96.0):
            result = check_context(threshold=95)

        assert result == "CLEAR_NEEDED"


class TestMigratedHelperSendClear:
    """Tests for send_clear function."""

    def test_send_clear_returns_false_without_pipe(self) -> None:
        """send_clear returns False when WRAPPER_PIPE not set."""
        from ccp.helper import send_clear

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("WRAPPER_PIPE", None)
            result = send_clear()

        assert result is False

    def test_send_clear_returns_false_when_pipe_missing(self, tmp_path: Path) -> None:
        """send_clear returns False when pipe file doesn't exist."""
        from ccp.helper import send_clear

        with patch.dict(os.environ, {"WRAPPER_PIPE": str(tmp_path / "nonexistent.pipe")}):
            result = send_clear()

        assert result is False


class TestMigratedHelperCLI:
    """Tests for CLI interface."""

    def test_cli_check_context_output(self) -> None:
        """CLI check-context prints OK or CLEAR_NEEDED."""
        from ccp.helper import cli_check_context

        with patch("ccp.helper.get_context_percentage", return_value=50.0):
            result = cli_check_context(json_output=False)

        assert result == "OK"

    def test_cli_check_context_json_output(self) -> None:
        """CLI check-context --json prints JSON."""
        from ccp.helper import cli_check_context

        with patch("ccp.helper.get_context_percentage", return_value=50.0):
            result = cli_check_context(json_output=True)

        data = json.loads(result)
        assert data["status"] == "OK"
        assert data["percentage"] == 50.0
