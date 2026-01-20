"""Tests for status line formatter."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from ccp.statusline.formatter import (
    Colors,
    StatusData,
    format_status_line,
    get_support_message,
    get_token_metrics,
)


class TestStatusData:
    """Tests for StatusData dataclass."""

    def test_from_json_parses_basic_fields(self) -> None:
        """Should parse basic fields from JSON."""
        data = {
            "session_id": "test-session-123",
            "transcript_path": "/path/to/transcript.jsonl",
            "cwd": "/workspace",
            "version": "1.0.0",
        }
        result = StatusData.from_json(data)
        assert result.session_id == "test-session-123"
        assert result.transcript_path == "/path/to/transcript.jsonl"
        assert result.cwd == "/workspace"
        assert result.version == "1.0.0"

    def test_from_json_parses_model_info(self) -> None:
        """Should parse model information from nested object."""
        data = {
            "model": {
                "id": "claude-sonnet-4-20250514",
                "display_name": "Claude Sonnet 4",
            }
        }
        result = StatusData.from_json(data)
        assert result.model_id == "claude-sonnet-4-20250514"
        assert result.model_display_name == "Claude Sonnet 4"

    def test_from_json_parses_context_window(self) -> None:
        """Should parse context window information."""
        data = {
            "context_window": {
                "used_percentage": 45.5,
                "remaining_percentage": 54.5,
                "context_window_size": 200000,
                "total_input_tokens": 50000,
                "total_output_tokens": 10000,
            }
        }
        result = StatusData.from_json(data)
        assert result.context_used_pct == 45.5
        assert result.context_remaining_pct == 54.5
        assert result.context_window_size == 200000
        assert result.total_input_tokens == 50000
        assert result.total_output_tokens == 10000

    def test_from_json_parses_cost(self) -> None:
        """Should parse cost information."""
        data = {"cost": {"total_cost_usd": 0.15}}
        result = StatusData.from_json(data)
        assert result.cost_usd == 0.15

    def test_from_json_parses_workspace_cwd(self) -> None:
        """Should prefer workspace.current_dir over cwd."""
        data = {
            "cwd": "/old/path",
            "workspace": {"current_dir": "/new/path"},
        }
        result = StatusData.from_json(data)
        assert result.cwd == "/new/path"

    def test_from_json_handles_empty_data(self) -> None:
        """Should handle empty JSON data gracefully."""
        result = StatusData.from_json({})
        assert result.session_id is None
        assert result.context_used_pct is None
        assert result.cost_usd is None

    def test_from_json_handles_none_nested_objects(self) -> None:
        """Should handle None values for nested objects."""
        data = {
            "model": None,
            "cost": None,
            "context_window": None,
            "workspace": None,
        }
        result = StatusData.from_json(data)
        assert result.model_id is None
        assert result.cost_usd is None
        assert result.context_used_pct is None


class TestGetTokenMetrics:
    """Tests for get_token_metrics function."""

    def test_returns_default_metrics_for_missing_file(self) -> None:
        """Should return zeroed metrics when file doesn't exist."""
        metrics = get_token_metrics("/nonexistent/path.jsonl")
        assert metrics["input_tokens"] == 0
        assert metrics["output_tokens"] == 0
        assert metrics["cached_tokens"] == 0
        assert metrics["context_length"] == 0

    def test_parses_token_usage_from_jsonl(self, tmp_path: Path) -> None:
        """Should sum token usage from JSONL entries."""
        transcript = tmp_path / "transcript.jsonl"
        entries = [
            {
                "message": {
                    "usage": {
                        "input_tokens": 100,
                        "output_tokens": 50,
                        "cache_read_input_tokens": 20,
                    }
                }
            },
            {
                "message": {
                    "usage": {
                        "input_tokens": 200,
                        "output_tokens": 75,
                        "cache_creation_input_tokens": 30,
                    }
                }
            },
        ]
        transcript.write_text("\n".join(json.dumps(e) for e in entries))

        metrics = get_token_metrics(str(transcript))
        assert metrics["input_tokens"] == 300
        assert metrics["output_tokens"] == 125
        assert metrics["cached_tokens"] == 50

    def test_excludes_sidechain_from_context_length(self, tmp_path: Path) -> None:
        """Should exclude sidechain messages from context length calculation."""
        transcript = tmp_path / "transcript.jsonl"
        entries = [
            {"message": {"usage": {"input_tokens": 100}}, "isSidechain": False},
            {"message": {"usage": {"input_tokens": 500}}, "isSidechain": True},
            {"message": {"usage": {"input_tokens": 200}}, "isSidechain": False},
        ]
        transcript.write_text("\n".join(json.dumps(e) for e in entries))

        metrics = get_token_metrics(str(transcript))
        assert metrics["context_length"] == 200

    def test_excludes_api_errors_from_context_length(self, tmp_path: Path) -> None:
        """Should exclude API error messages from context length."""
        transcript = tmp_path / "transcript.jsonl"
        entries = [
            {"message": {"usage": {"input_tokens": 100}}, "isApiErrorMessage": False},
            {"message": {"usage": {"input_tokens": 999}}, "isApiErrorMessage": True},
        ]
        transcript.write_text("\n".join(json.dumps(e) for e in entries))

        metrics = get_token_metrics(str(transcript))
        assert metrics["context_length"] == 100

    def test_handles_invalid_json_lines(self, tmp_path: Path) -> None:
        """Should skip invalid JSON lines gracefully."""
        transcript = tmp_path / "transcript.jsonl"
        content = '{"message": {"usage": {"input_tokens": 100}}}\nnot valid json\n{"message": {"usage": {"input_tokens": 50}}}'
        transcript.write_text(content)

        metrics = get_token_metrics(str(transcript))
        assert metrics["input_tokens"] == 150

    def test_handles_empty_file(self, tmp_path: Path) -> None:
        """Should return zeroed metrics for empty file."""
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text("")

        metrics = get_token_metrics(str(transcript))
        assert metrics["input_tokens"] == 0


class TestGetSupportMessage:
    """Tests for get_support_message function."""

    def test_returns_thanks_message_for_standard(self) -> None:
        """Should return thanks message for standard license."""
        from unittest.mock import MagicMock, patch

        mock_state = MagicMock()
        mock_state.tier = "standard"

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            data = StatusData(version="1.0.0")
            msg = get_support_message(data)
            assert msg is not None
            assert "Standard" in msg

    def test_returns_trial_message_for_trial(self) -> None:
        """Should return trial message for trial tier."""
        from unittest.mock import MagicMock, patch

        mock_state = MagicMock()
        mock_state.tier = "trial"
        mock_state.days_remaining.return_value = None

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            data = StatusData()
            msg = get_support_message(data)
            assert msg is not None
            assert "Trial" in msg

    def test_returns_trial_message_with_days(self) -> None:
        """Should return trial message with days remaining."""
        from unittest.mock import MagicMock, patch

        mock_state = MagicMock()
        mock_state.tier = "trial"
        mock_state.days_remaining.return_value = 5

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            data = StatusData()
            msg = get_support_message(data)
            assert msg is not None
            assert "Trial" in msg
            assert "5d" in msg
            assert "license.claude-code.pro" in msg

    def test_message_contains_version_info(self) -> None:
        """Should include CCP and CC version info."""
        from unittest.mock import MagicMock, patch

        mock_state = MagicMock()
        mock_state.tier = "trial"

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            data = StatusData(version="1.0.50")
            msg = get_support_message(data)
            assert msg is not None
            assert "CCP:" in msg
            assert "CC:1.0.50" in msg

    def test_ccp_version_comes_first(self) -> None:
        """Should show CCP version before CC version."""
        from unittest.mock import MagicMock, patch

        mock_state = MagicMock()
        mock_state.tier = "trial"

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            data = StatusData(version="1.0.50")
            msg = get_support_message(data)
            assert msg is not None
            ccp_pos = msg.find("CCP:")
            cc_pos = msg.find("CC:")
            assert ccp_pos < cc_pos

    def test_message_uses_non_breaking_spaces(self) -> None:
        """Should replace spaces with non-breaking spaces."""
        from unittest.mock import MagicMock, patch

        mock_state = MagicMock()
        mock_state.tier = "trial"

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            data = StatusData()
            msg = get_support_message(data)
            assert msg is not None
            assert " " not in msg
            assert "\u00a0" in msg

    def test_returns_none_on_exception(self) -> None:
        """Should return None when license manager throws."""
        from unittest.mock import patch

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.side_effect = Exception("License error")
            data = StatusData()
            msg = get_support_message(data)
            assert msg is None


class TestFormatStatusLine:
    """Tests for format_status_line function."""

    def test_includes_support_message_when_no_context(self) -> None:
        """Should include support message even when no context data."""
        from unittest.mock import MagicMock, patch

        mock_state = MagicMock()
        mock_state.tier = "trial"
        mock_state.days_remaining.return_value = 5

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            data = StatusData()
            result = format_status_line(data)
            assert "\n" in result
            assert "Trial" in result
            assert "license.claude-code.pro" in result

    def test_includes_context_widget_output(self) -> None:
        """Should include context percentage when available."""
        data = StatusData(context_used_pct=50.0)
        result = format_status_line(data)
        assert "50%" in result

    def test_uses_pipe_separator(self) -> None:
        """Should separate widgets with pipe character."""
        data = StatusData(context_used_pct=50.0)
        result = format_status_line(data)
        assert "|" in result

    def test_prefixes_with_reset_code(self) -> None:
        """Should prefix output with ANSI reset code."""
        data = StatusData(context_used_pct=50.0)
        result = format_status_line(data)
        assert result.startswith("\033[0m")

    def test_replaces_spaces_with_non_breaking(self) -> None:
        """Should replace spaces with non-breaking spaces."""
        data = StatusData(context_used_pct=50.0)
        result = format_status_line(data)
        assert " " not in result
        assert "\u00a0" in result

    def test_includes_trial_message_on_third_line_for_trial(self) -> None:
        """Should include trial message on third line for trial tier."""
        from unittest.mock import MagicMock, patch

        mock_state = MagicMock()
        mock_state.tier = "trial"
        mock_state.days_remaining.return_value = 5

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            data = StatusData(context_used_pct=50.0)
            result = format_status_line(data)
            lines = result.split("\n")
            assert len(lines) == 3
            assert "Trial" in lines[2]
            assert "license.claude-code.pro" in lines[2]

    def test_includes_tier_message_on_third_line_for_standard(self) -> None:
        """Should include tier message on third line for standard tier."""
        from unittest.mock import MagicMock, patch

        mock_state = MagicMock()
        mock_state.tier = "standard"

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            data = StatusData(context_used_pct=50.0)
            result = format_status_line(data)
            lines = result.split("\n")
            assert len(lines) == 3
            assert "Standard" in lines[2]

    def test_includes_mode_on_second_line(self) -> None:
        """Should include mode (Quick/Spec) on second line."""
        data = StatusData(context_used_pct=50.0)
        result = format_status_line(data)
        lines = result.split("\n")
        assert len(lines) == 3
        # Either "Quick Mode" or "Spec:" depending on active plan
        assert "Mode" in lines[1] or "Spec:" in lines[1]
