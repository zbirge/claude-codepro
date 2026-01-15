"""Tests for platform utilities module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPlatformDetection:
    """Test platform detection functions."""

    def test_is_macos_returns_bool(self):
        """is_macos returns boolean."""
        from installer.platform_utils import is_macos

        result = is_macos()
        assert isinstance(result, bool)

    def test_is_linux_returns_bool(self):
        """is_linux returns boolean."""
        from installer.platform_utils import is_linux

        result = is_linux()
        assert isinstance(result, bool)

    def test_is_windows_returns_bool(self):
        """is_windows returns boolean."""
        from installer.platform_utils import is_windows

        result = is_windows()
        assert isinstance(result, bool)

    def test_is_wsl_returns_bool(self):
        """is_wsl returns boolean."""
        from installer.platform_utils import is_wsl

        result = is_wsl()
        assert isinstance(result, bool)

    @patch("platform.system", return_value="Darwin")
    def test_is_macos_with_darwin(self, mock_system):
        """is_macos returns True on Darwin."""
        from installer.platform_utils import is_macos

        assert is_macos() is True

    @patch("platform.system", return_value="Linux")
    def test_is_linux_with_linux(self, mock_system):
        """is_linux returns True on Linux."""
        from installer.platform_utils import is_linux

        assert is_linux() is True

    @patch("platform.system", return_value="Windows")
    def test_is_windows_with_windows(self, mock_system):
        """is_windows returns True on Windows."""
        from installer.platform_utils import is_windows

        assert is_windows() is True


class TestCommandExists:
    """Test command_exists function."""

    def test_command_exists_finds_common_commands(self):
        """command_exists finds common system commands."""
        from installer.platform_utils import command_exists

        # These should exist on any Unix-like system
        assert command_exists("ls") is True
        assert command_exists("cat") is True

    def test_command_exists_returns_false_for_nonexistent(self):
        """command_exists returns False for nonexistent commands."""
        from installer.platform_utils import command_exists

        assert command_exists("definitely_not_a_real_command_12345") is False


class TestShellConfig:
    """Test shell configuration utilities."""

    def test_get_shell_config_files_returns_list(self):
        """get_shell_config_files returns list of paths."""
        from installer.platform_utils import get_shell_config_files

        result = get_shell_config_files()
        assert isinstance(result, list)
        for path in result:
            assert isinstance(path, Path)

    def test_shell_config_files_includes_common_shells(self):
        """get_shell_config_files includes common shell configs."""
        from installer.platform_utils import get_shell_config_files

        result = get_shell_config_files()
        path_names = [p.name for p in result]
        # Should include at least one of these common configs
        common_configs = [".bashrc", ".zshrc", "config.fish"]
        assert any(name in path_names for name in common_configs)


class TestIsInDevcontainer:
    """Test devcontainer detection."""

    def test_is_in_devcontainer_returns_bool(self):
        """is_in_devcontainer returns boolean."""
        from installer.platform_utils import is_in_devcontainer

        result = is_in_devcontainer()
        assert isinstance(result, bool)

    @patch.object(Path, "exists")
    def test_is_in_devcontainer_returns_true_with_dockerenv(self, mock_exists):
        """is_in_devcontainer returns True when /.dockerenv exists."""
        from installer.platform_utils import is_in_devcontainer

        mock_exists.side_effect = lambda: True

        with patch("installer.platform_utils.Path") as mock_path:
            mock_dockerenv = MagicMock()
            mock_dockerenv.exists.return_value = True
            mock_containerenv = MagicMock()
            mock_containerenv.exists.return_value = False

            mock_path.return_value = mock_dockerenv

            def path_side_effect(arg):
                if arg == "/.dockerenv":
                    return mock_dockerenv
                elif arg == "/run/.containerenv":
                    return mock_containerenv
                return MagicMock()

            mock_path.side_effect = path_side_effect

            result = is_in_devcontainer()
            assert result is True


class TestHasNvidiaGpu:
    """Test has_nvidia_gpu function."""

    @patch("installer.platform_utils.subprocess.run")
    def test_returns_true_when_nvidia_smi_succeeds(self, mock_run):
        """has_nvidia_gpu returns True when nvidia-smi exits 0."""
        from installer.platform_utils import has_nvidia_gpu

        mock_run.return_value = MagicMock(returncode=0)
        assert has_nvidia_gpu() is True
        mock_run.assert_called_once()

    @patch("installer.platform_utils.subprocess.run")
    def test_returns_false_when_nvidia_smi_fails(self, mock_run):
        """has_nvidia_gpu returns False when nvidia-smi exits non-zero."""
        from installer.platform_utils import has_nvidia_gpu

        mock_run.return_value = MagicMock(returncode=1)
        assert has_nvidia_gpu() is False

    @patch("installer.platform_utils.subprocess.run")
    def test_returns_false_on_file_not_found(self, mock_run):
        """has_nvidia_gpu returns False when nvidia-smi not found."""
        from installer.platform_utils import has_nvidia_gpu

        mock_run.side_effect = FileNotFoundError()
        assert has_nvidia_gpu() is False

    @patch("installer.platform_utils.subprocess.run")
    def test_returns_false_on_timeout(self, mock_run):
        """has_nvidia_gpu returns False on timeout."""
        import subprocess

        from installer.platform_utils import has_nvidia_gpu

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="nvidia-smi", timeout=10)
        assert has_nvidia_gpu() is False

    @patch("installer.platform_utils.subprocess.run")
    def test_returns_false_on_os_error(self, mock_run):
        """has_nvidia_gpu returns False on OSError."""
        from installer.platform_utils import has_nvidia_gpu

        mock_run.side_effect = OSError("Permission denied")
        assert has_nvidia_gpu() is False

    @patch("installer.platform_utils.subprocess.run")
    def test_verbose_returns_dict_with_diagnostic_info(self, mock_run):
        """has_nvidia_gpu with verbose=True returns diagnostic dict."""
        from installer.platform_utils import has_nvidia_gpu

        mock_run.return_value = MagicMock(returncode=0, stdout=b"GPU 0: NVIDIA", stderr=b"")
        result = has_nvidia_gpu(verbose=True)
        assert isinstance(result, dict)
        assert "detected" in result
        assert "method" in result
        assert result["detected"] is True

    @patch("installer.platform_utils.subprocess.run")
    def test_verbose_includes_error_on_failure(self, mock_run):
        """has_nvidia_gpu verbose mode includes error info when nvidia-smi fails."""
        from installer.platform_utils import has_nvidia_gpu

        mock_run.side_effect = FileNotFoundError("nvidia-smi not found")
        result = has_nvidia_gpu(verbose=True)
        assert isinstance(result, dict)
        assert result["detected"] is False
        assert "error" in result

    @patch("installer.platform_utils.subprocess.run")
    @patch("installer.platform_utils.Path.glob")
    def test_fallback_to_dev_nvidia_when_smi_fails(self, mock_glob, mock_run):
        """has_nvidia_gpu falls back to /dev/nvidia* check when nvidia-smi fails."""
        from installer.platform_utils import has_nvidia_gpu

        mock_run.side_effect = FileNotFoundError()
        mock_glob.return_value = [Path("/dev/nvidia0")]
        result = has_nvidia_gpu(verbose=True)
        assert result["detected"] is True
        assert result["method"] == "dev_nvidia"

    @patch("installer.platform_utils.subprocess.run")
    @patch("installer.platform_utils.Path.glob")
    def test_returns_false_when_all_methods_fail(self, mock_glob, mock_run):
        """has_nvidia_gpu returns False when nvidia-smi and /dev/nvidia* both fail."""
        from installer.platform_utils import has_nvidia_gpu

        mock_run.side_effect = FileNotFoundError()
        mock_glob.return_value = []
        result = has_nvidia_gpu(verbose=True)
        assert result["detected"] is False


class TestIsWsl:
    """Test is_wsl function."""

    @patch("installer.platform_utils.is_linux", return_value=False)
    def test_is_wsl_returns_false_on_non_linux(self, mock_linux):
        """is_wsl returns False on non-Linux systems."""
        from installer.platform_utils import is_wsl

        assert is_wsl() is False

    @patch("installer.platform_utils.is_linux", return_value=True)
    @patch("builtins.open")
    def test_is_wsl_returns_true_when_microsoft_in_version(self, mock_open, mock_linux):
        """is_wsl returns True when /proc/version contains 'microsoft'."""
        from installer.platform_utils import is_wsl

        mock_open.return_value.__enter__.return_value.read.return_value = "Linux version 5.15.0-microsoft-standard"
        assert is_wsl() is True

    @patch("installer.platform_utils.is_linux", return_value=True)
    @patch("builtins.open")
    def test_is_wsl_returns_false_on_io_error(self, mock_open, mock_linux):
        """is_wsl returns False on IOError."""
        from installer.platform_utils import is_wsl

        mock_open.side_effect = IOError("Cannot read file")
        assert is_wsl() is False


class TestGetShellConfigFiles:
    """Test get_shell_config_files branches."""

    def test_get_shell_config_files_includes_bash_profile_if_exists(self):
        """get_shell_config_files includes .bash_profile if it exists."""
        import tempfile

        from installer.platform_utils import get_shell_config_files

        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            bashrc = home / ".bashrc"
            bash_profile = home / ".bash_profile"
            bashrc.write_text("# bashrc")
            bash_profile.write_text("# bash_profile")

            with patch("installer.platform_utils.Path.home", return_value=home):
                result = get_shell_config_files()

            assert bash_profile in result

    def test_get_shell_config_files_includes_fish_config_if_exists(self):
        """get_shell_config_files includes config.fish if it exists."""
        import tempfile

        from installer.platform_utils import get_shell_config_files

        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            fish_dir = home / ".config" / "fish"
            fish_dir.mkdir(parents=True)
            fish_config = fish_dir / "config.fish"
            fish_config.write_text("# fish config")

            with patch("installer.platform_utils.Path.home", return_value=home):
                result = get_shell_config_files()

            assert fish_config in result

    def test_get_shell_config_files_returns_defaults_if_none_exist(self):
        """get_shell_config_files returns defaults if no configs exist."""
        import tempfile

        from installer.platform_utils import get_shell_config_files

        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            # No shell configs exist

            with patch("installer.platform_utils.Path.home", return_value=home):
                result = get_shell_config_files()

            # Should return default paths
            assert len(result) == 3
            assert any(".bashrc" in str(p) for p in result)
