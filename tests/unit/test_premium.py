"""Unit tests for scripts/lib/premium.py."""

from __future__ import annotations

import stat
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add scripts directory to path so we can import premium
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from lib.premium import (
    download_premium_binary,
    get_platform_binary_name,
    prompt_for_premium,
    save_license_to_env,
)


class TestSaveLicenseToEnv:
    """Test save_license_to_env function."""

    def test_save_license_to_env_creates_new_file_when_not_exists(self):
        """Test that save_license_to_env creates .env with license key when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            env_file = project_dir / ".env"

            save_license_to_env(project_dir, "test-license-key-123")

            assert env_file.exists()
            content = env_file.read_text()
            assert "CCP_LICENSE_KEY=test-license-key-123" in content

    def test_save_license_to_env_preserves_existing_variables(self):
        """Test that save_license_to_env preserves other environment variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            env_file = project_dir / ".env"

            # Create .env with existing variables
            env_file.write_text("OPENAI_API_KEY=sk-abc123\nEXA_API_KEY=exa-key\n")

            save_license_to_env(project_dir, "new-license-key")

            content = env_file.read_text()
            # Should preserve existing variables
            assert "OPENAI_API_KEY=sk-abc123" in content
            assert "EXA_API_KEY=exa-key" in content
            # Should add new license key
            assert "CCP_LICENSE_KEY=new-license-key" in content

    def test_save_license_to_env_replaces_existing_license_key(self):
        """Test that save_license_to_env replaces existing CCP_LICENSE_KEY."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            env_file = project_dir / ".env"

            # Create .env with existing license key and other variables
            env_file.write_text("OPENAI_API_KEY=sk-abc123\nCCP_LICENSE_KEY=old-key\nEXA_API_KEY=exa-key\n")

            save_license_to_env(project_dir, "new-license-key")

            content = env_file.read_text()
            # Should preserve existing variables
            assert "OPENAI_API_KEY=sk-abc123" in content
            assert "EXA_API_KEY=exa-key" in content
            # Should replace old license key with new one
            assert "CCP_LICENSE_KEY=new-license-key" in content
            assert "CCP_LICENSE_KEY=old-key" not in content

    def test_save_license_to_env_preserves_comments(self):
        """Test that save_license_to_env preserves comments in .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            env_file = project_dir / ".env"

            # Create .env with comments
            env_file.write_text("# This is a comment\nOPENAI_API_KEY=sk-abc123\n# Another comment\n")

            save_license_to_env(project_dir, "test-license")

            content = env_file.read_text()
            assert "# This is a comment" in content
            assert "# Another comment" in content
            assert "OPENAI_API_KEY=sk-abc123" in content
            assert "CCP_LICENSE_KEY=test-license" in content

    def test_save_license_to_env_preserves_empty_lines(self):
        """Test that save_license_to_env preserves empty lines in .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            env_file = project_dir / ".env"

            # Create .env with empty lines
            original_content = "OPENAI_API_KEY=sk-abc123\n\nEXA_API_KEY=exa-key\n"
            env_file.write_text(original_content)

            save_license_to_env(project_dir, "test-license")

            content = env_file.read_text()
            lines = content.splitlines()
            # Should preserve structure with empty line between keys
            assert "OPENAI_API_KEY=sk-abc123" in lines
            assert "" in lines  # Empty line preserved
            assert "EXA_API_KEY=exa-key" in lines


class TestDownloadPremiumBinaryLocalMode:
    """Test download_premium_binary function with local mode support."""

    def test_download_premium_binary_in_local_mode_copies_from_dist(self):
        """Test that download_premium_binary copies from premium/dist/ in local mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Setup local repo with premium binary in dist
            local_repo_dir = tmpdir_path / "repo"
            binary_name = get_platform_binary_name()
            dist_dir = local_repo_dir / "premium" / "dist"
            dist_dir.mkdir(parents=True)
            source_binary = dist_dir / binary_name
            source_binary.write_bytes(b"premium binary content")

            # Destination directory
            dest_dir = tmpdir_path / "dest" / ".claude" / "bin"

            success, result = download_premium_binary(
                dest_dir, "v1.0.0", local_mode=True, local_repo_dir=local_repo_dir
            )

            assert success is True
            dest_binary = Path(result)
            assert dest_binary.exists()
            assert dest_binary.read_bytes() == b"premium binary content"

    def test_download_premium_binary_in_local_mode_returns_error_when_binary_missing(self):
        """Test that download_premium_binary returns error when local binary doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Setup local repo WITHOUT premium binary
            local_repo_dir = tmpdir_path / "repo"
            local_repo_dir.mkdir()

            dest_dir = tmpdir_path / "dest" / ".claude" / "bin"

            success, result = download_premium_binary(
                dest_dir, "v1.0.0", local_mode=True, local_repo_dir=local_repo_dir
            )

            assert success is False
            assert "not found" in result.lower()

    def test_download_premium_binary_in_local_mode_makes_binary_executable(self):
        """Test that download_premium_binary sets executable permissions in local mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Setup local repo with premium binary
            local_repo_dir = tmpdir_path / "repo"
            binary_name = get_platform_binary_name()
            dist_dir = local_repo_dir / "premium" / "dist"
            dist_dir.mkdir(parents=True)
            source_binary = dist_dir / binary_name
            source_binary.write_bytes(b"binary content")

            dest_dir = tmpdir_path / "dest" / ".claude" / "bin"

            success, result = download_premium_binary(
                dest_dir, "v1.0.0", local_mode=True, local_repo_dir=local_repo_dir
            )

            assert success is True
            dest_binary = Path(result)
            # Check executable bit is set
            assert dest_binary.stat().st_mode & stat.S_IXUSR

    @patch("urllib.request.urlopen")
    def test_download_premium_binary_downloads_when_not_local_mode(self, mock_urlopen):
        """Test that download_premium_binary downloads from GitHub when not in local mode."""
        mock_response = Mock()
        mock_response.read.return_value = b"downloaded binary"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            dest_dir = Path(tmpdir) / ".claude" / "bin"

            success, result = download_premium_binary(dest_dir, "v1.0.0")

            assert success is True
            assert mock_urlopen.called
            dest_binary = Path(result)
            assert dest_binary.exists()


class TestPromptForPremium:
    """Test prompt_for_premium function."""

    def test_prompt_for_premium_returns_key_from_env_file(self, capsys):
        """Test that prompt_for_premium finds license key in .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            env_file = project_dir / ".env"
            env_file.write_text("OPENAI_API_KEY=sk-123\nCCP_LICENSE_KEY=my-license-key\n")

            with patch.dict("os.environ", {}, clear=True):
                result = prompt_for_premium(non_interactive=False, project_dir=project_dir)

            assert result == "my-license-key"
            captured = capsys.readouterr()
            assert "Found license key in .env file" in captured.out

    def test_prompt_for_premium_returns_key_from_environment_variable(self, capsys):
        """Test that prompt_for_premium finds license key in environment."""
        with patch.dict("os.environ", {"CCP_LICENSE_KEY": "env-license-key"}):
            result = prompt_for_premium(non_interactive=False, project_dir=None)

        assert result == "env-license-key"
        captured = capsys.readouterr()
        assert "Found license key in CCP_LICENSE_KEY environment variable" in captured.out

    def test_prompt_for_premium_env_var_takes_precedence_over_env_file(self, capsys):
        """Test that environment variable takes precedence over .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            env_file = project_dir / ".env"
            env_file.write_text("CCP_LICENSE_KEY=file-key\n")

            with patch.dict("os.environ", {"CCP_LICENSE_KEY": "env-key"}):
                result = prompt_for_premium(non_interactive=False, project_dir=project_dir)

            assert result == "env-key"
            captured = capsys.readouterr()
            assert "environment variable" in captured.out

    def test_prompt_for_premium_returns_none_in_non_interactive_without_key(self):
        """Test that prompt_for_premium returns None in non-interactive mode without key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            with patch.dict("os.environ", {}, clear=True):
                result = prompt_for_premium(non_interactive=True, project_dir=project_dir)

            assert result is None


class TestGetPlatformBinaryName:
    """Test get_platform_binary_name function."""

    @patch("platform.system")
    @patch("platform.machine")
    def test_get_platform_binary_name_darwin_arm64(self, mock_machine, mock_system):
        """Test binary name for macOS ARM64."""
        mock_system.return_value = "Darwin"
        mock_machine.return_value = "arm64"

        result = get_platform_binary_name()

        assert result == "ccp-premium-darwin-arm64"

    @patch("platform.system")
    @patch("platform.machine")
    def test_get_platform_binary_name_linux_x86_64(self, mock_machine, mock_system):
        """Test binary name for Linux x86_64."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "x86_64"

        result = get_platform_binary_name()

        assert result == "ccp-premium-linux-x86_64"
