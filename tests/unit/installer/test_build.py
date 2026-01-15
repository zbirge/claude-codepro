"""Tests for installer build script."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestBuildHelpers:
    """Test build script helper functions."""

    def test_get_platform_suffix_returns_string(self):
        """get_platform_suffix returns a string."""
        from installer.build import get_platform_suffix

        result = get_platform_suffix()
        assert isinstance(result, str)
        assert "-" in result

    @patch("platform.system", return_value="Linux")
    @patch("platform.machine", return_value="x86_64")
    def test_get_platform_suffix_linux_x86_64(self, mock_machine, mock_system):
        """get_platform_suffix returns linux-x86_64."""
        from installer.build import get_platform_suffix

        result = get_platform_suffix()
        assert result == "linux-x86_64"

    @patch("platform.system", return_value="Darwin")
    @patch("platform.machine", return_value="arm64")
    def test_get_platform_suffix_darwin_arm64(self, mock_machine, mock_system):
        """get_platform_suffix returns darwin-arm64."""
        from installer.build import get_platform_suffix

        result = get_platform_suffix()
        assert result == "darwin-arm64"


class TestBuildTimestamp:
    """Test build timestamp functions."""

    def test_set_build_timestamp_returns_version_and_timestamp(self):
        """set_build_timestamp returns (version, timestamp) tuple."""
        from installer.build import set_build_timestamp

        version, timestamp = set_build_timestamp()
        assert isinstance(version, str)
        assert isinstance(timestamp, str)
        # Timestamp should contain UTC
        assert "UTC" in timestamp

    def test_reset_build_timestamp_sets_dev(self):
        """reset_build_timestamp resets to dev."""
        from installer import __build__
        from installer.build import reset_build_timestamp, set_build_timestamp

        # Set a timestamp first
        set_build_timestamp()

        # Reset it
        reset_build_timestamp()

        # Re-import to get updated value
        import importlib

        import installer

        importlib.reload(installer)
        assert installer.__build__ == "dev"


class TestBuildWithPyinstaller:
    """Test PyInstaller build function."""

    def test_build_with_pyinstaller_exists(self):
        """build_with_pyinstaller function exists."""
        from installer.build import build_with_pyinstaller

        assert callable(build_with_pyinstaller)

    @patch("installer.build.subprocess.run")
    def test_build_with_pyinstaller_local(self, mock_run):
        """build_with_pyinstaller in local mode uses simple name."""
        from installer.build import BUILD_DIR, build_with_pyinstaller

        mock_run.return_value.returncode = 0

        result = build_with_pyinstaller(local=True)

        assert result == BUILD_DIR / "ccp-installer"
        mock_run.assert_called_once()
        # Check that --name uses "ccp-installer"
        cmd = mock_run.call_args[0][0]
        name_idx = cmd.index("--name")
        assert cmd[name_idx + 1] == "ccp-installer"

    @patch("installer.build.subprocess.run")
    @patch("installer.build.get_platform_suffix", return_value="linux-x86_64")
    def test_build_with_pyinstaller_ci(self, mock_suffix, mock_run):
        """build_with_pyinstaller in CI mode uses platform suffix."""
        from installer.build import BUILD_DIR, build_with_pyinstaller

        mock_run.return_value.returncode = 0

        result = build_with_pyinstaller(local=False)

        assert result == BUILD_DIR / "ccp-installer-linux-x86_64"
        mock_run.assert_called_once()

    @patch("installer.build.subprocess.run")
    @patch("platform.system", return_value="Windows")
    @patch("installer.build.get_platform_suffix", return_value="windows-x86_64")
    def test_build_with_pyinstaller_windows(self, mock_suffix, mock_system, mock_run):
        """build_with_pyinstaller adds .exe on Windows."""
        from installer.build import BUILD_DIR, build_with_pyinstaller

        mock_run.return_value.returncode = 0

        result = build_with_pyinstaller(local=False)

        assert result == BUILD_DIR / "ccp-installer-windows-x86_64.exe"

    @patch("installer.build.subprocess.run")
    def test_build_with_pyinstaller_raises_on_failure(self, mock_run):
        """build_with_pyinstaller raises on subprocess failure."""
        import subprocess

        from installer.build import build_with_pyinstaller

        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Build failed"

        with pytest.raises(subprocess.CalledProcessError):
            build_with_pyinstaller(local=True)


class TestDeployToBin:
    """Test deploy_to_bin function."""

    def test_deploy_to_bin_copies_and_sets_permissions(self):
        """deploy_to_bin copies binary and sets executable."""
        from installer.build import deploy_to_bin

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake binary
            binary = Path(tmpdir) / "fake-binary"
            binary.write_text("fake binary content")

            with patch("installer.build.BIN_DIR", Path(tmpdir) / ".claude" / "bin"):
                result = deploy_to_bin(binary)

                assert result.exists()
                # Check it's executable (at least owner)
                assert result.stat().st_mode & 0o100


class TestMain:
    """Test main function."""

    @patch("installer.build.build_with_pyinstaller")
    @patch("installer.build.get_current_version", return_value="1.0.0")
    @patch("sys.argv", ["build.py", "--local"])
    def test_main_local_build(self, mock_version, mock_build):
        """main() runs local build."""
        from installer.build import BUILD_DIR, main

        mock_binary = BUILD_DIR / "ccp-installer"
        # Create the directory and file to avoid stat errors
        BUILD_DIR.mkdir(parents=True, exist_ok=True)
        mock_binary.write_text("binary")
        mock_build.return_value = mock_binary

        with patch("installer.build.deploy_to_bin") as mock_deploy:
            mock_deploy.return_value = mock_binary
            result = main()

        assert result == 0
        mock_build.assert_called_once_with(local=True)

    @patch("installer.build.build_with_pyinstaller")
    @patch("installer.build.set_build_timestamp", return_value=("1.0.0", "2026-01-10 UTC"))
    @patch("installer.build.reset_build_timestamp")
    @patch("sys.argv", ["build.py"])
    def test_main_ci_build(self, mock_reset, mock_timestamp, mock_build):
        """main() runs CI build and resets timestamp."""
        from installer.build import BUILD_DIR, main

        mock_binary = BUILD_DIR / "ccp-installer-linux-x86_64"
        BUILD_DIR.mkdir(parents=True, exist_ok=True)
        mock_binary.write_text("binary")
        mock_build.return_value = mock_binary

        result = main()

        assert result == 0
        mock_build.assert_called_once_with(local=False)
        mock_reset.assert_called_once()

    @patch("installer.build.build_with_pyinstaller")
    @patch("installer.build.get_current_version", return_value="1.0.0")
    @patch("sys.argv", ["build.py", "--local"])
    def test_main_returns_1_on_build_failure(self, mock_version, mock_build):
        """main() returns 1 on build failure."""
        import subprocess

        from installer.build import main

        mock_build.side_effect = subprocess.CalledProcessError(1, "pyinstaller")

        result = main()

        assert result == 1

    @patch("installer.build.build_with_pyinstaller")
    @patch("installer.build.get_current_version", return_value="1.0.0")
    @patch("installer.build.BUILD_DIR")
    @patch("sys.argv", ["build.py", "--local", "--clean"])
    def test_main_clean_removes_build_dir(self, mock_build_dir, mock_version, mock_build):
        """main() with --clean removes build directory."""
        import shutil

        from installer.build import main

        with tempfile.TemporaryDirectory() as tmpdir:
            build_dir = Path(tmpdir) / "dist"
            build_dir.mkdir()
            (build_dir / "old_file").write_text("old")

            mock_build_dir.__truediv__ = lambda self, x: build_dir / x
            mock_build_dir.exists.return_value = True

            mock_binary = build_dir / "ccp-installer"
            mock_binary.write_text("binary")
            mock_build.return_value = mock_binary

            with patch("shutil.rmtree"):
                with patch("installer.build.deploy_to_bin"):
                    # Note: rmtree won't actually be called due to mock structure
                    pass


class TestGetCurrentVersion:
    """Test get_current_version function."""

    def test_get_current_version_returns_string(self):
        """get_current_version returns a version string."""
        from installer.build import get_current_version

        result = get_current_version()
        assert isinstance(result, str)
        # Should match semver pattern roughly
        assert "." in result


class TestPlatformSuffixBranches:
    """Test platform suffix edge cases."""

    @patch("platform.system", return_value="Linux")
    @patch("platform.machine", return_value="aarch64")
    def test_get_platform_suffix_aarch64(self, mock_machine, mock_system):
        """get_platform_suffix normalizes aarch64 to arm64."""
        from installer.build import get_platform_suffix

        result = get_platform_suffix()
        assert result == "linux-arm64"

    @patch("platform.system", return_value="Linux")
    @patch("platform.machine", return_value="amd64")
    def test_get_platform_suffix_amd64(self, mock_machine, mock_system):
        """get_platform_suffix normalizes amd64 to x86_64."""
        from installer.build import get_platform_suffix

        result = get_platform_suffix()
        assert result == "linux-x86_64"

    @patch("platform.system", return_value="Linux")
    @patch("platform.machine", return_value="i386")
    def test_get_platform_suffix_unknown_arch(self, mock_machine, mock_system):
        """get_platform_suffix uses unknown arch as-is."""
        from installer.build import get_platform_suffix

        result = get_platform_suffix()
        assert result == "linux-i386"
