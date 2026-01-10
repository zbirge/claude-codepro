"""Tests for git setup step."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestGitSetupStep:
    """Test GitSetupStep class."""

    def test_git_setup_step_has_correct_name(self):
        """GitSetupStep has name 'git_setup'."""
        from installer.steps.git_setup import GitSetupStep

        step = GitSetupStep()
        assert step.name == "git_setup"

    def test_check_returns_true_when_git_configured(self):
        """check() returns True when git is properly configured."""
        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep
        from installer.ui import Console

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # Initialize git and configure
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=project_dir, capture_output=True)
            # Disable commit signing for test environments
            subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=project_dir, capture_output=True)

            # Create a commit
            (project_dir / ".gitignore").write_text("*.tmp\n")
            subprocess.run(["git", "add", "."], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial"], cwd=project_dir, capture_output=True)

            ctx = InstallContext(
                project_dir=project_dir,
                ui=Console(non_interactive=True),
            )

            assert step.check(ctx) is True

    def test_check_returns_false_when_no_git(self):
        """check() returns False when no git repository."""
        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep
        from installer.ui import Console

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            ctx = InstallContext(
                project_dir=project_dir,
                ui=Console(non_interactive=True),
            )

            assert step.check(ctx) is False


class TestGitHelpers:
    """Test git helper functions."""

    def test_is_git_initialized(self):
        """is_git_initialized returns True when .git exists."""
        from installer.steps.git_setup import is_git_initialized

        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            assert is_git_initialized(project_dir) is False

            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            assert is_git_initialized(project_dir) is True

    def test_get_git_config(self):
        """get_git_config retrieves config values."""
        from installer.steps.git_setup import get_git_config

        # This tests the global config lookup
        result = get_git_config("core.pager")
        # Result can be None or string depending on system config
        assert result is None or isinstance(result, str)

    def test_has_commits_returns_false_for_empty_repo(self):
        """has_commits returns False for empty repository."""
        from installer.steps.git_setup import has_commits

        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            assert has_commits(project_dir) is False

    def test_has_commits_returns_true_with_commit(self):
        """has_commits returns True when repository has commits."""
        from installer.steps.git_setup import has_commits

        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=project_dir, capture_output=True)
            # Disable commit signing for test environments
            subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=project_dir, capture_output=True)
            (project_dir / "test.txt").write_text("test")
            subprocess.run(["git", "add", "."], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial"], cwd=project_dir, capture_output=True)
            assert has_commits(project_dir) is True


class TestSetGitConfig:
    """Test set_git_config function."""

    def test_set_git_config_returns_true_on_success(self):
        """set_git_config returns True when config is set successfully."""
        from installer.steps.git_setup import set_git_config

        with patch("installer.steps.git_setup.subprocess.run") as mock_run:
            mock_run.return_value = None  # check=True succeeds

            result = set_git_config("test.key", "test_value")
            assert result is True
            mock_run.assert_called_once()

    def test_set_git_config_returns_false_on_failure(self):
        """set_git_config returns False when config fails."""
        from installer.steps.git_setup import set_git_config

        with patch("installer.steps.git_setup.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")

            result = set_git_config("test.key", "test_value")
            assert result is False


class TestGetGitConfigBranches:
    """Test get_git_config edge cases."""

    def test_get_git_config_with_project_dir(self):
        """get_git_config checks local repo config first."""
        from installer.steps.git_setup import get_git_config

        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "test.local", "local_value"], cwd=project_dir, capture_output=True)

            result = get_git_config("test.local", project_dir)
            assert result == "local_value"

    def test_get_git_config_handles_exception(self):
        """get_git_config returns None on exception."""
        from installer.steps.git_setup import get_git_config

        with patch("installer.steps.git_setup.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Test error")

            result = get_git_config("any.key")
            assert result is None


class TestHasCommitsException:
    """Test has_commits exception handling."""

    def test_has_commits_returns_false_on_exception(self):
        """has_commits returns False on exception."""
        from installer.steps.git_setup import has_commits

        with patch("installer.steps.git_setup.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Test error")

            result = has_commits(Path("/any/path"))
            assert result is False


class TestCreateInitialCommit:
    """Test create_initial_commit function."""

    def test_create_initial_commit_returns_true_on_success(self):
        """create_initial_commit returns True when successful."""
        from installer.steps.git_setup import create_initial_commit

        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=project_dir, capture_output=True)
            (project_dir / "test.txt").write_text("test content")

            result = create_initial_commit(project_dir)
            assert result is True

    def test_create_initial_commit_returns_false_on_failure(self):
        """create_initial_commit returns False on failure."""
        from installer.steps.git_setup import create_initial_commit

        with patch("installer.steps.git_setup.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")

            result = create_initial_commit(Path("/any/path"))
            assert result is False


class TestGitSetupRun:
    """Test GitSetupStep.run()."""

    def test_run_initializes_git_if_needed(self):
        """run() initializes git repository if not present."""
        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep
        from installer.ui import Console

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            ctx = InstallContext(
                project_dir=project_dir,
                non_interactive=True,
                ui=Console(non_interactive=True),
            )

            # Mock environment variables for non-interactive
            with patch.dict("os.environ", {"GIT_USER_NAME": "CI User", "GIT_USER_EMAIL": "ci@test.com"}):
                step.run(ctx)

            # Git should be initialized
            assert (project_dir / ".git").is_dir()

    def test_run_skips_when_already_configured(self):
        """run() skips when git is already configured."""
        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep
        from installer.ui import Console

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # Pre-configure git
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Existing"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "user.email", "existing@test.com"], cwd=project_dir, capture_output=True)
            # Disable commit signing for test environments
            subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=project_dir, capture_output=True)
            (project_dir / ".gitignore").write_text("*.tmp\n")
            subprocess.run(["git", "add", "."], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial"], cwd=project_dir, capture_output=True)

            ctx = InstallContext(
                project_dir=project_dir,
                non_interactive=True,
                ui=Console(non_interactive=True),
            )

            # Should complete without error
            step.run(ctx)

    def test_run_handles_git_not_installed(self):
        """run() handles case where git is not installed."""
        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep
        from installer.ui import Console

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            ctx = InstallContext(
                project_dir=project_dir,
                non_interactive=True,
                ui=Console(non_interactive=True),
            )

            with patch("installer.steps.git_setup.subprocess.run") as mock_run:
                mock_run.side_effect = Exception("Git not found")

                # Should not raise, just return early
                step.run(ctx)

    def test_run_handles_git_init_failure(self):
        """run() handles git init failure."""
        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep
        from installer.ui import Console

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            ctx = InstallContext(
                project_dir=project_dir,
                non_interactive=True,
                ui=Console(non_interactive=True),
            )

            call_count = 0

            def mock_run_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    # First call is git --version, succeed
                    return None
                # Second call is git init, fail
                raise subprocess.CalledProcessError(1, "git init")

            with patch("installer.steps.git_setup.subprocess.run") as mock_run:
                mock_run.side_effect = mock_run_side_effect

                # Should not raise, just return early
                step.run(ctx)

    def test_run_prompts_for_username_interactively(self):
        """run() prompts for user.name in interactive mode."""
        from unittest.mock import MagicMock

        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep
        from installer.ui import Console

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=project_dir, capture_output=True)

            mock_ui = MagicMock(spec=Console)
            mock_ui.input.side_effect = ["Test User", "test@example.com"]

            ctx = InstallContext(
                project_dir=project_dir,
                non_interactive=False,
                ui=mock_ui,
            )

            # Mock get_git_config to return None for user.name/email to force prompting
            with patch("installer.steps.git_setup.get_git_config", return_value=None):
                step.run(ctx)

            # Should have called input for name and email
            assert mock_ui.input.call_count >= 1

    def test_run_non_interactive_missing_env_var(self):
        """run() handles missing env vars in non-interactive mode."""
        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep
        from installer.ui import Console

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=project_dir, capture_output=True)

            ctx = InstallContext(
                project_dir=project_dir,
                non_interactive=True,
                ui=Console(non_interactive=True),
            )

            # No GIT_USER_NAME or GIT_USER_EMAIL in environment
            with patch.dict("os.environ", {}, clear=True):
                # Should return early without raising
                step.run(ctx)

    def test_run_handles_empty_username_input(self):
        """run() handles empty username input."""
        from unittest.mock import MagicMock

        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep
        from installer.ui import Console

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=project_dir, capture_output=True)

            mock_ui = MagicMock(spec=Console)
            mock_ui.input.return_value = ""  # Empty input

            ctx = InstallContext(
                project_dir=project_dir,
                non_interactive=False,
                ui=mock_ui,
            )

            # Should return early without raising
            step.run(ctx)

    def test_run_handles_set_config_failure(self):
        """run() handles failure when setting git config."""
        from unittest.mock import MagicMock

        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=project_dir, capture_output=True)

            mock_ui = MagicMock()
            mock_ui.input.return_value = "Test User"

            ctx = InstallContext(
                project_dir=project_dir,
                non_interactive=False,
                ui=mock_ui,
            )

            with patch("installer.steps.git_setup.set_git_config", return_value=False):
                # Should return early when set_git_config fails
                step.run(ctx)

    def test_run_creates_initial_commit_with_gitignore(self):
        """run() creates .gitignore and initial commit."""
        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep
        from installer.ui import Console

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            ctx = InstallContext(
                project_dir=project_dir,
                non_interactive=True,
                ui=Console(non_interactive=True),
            )

            with patch.dict("os.environ", {"GIT_USER_NAME": "CI User", "GIT_USER_EMAIL": "ci@test.com"}):
                step.run(ctx)

            # .gitignore should be created
            assert (project_dir / ".gitignore").exists()

    def test_run_handles_initial_commit_failure(self):
        """run() handles failure when creating initial commit."""
        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep
        from installer.ui import Console

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=project_dir, capture_output=True)

            ctx = InstallContext(
                project_dir=project_dir,
                non_interactive=True,
                ui=Console(non_interactive=True),
            )

            with patch("installer.steps.git_setup.create_initial_commit", return_value=False):
                # Should not raise, just warn
                step.run(ctx)


class TestGitSetupCheck:
    """Test GitSetupStep.check() branches."""

    def test_check_returns_false_when_no_user_name(self):
        """check() returns False when user.name not configured."""
        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep
        from installer.ui import Console

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            # No user.name configured

            ctx = InstallContext(
                project_dir=project_dir,
                ui=Console(non_interactive=True),
            )

            assert step.check(ctx) is False

    def test_check_returns_false_when_no_user_email(self):
        """check() returns False when user.email not configured."""
        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep
        from installer.ui import Console

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=project_dir, capture_output=True)
            # No user.email configured

            ctx = InstallContext(
                project_dir=project_dir,
                ui=Console(non_interactive=True),
            )

            assert step.check(ctx) is False

    def test_check_returns_false_when_no_commits(self):
        """check() returns False when no commits exist."""
        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep
        from installer.ui import Console

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=project_dir, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=project_dir, capture_output=True)
            # No commits

            ctx = InstallContext(
                project_dir=project_dir,
                ui=Console(non_interactive=True),
            )

            assert step.check(ctx) is False


class TestGitSetupRollback:
    """Test GitSetupStep.rollback()."""

    def test_rollback_does_nothing(self):
        """rollback() does nothing (by design)."""
        from installer.context import InstallContext
        from installer.steps.git_setup import GitSetupStep
        from installer.ui import Console

        step = GitSetupStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            ctx = InstallContext(
                project_dir=project_dir,
                ui=Console(non_interactive=True),
            )

            # Should not raise
            step.rollback(ctx)
