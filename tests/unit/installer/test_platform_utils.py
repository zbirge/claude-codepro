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


class TestPackageManager:
    """Test package manager detection."""

    def test_get_package_manager_returns_string_or_none(self):
        """get_package_manager returns string or None."""
        from installer.platform_utils import get_package_manager

        result = get_package_manager()
        assert result is None or isinstance(result, str)


class TestPlatformDirs:
    """Test platformdirs integration."""

    def test_get_config_dir_returns_path(self):
        """get_config_dir returns a Path."""
        from installer.platform_utils import get_config_dir

        result = get_config_dir()
        assert isinstance(result, Path)

    def test_get_data_dir_returns_path(self):
        """get_data_dir returns a Path."""
        from installer.platform_utils import get_data_dir

        result = get_data_dir()
        assert isinstance(result, Path)


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


class TestPlatformSuffix:
    """Test platform suffix generation."""

    def test_get_platform_suffix_returns_string(self):
        """get_platform_suffix returns a string."""
        from installer.platform_utils import get_platform_suffix

        result = get_platform_suffix()
        assert isinstance(result, str)
        assert "-" in result  # e.g., "linux-x86_64"

    @patch("platform.system", return_value="Linux")
    @patch("platform.machine", return_value="x86_64")
    def test_get_platform_suffix_linux_x86_64(self, mock_machine, mock_system):
        """get_platform_suffix returns correct format for Linux x86_64."""
        from installer.platform_utils import get_platform_suffix

        result = get_platform_suffix()
        assert result == "linux-x86_64"

    @patch("platform.system", return_value="Darwin")
    @patch("platform.machine", return_value="arm64")
    def test_get_platform_suffix_darwin_arm64(self, mock_machine, mock_system):
        """get_platform_suffix returns correct format for macOS arm64."""
        from installer.platform_utils import get_platform_suffix

        result = get_platform_suffix()
        assert result == "darwin-arm64"


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


class TestIsInDevcontainer:
    """Test is_in_devcontainer function."""

    @patch.object(Path, "exists")
    def test_is_in_devcontainer_returns_true_with_dockerenv(self, mock_exists):
        """is_in_devcontainer returns True when /.dockerenv exists."""
        from installer.platform_utils import is_in_devcontainer

        def exists_side_effect(self):
            return str(self) == "/.dockerenv"

        mock_exists.side_effect = lambda: True

        # We need to patch Path itself
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


class TestGetPackageManager:
    """Test get_package_manager function branches."""

    @patch("installer.platform_utils.is_macos", return_value=True)
    @patch("installer.platform_utils.command_exists")
    def test_get_package_manager_macos_with_brew(self, mock_cmd, mock_macos):
        """get_package_manager returns 'brew' on macOS with Homebrew."""
        from installer.platform_utils import get_package_manager

        mock_cmd.return_value = True
        assert get_package_manager() == "brew"

    @patch("installer.platform_utils.is_macos", return_value=True)
    @patch("installer.platform_utils.command_exists", return_value=False)
    def test_get_package_manager_macos_without_brew(self, mock_cmd, mock_macos):
        """get_package_manager returns None on macOS without Homebrew."""
        from installer.platform_utils import get_package_manager

        assert get_package_manager() is None

    @patch("installer.platform_utils.is_macos", return_value=False)
    @patch("installer.platform_utils.is_linux", return_value=True)
    @patch("installer.platform_utils.is_wsl", return_value=False)
    @patch("installer.platform_utils.command_exists")
    def test_get_package_manager_linux_apt(self, mock_cmd, mock_wsl, mock_linux, mock_macos):
        """get_package_manager returns 'apt-get' on Debian-based Linux."""
        from installer.platform_utils import get_package_manager

        mock_cmd.side_effect = lambda cmd: cmd == "apt-get"
        assert get_package_manager() == "apt-get"

    @patch("installer.platform_utils.is_macos", return_value=False)
    @patch("installer.platform_utils.is_linux", return_value=True)
    @patch("installer.platform_utils.is_wsl", return_value=False)
    @patch("installer.platform_utils.command_exists")
    def test_get_package_manager_linux_dnf(self, mock_cmd, mock_wsl, mock_linux, mock_macos):
        """get_package_manager returns 'dnf' on Fedora."""
        from installer.platform_utils import get_package_manager

        mock_cmd.side_effect = lambda cmd: cmd == "dnf"
        assert get_package_manager() == "dnf"

    @patch("installer.platform_utils.is_macos", return_value=False)
    @patch("installer.platform_utils.is_linux", return_value=True)
    @patch("installer.platform_utils.is_wsl", return_value=False)
    @patch("installer.platform_utils.command_exists")
    def test_get_package_manager_linux_yum(self, mock_cmd, mock_wsl, mock_linux, mock_macos):
        """get_package_manager returns 'yum' on older RHEL."""
        from installer.platform_utils import get_package_manager

        mock_cmd.side_effect = lambda cmd: cmd == "yum"
        assert get_package_manager() == "yum"

    @patch("installer.platform_utils.is_macos", return_value=False)
    @patch("installer.platform_utils.is_linux", return_value=True)
    @patch("installer.platform_utils.is_wsl", return_value=False)
    @patch("installer.platform_utils.command_exists")
    def test_get_package_manager_linux_pacman(self, mock_cmd, mock_wsl, mock_linux, mock_macos):
        """get_package_manager returns 'pacman' on Arch."""
        from installer.platform_utils import get_package_manager

        mock_cmd.side_effect = lambda cmd: cmd == "pacman"
        assert get_package_manager() == "pacman"


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


class TestAddToPath:
    """Test add_to_path function."""

    def test_add_to_path_adds_export_to_bashrc(self):
        """add_to_path adds export line to bashrc."""
        import tempfile

        from installer.platform_utils import add_to_path

        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            bashrc = home / ".bashrc"
            bashrc.write_text("# existing config\n")

            with patch("installer.platform_utils.get_shell_config_files", return_value=[bashrc]):
                add_to_path(Path("/custom/bin"))

            content = bashrc.read_text()
            assert 'export PATH="/custom/bin:$PATH"' in content

    def test_add_to_path_adds_set_to_fish_config(self):
        """add_to_path adds set -gx line to fish config."""
        import tempfile

        from installer.platform_utils import add_to_path

        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            fish_dir = home / ".config" / "fish"
            fish_dir.mkdir(parents=True)
            fish_config = fish_dir / "config.fish"
            fish_config.write_text("# existing config\n")

            with patch("installer.platform_utils.get_shell_config_files", return_value=[fish_config]):
                add_to_path(Path("/custom/bin"))

            content = fish_config.read_text()
            assert 'set -gx PATH "/custom/bin" $PATH' in content

    def test_add_to_path_skips_if_already_in_path(self):
        """add_to_path skips if path already in config."""
        import tempfile

        from installer.platform_utils import add_to_path

        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            bashrc = home / ".bashrc"
            bashrc.write_text('# existing\nexport PATH="/custom/bin:$PATH"\n')

            with patch("installer.platform_utils.get_shell_config_files", return_value=[bashrc]):
                add_to_path(Path("/custom/bin"))

            content = bashrc.read_text()
            # Should not duplicate
            assert content.count("/custom/bin") == 1

    def test_add_to_path_skips_nonexistent_files(self):
        """add_to_path skips files that don't exist."""
        import tempfile

        from installer.platform_utils import add_to_path

        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            bashrc = home / ".bashrc"  # Does not exist

            with patch("installer.platform_utils.get_shell_config_files", return_value=[bashrc]):
                # Should not raise
                add_to_path(Path("/custom/bin"))
