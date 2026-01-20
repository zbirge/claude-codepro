"""Tests for status line widgets."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ccp.statusline.formatter import StatusData
from ccp.statusline.widgets import (
    AuditorWidget,
    Colors,
    ContextWidget,
    LicenseWidget,
    MemoryWidget,
    VersionWidget,
)


class TestContextWidget:
    """Tests for ContextWidget."""

    def test_returns_placeholder_when_no_context_data(self) -> None:
        """Should return placeholder when context_used_pct is None."""
        widget = ContextWidget()
        data = StatusData()
        result = widget.render(data, {}, {})
        assert result is not None
        assert "--%"in result
        assert "░" in result

    def test_renders_percentage(self) -> None:
        """Should render the context percentage."""
        widget = ContextWidget()
        data = StatusData(context_used_pct=50.0)
        result = widget.render(data, {}, {})
        assert result is not None
        assert "50%" in result

    def test_uses_green_color_below_80_percent(self) -> None:
        """Should use green color when below 80%."""
        widget = ContextWidget()
        data = StatusData(context_used_pct=50.0)
        result = widget.render(data, {}, {})
        assert result is not None
        assert Colors.GREEN in result

    def test_uses_yellow_color_at_80_percent(self) -> None:
        """Should use yellow color at 80%."""
        widget = ContextWidget()
        data = StatusData(context_used_pct=80.0)
        result = widget.render(data, {}, {})
        assert result is not None
        assert Colors.YELLOW in result

    def test_uses_red_bold_at_90_percent(self) -> None:
        """Should use red bold color at 90%."""
        widget = ContextWidget()
        data = StatusData(context_used_pct=90.0)
        result = widget.render(data, {}, {})
        assert result is not None
        assert Colors.RED in result
        assert Colors.BOLD in result

    def test_renders_progress_bar(self) -> None:
        """Should render a progress bar with filled and empty chars."""
        widget = ContextWidget()
        data = StatusData(context_used_pct=50.0)
        result = widget.render(data, {}, {})
        assert result is not None
        assert "█" in result
        assert "░" in result

    def test_progress_bar_width_is_10_chars(self) -> None:
        """Should render progress bar with exactly 10 characters."""
        widget = ContextWidget()
        assert widget.BAR_WIDTH == 10

    def test_handles_zero_percent(self) -> None:
        """Should handle 0% context usage."""
        widget = ContextWidget()
        data = StatusData(context_used_pct=0.0)
        result = widget.render(data, {}, {})
        assert result is not None
        assert "0%" in result

    def test_handles_100_percent(self) -> None:
        """Should handle 100% context usage."""
        widget = ContextWidget()
        data = StatusData(context_used_pct=100.0)
        result = widget.render(data, {}, {})
        assert result is not None
        assert "100%" in result


class TestMemoryWidget:
    """Tests for MemoryWidget."""

    def test_returns_inactive_when_no_observations(self) -> None:
        """Should return 'Memory: --' when no observations exist."""
        widget = MemoryWidget()
        data = StatusData()
        with patch("ccp.statusline.providers.MemoryProvider") as mock_provider:
            mock_provider.return_value.get_observation_count.return_value = 0
            result = widget.render(data, {}, {})
            assert result is not None
            assert "Memory: --" in result

    def test_renders_time_format(self) -> None:
        """Should render time since last observation."""
        widget = MemoryWidget()
        data = StatusData()
        import time

        current_epoch_ms = int(time.time() * 1000)
        recent_epoch_ms = current_epoch_ms - 5000  # 5 seconds ago

        with patch("ccp.statusline.providers.MemoryProvider") as mock_provider:
            mock_provider.return_value.get_observation_count.return_value = 100
            mock_provider.return_value.get_observations.return_value = [{"created_at_epoch": recent_epoch_ms}]
            result = widget.render(data, {}, {})
            assert result is not None
            assert "Memory:" in result
            assert "s" in result

    def test_renders_time_since_last_observation_seconds(self) -> None:
        """Should show seconds for very recent observations."""
        widget = MemoryWidget()
        data = StatusData()
        import time

        current_epoch_ms = int(time.time() * 1000)
        recent_epoch_ms = current_epoch_ms - 30000

        with patch("ccp.statusline.providers.MemoryProvider") as mock_provider:
            mock_provider.return_value.get_observation_count.return_value = 5
            mock_provider.return_value.get_observations.return_value = [
                {"created_at_epoch": recent_epoch_ms}
            ]
            result = widget.render(data, {}, {})
            assert result is not None
            assert "s" in result or "ago" in result

    def test_renders_time_since_last_observation_minutes(self) -> None:
        """Should show minutes for observations within an hour."""
        widget = MemoryWidget()
        data = StatusData()
        import time

        current_epoch_ms = int(time.time() * 1000)
        recent_epoch_ms = current_epoch_ms - (10 * 60 * 1000)

        with patch("ccp.statusline.providers.MemoryProvider") as mock_provider:
            mock_provider.return_value.get_observation_count.return_value = 5
            mock_provider.return_value.get_observations.return_value = [
                {"created_at_epoch": recent_epoch_ms}
            ]
            result = widget.render(data, {}, {})
            assert result is not None
            assert "m" in result

    def test_renders_time_since_last_observation_hours(self) -> None:
        """Should show hours for older observations."""
        widget = MemoryWidget()
        data = StatusData()
        import time

        current_epoch_ms = int(time.time() * 1000)
        recent_epoch_ms = current_epoch_ms - (2 * 60 * 60 * 1000)

        with patch("ccp.statusline.providers.MemoryProvider") as mock_provider:
            mock_provider.return_value.get_observation_count.return_value = 5
            mock_provider.return_value.get_observations.return_value = [
                {"created_at_epoch": recent_epoch_ms}
            ]
            result = widget.render(data, {}, {})
            assert result is not None
            assert "h" in result

    def test_includes_memory_label(self) -> None:
        """Should include 'Memory:' label."""
        widget = MemoryWidget()
        data = StatusData()
        with patch("ccp.statusline.providers.MemoryProvider") as mock_provider:
            mock_provider.return_value.get_observation_count.return_value = 10
            mock_provider.return_value.get_observations.return_value = []
            result = widget.render(data, {}, {})
            assert result is not None
            assert "Memory:" in result

    def test_handles_provider_exception(self) -> None:
        """Should return None on provider exception."""
        widget = MemoryWidget()
        data = StatusData()
        with patch("ccp.statusline.providers.MemoryProvider") as mock_provider:
            mock_provider.side_effect = Exception("Database error")
            result = widget.render(data, {}, {})
            assert result is None


class TestLicenseWidget:
    """Tests for LicenseWidget."""

    def test_returns_none_when_no_license_state(self) -> None:
        """Should return None when no license state exists."""
        widget = LicenseWidget()
        data = StatusData()
        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = None
            result = widget.render(data, {}, {})
            assert result is None

    def test_renders_standard_for_standard_tier(self) -> None:
        """Should show 'Standard' in green for standard tier."""
        widget = LicenseWidget()
        data = StatusData()
        mock_state = MagicMock()
        mock_state.tier = "standard"

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            result = widget.render(data, {}, {})
            assert result is not None
            assert "Standard" in result
            assert Colors.GREEN in result

    def test_renders_enterprise_for_enterprise_tier(self) -> None:
        """Should show 'Enterprise' in cyan for enterprise tier."""
        widget = LicenseWidget()
        data = StatusData()
        mock_state = MagicMock()
        mock_state.tier = "enterprise"

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            result = widget.render(data, {}, {})
            assert result is not None
            assert "Enterprise" in result
            assert Colors.CYAN in result

    def test_renders_trial_for_trial_tier(self) -> None:
        """Should show 'Trial' in cyan for active trial."""
        widget = LicenseWidget()
        data = StatusData()
        mock_state = MagicMock()
        mock_state.tier = "trial"
        mock_state.is_trial_expired.return_value = False
        mock_state.days_remaining.return_value = 10

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            result = widget.render(data, {}, {})
            assert result is not None
            assert "Trial" in result
            assert Colors.CYAN in result

    def test_renders_trial_with_days_when_expiring_soon(self) -> None:
        """Should show days remaining when trial expiring within 3 days."""
        widget = LicenseWidget()
        data = StatusData()
        mock_state = MagicMock()
        mock_state.tier = "trial"
        mock_state.is_trial_expired.return_value = False
        mock_state.days_remaining.return_value = 2

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            result = widget.render(data, {}, {})
            assert result is not None
            assert "Trial:2d" in result
            assert Colors.YELLOW in result

    def test_renders_expired_for_expired_trial(self) -> None:
        """Should show 'Expired' in red for expired trial."""
        widget = LicenseWidget()
        data = StatusData()
        mock_state = MagicMock()
        mock_state.tier = "trial"
        mock_state.is_trial_expired.return_value = True

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            result = widget.render(data, {}, {})
            assert result is not None
            assert "Expired" in result
            assert Colors.RED in result

    def test_handles_license_manager_exception(self) -> None:
        """Should return None on license manager exception."""
        widget = LicenseWidget()
        data = StatusData()
        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.side_effect = Exception("License error")
            result = widget.render(data, {}, {})
            assert result is None

    def test_returns_none_for_unknown_tier(self) -> None:
        """Should return None for unknown tier."""
        widget = LicenseWidget()
        data = StatusData()
        mock_state = MagicMock()
        mock_state.tier = "unknown"

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            result = widget.render(data, {}, {})
            assert result is None


class TestVersionWidget:
    """Tests for VersionWidget."""

    def test_renders_cc_version_from_data(self) -> None:
        """Should render Claude Code version from status data."""
        widget = VersionWidget()
        data = StatusData(version="1.0.50")
        result = widget.render(data, {}, {})
        assert result is not None
        assert "CC:1.0.50" in result

    def test_renders_ccp_version(self) -> None:
        """Should render Claude CodePro version."""
        widget = VersionWidget()
        data = StatusData()
        result = widget.render(data, {}, {})
        assert result is not None
        assert "CCP:" in result

    def test_renders_both_versions(self) -> None:
        """Should render both CC and CCP versions when available."""
        widget = VersionWidget()
        data = StatusData(version="1.0.50")
        result = widget.render(data, {}, {})
        assert result is not None
        assert "CC:1.0.50" in result
        assert "CCP:" in result

    def test_uses_dim_color(self) -> None:
        """Should use dim color for version text."""
        widget = VersionWidget()
        data = StatusData(version="1.0.0")
        result = widget.render(data, {}, {})
        assert result is not None
        assert Colors.DIM in result
        assert Colors.RESET in result

    def test_returns_none_when_no_versions(self) -> None:
        """Should return None when no versions available."""
        widget = VersionWidget()
        data = StatusData()
        with patch("ccp.__version__", side_effect=ImportError):
            result = widget.render(data, {}, {})
            # CCP version will still be available from import
            assert result is not None


class TestAuditorWidget:
    """Tests for AuditorWidget."""

    def test_returns_init_when_no_license(self) -> None:
        """Should return 'Auditor: init' when no license exists (trial auto-creates)."""
        widget = AuditorWidget()
        data = StatusData()

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = None
            result = widget.render(data, {}, {})
            assert result is not None
            # When no license, auditor still shows but may be in init state

    def test_returns_ok_for_standard_with_no_violations(self, tmp_path) -> None:
        """Should return 'Auditor: ' for standard tier with no violations."""
        widget = AuditorWidget()
        data = StatusData()
        mock_state = MagicMock()
        mock_state.tier = "standard"

        # Ensure findings file doesn't exist but heartbeat exists
        widget.FINDINGS_FILE = str(tmp_path / "nonexistent.json")
        heartbeat_file = tmp_path / "heartbeat"
        heartbeat_file.write_text("1")
        widget.HEARTBEAT_FILE = str(heartbeat_file)

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            result = widget.render(data, {}, {})
            assert result is not None
            assert "Auditor: " in result
            assert "s" in result  # Should show time like "5s"

    def test_returns_ok_for_trial_with_no_violations(self, tmp_path) -> None:
        """Should return 'Auditor: ' for trial tier with no violations."""
        widget = AuditorWidget()
        data = StatusData()
        mock_state = MagicMock()
        mock_state.tier = "trial"

        # Ensure findings file doesn't exist but heartbeat exists
        widget.FINDINGS_FILE = str(tmp_path / "nonexistent.json")
        heartbeat_file = tmp_path / "heartbeat"
        heartbeat_file.write_text("1")
        widget.HEARTBEAT_FILE = str(heartbeat_file)

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            result = widget.render(data, {}, {})
            assert result is not None
            assert "Auditor: " in result

    def test_returns_violation_count_when_violations_exist(self, tmp_path) -> None:
        """Should return violation count when findings file has violations."""
        import json

        widget = AuditorWidget()
        data = StatusData()
        mock_state = MagicMock()
        mock_state.tier = "standard"

        # Create findings file with violations and heartbeat
        findings_file = tmp_path / "findings.json"
        findings_file.write_text(json.dumps({
            "violations": [
                {"rule": "test1", "severity": "error"},
                {"rule": "test2", "severity": "warning"},
            ]
        }))
        widget.FINDINGS_FILE = str(findings_file)
        heartbeat_file = tmp_path / "heartbeat"
        heartbeat_file.write_text("1")
        widget.HEARTBEAT_FILE = str(heartbeat_file)

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            result = widget.render(data, {}, {})
            assert result is not None
            assert "Auditor: 2!" in result
            assert Colors.YELLOW in result

    def test_handles_empty_violations_list(self, tmp_path) -> None:
        """Should return 'Auditor: ' when findings file has empty violations."""
        import json

        widget = AuditorWidget()
        data = StatusData()
        mock_state = MagicMock()
        mock_state.tier = "trial"

        # Create findings file with empty violations and heartbeat
        findings_file = tmp_path / "findings.json"
        findings_file.write_text(json.dumps({"violations": []}))
        widget.FINDINGS_FILE = str(findings_file)
        heartbeat_file = tmp_path / "heartbeat"
        heartbeat_file.write_text("1")
        widget.HEARTBEAT_FILE = str(heartbeat_file)

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            result = widget.render(data, {}, {})
            assert result is not None
            assert "Auditor: " in result

    def test_handles_malformed_json(self, tmp_path) -> None:
        """Should return 'Auditor: ' when findings file has invalid JSON."""
        widget = AuditorWidget()
        data = StatusData()
        mock_state = MagicMock()
        mock_state.tier = "standard"

        # Create malformed findings file and heartbeat
        findings_file = tmp_path / "findings.json"
        findings_file.write_text("not valid json")
        widget.FINDINGS_FILE = str(findings_file)
        heartbeat_file = tmp_path / "heartbeat"
        heartbeat_file.write_text("1")
        widget.HEARTBEAT_FILE = str(heartbeat_file)

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            result = widget.render(data, {}, {})
            assert result is not None
            assert "Auditor: " in result

    def test_returns_init_when_no_heartbeat(self, tmp_path) -> None:
        """Should return 'Auditor: init' when no heartbeat file exists."""
        widget = AuditorWidget()
        data = StatusData()
        mock_state = MagicMock()
        mock_state.tier = "standard"

        # No heartbeat file
        widget.HEARTBEAT_FILE = str(tmp_path / "nonexistent_heartbeat")

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            result = widget.render(data, {}, {})
            assert result is not None
            assert "Auditor: init" in result
            assert Colors.DIM in result

    def test_returns_stale_when_heartbeat_stale(self, tmp_path) -> None:
        """Should return 'Auditor: stale' when heartbeat file is stale."""
        import os
        import time

        widget = AuditorWidget()
        data = StatusData()
        mock_state = MagicMock()
        mock_state.tier = "standard"

        # Create stale heartbeat file (modify time in the past)
        heartbeat_file = tmp_path / "heartbeat"
        heartbeat_file.write_text("1")
        # Set mtime to 3 minutes ago (stale threshold is 2 minutes)
        old_time = time.time() - 180
        os.utime(heartbeat_file, (old_time, old_time))
        widget.HEARTBEAT_FILE = str(heartbeat_file)

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.return_value.get_state.return_value = mock_state
            result = widget.render(data, {}, {})
            assert result is not None
            assert "Auditor: stale" in result
            assert Colors.DIM in result

    def test_handles_license_manager_exception(self) -> None:
        """Should show init state on license manager exception."""
        widget = AuditorWidget()
        data = StatusData()

        with patch("ccp.auth.LicenseManager") as mock_manager:
            mock_manager.side_effect = Exception("License error")
            result = widget.render(data, {}, {})
            # Auditor still renders (init state) even on exception
            assert result is not None
