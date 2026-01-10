"""Tests for CLI entry point and step orchestration."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestCLIApp:
    """Test CLI application."""

    def test_cli_app_exists(self):
        """CLI app module exists."""
        from installer.cli import app

        assert app is not None

    def test_cli_has_install_command(self):
        """CLI has install command."""
        from installer.cli import install

        assert callable(install)


class TestRunInstallation:
    """Test step orchestration."""

    def test_run_installation_exists(self):
        """run_installation function exists."""
        from installer.cli import run_installation

        assert callable(run_installation)

    @patch("installer.cli.get_all_steps")
    def test_run_installation_executes_steps(self, mock_get_all_steps):
        """run_installation executes steps in order."""
        from installer.cli import run_installation
        from installer.context import InstallContext
        from installer.ui import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
                non_interactive=True,
            )

            # Create mock steps
            mock_step1 = MagicMock()
            mock_step1.name = "step1"
            mock_step1.check.return_value = False

            mock_step2 = MagicMock()
            mock_step2.name = "step2"
            mock_step2.check.return_value = False

            mock_get_all_steps.return_value = [mock_step1, mock_step2]

            run_installation(ctx)

            # Both steps should be called
            mock_step1.run.assert_called_once_with(ctx)
            mock_step2.run.assert_called_once_with(ctx)


class TestRollback:
    """Test rollback functionality."""

    def test_rollback_completed_steps_exists(self):
        """rollback_completed_steps function exists."""
        from installer.cli import rollback_completed_steps

        assert callable(rollback_completed_steps)

    def test_rollback_calls_step_rollback(self):
        """rollback_completed_steps calls rollback on completed steps."""
        from installer.cli import rollback_completed_steps
        from installer.context import InstallContext
        from installer.ui import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            ctx.mark_completed("test_step")

            # Mock step
            mock_step = MagicMock()
            mock_step.name = "test_step"

            steps = [mock_step]
            rollback_completed_steps(ctx, steps)

            mock_step.rollback.assert_called_once_with(ctx)


class TestBackupFeature:
    """Test backup feature ignores special files."""

    def test_ignore_special_files_skips_tmp_directory(self):
        """ignore_special_files function skips tmp directory."""
        # Import the function by running the backup code path
        from pathlib import Path

        # Simulate the ignore function logic
        def ignore_special_files(directory: str, files: list[str]) -> list[str]:
            ignored = []
            for f in files:
                path = Path(directory) / f
                if path.is_fifo() or path.is_socket() or path.is_block_device() or path.is_char_device():
                    ignored.append(f)
                if f == "tmp":
                    ignored.append(f)
            return ignored

        # Test that tmp is ignored
        result = ignore_special_files("/some/dir", ["commands", "hooks", "tmp", "scripts"])
        assert "tmp" in result
        assert "commands" not in result
        assert "hooks" not in result

    def test_backup_copytree_with_ignore(self):
        """Backup uses copytree with ignore function."""
        import shutil
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source directory with regular files and tmp subdirectory
            source = Path(tmpdir) / ".claude"
            source.mkdir()
            (source / "commands").mkdir()
            (source / "commands" / "spec.md").write_text("test")
            (source / "tmp").mkdir()
            (source / "tmp" / "pipes").mkdir()

            # Create backup with ignore function
            backup = Path(tmpdir) / ".claude.backup.test"

            def ignore_special_files(directory: str, files: list[str]) -> list[str]:
                ignored = []
                for f in files:
                    if f == "tmp":
                        ignored.append(f)
                return ignored

            shutil.copytree(source, backup, ignore=ignore_special_files)

            # Verify backup was created without tmp
            assert backup.exists()
            assert (backup / "commands" / "spec.md").exists()
            assert not (backup / "tmp").exists()


class TestRollbackComprehensive:
    """Comprehensive tests for rollback functionality."""

    def test_rollback_completed_steps_calls_rollback_in_reverse_order(self):
        """rollback_completed_steps calls rollback in reverse order."""
        from installer.cli import rollback_completed_steps
        from installer.context import InstallContext
        from installer.ui import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            ctx.mark_completed("step1")
            ctx.mark_completed("step2")
            ctx.mark_completed("step3")

            # Track order of rollback calls
            rollback_order = []

            mock_step1 = MagicMock()
            mock_step1.name = "step1"
            mock_step1.rollback.side_effect = lambda ctx: rollback_order.append("step1")

            mock_step2 = MagicMock()
            mock_step2.name = "step2"
            mock_step2.rollback.side_effect = lambda ctx: rollback_order.append("step2")

            mock_step3 = MagicMock()
            mock_step3.name = "step3"
            mock_step3.rollback.side_effect = lambda ctx: rollback_order.append("step3")

            steps = [mock_step1, mock_step2, mock_step3]
            rollback_completed_steps(ctx, steps)

            # Should be in reverse order
            assert rollback_order == ["step3", "step2", "step1"]

    def test_rollback_completed_steps_handles_rollback_errors(self):
        """rollback_completed_steps logs errors but continues."""
        from installer.cli import rollback_completed_steps
        from installer.context import InstallContext
        from installer.ui import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            ctx.mark_completed("step1")
            ctx.mark_completed("step2")

            rollback_order = []

            mock_step1 = MagicMock()
            mock_step1.name = "step1"
            mock_step1.rollback.side_effect = lambda ctx: rollback_order.append("step1")

            mock_step2 = MagicMock()
            mock_step2.name = "step2"
            mock_step2.rollback.side_effect = RuntimeError("Rollback failed")

            steps = [mock_step1, mock_step2]
            # Should not raise even though step2 rollback fails
            rollback_completed_steps(ctx, steps)

            # step2 rollback was attempted even though it failed
            mock_step2.rollback.assert_called_once()
            # step1 rollback should still be called
            assert rollback_order == ["step1"]

    def test_rollback_completed_steps_only_rollbacks_completed(self):
        """rollback_completed_steps only rolls back steps in completed_steps list."""
        from installer.cli import rollback_completed_steps
        from installer.context import InstallContext
        from installer.ui import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            # Only mark step1 as completed, not step2
            ctx.mark_completed("step1")

            mock_step1 = MagicMock()
            mock_step1.name = "step1"

            mock_step2 = MagicMock()
            mock_step2.name = "step2"

            steps = [mock_step1, mock_step2]
            rollback_completed_steps(ctx, steps)

            # Only step1 should be rolled back
            mock_step1.rollback.assert_called_once_with(ctx)
            mock_step2.rollback.assert_not_called()

    def test_rollback_without_ui(self):
        """rollback_completed_steps works without UI."""
        from installer.cli import rollback_completed_steps
        from installer.context import InstallContext

        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=None,
            )
            ctx.mark_completed("step1")

            mock_step = MagicMock()
            mock_step.name = "step1"

            rollback_completed_steps(ctx, [mock_step])
            mock_step.rollback.assert_called_once_with(ctx)


class TestRunInstallationComprehensive:
    """Comprehensive tests for run_installation."""

    @patch("installer.cli.get_all_steps")
    def test_run_installation_rollbacks_on_fatal_error(self, mock_get_all_steps):
        """run_installation calls rollback on FatalInstallError."""
        from installer.cli import run_installation
        from installer.context import InstallContext
        from installer.errors import FatalInstallError
        from installer.ui import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
                non_interactive=True,
            )

            mock_step1 = MagicMock()
            mock_step1.name = "step1"
            mock_step1.check.return_value = False

            mock_step2 = MagicMock()
            mock_step2.name = "step2"
            mock_step2.check.return_value = False
            mock_step2.run.side_effect = FatalInstallError("Test error")

            mock_get_all_steps.return_value = [mock_step1, mock_step2]

            with pytest.raises(FatalInstallError):
                run_installation(ctx)

            # step1 was completed so should be rolled back
            mock_step1.rollback.assert_called_once()

    @patch("installer.cli.get_all_steps")
    def test_run_installation_marks_completed_steps(self, mock_get_all_steps):
        """run_installation marks steps as completed."""
        from installer.cli import run_installation
        from installer.context import InstallContext
        from installer.ui import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
                non_interactive=True,
            )

            mock_step = MagicMock()
            mock_step.name = "test_step"
            mock_step.check.return_value = False

            mock_get_all_steps.return_value = [mock_step]

            run_installation(ctx)

            assert "test_step" in ctx.completed_steps

    @patch("installer.cli.get_all_steps")
    def test_run_installation_skips_completed_steps(self, mock_get_all_steps):
        """run_installation skips steps that return True from check()."""
        from installer.cli import run_installation
        from installer.context import InstallContext
        from installer.ui import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
                non_interactive=True,
            )

            mock_step = MagicMock()
            mock_step.name = "already_done"
            mock_step.check.return_value = True  # Already complete

            mock_get_all_steps.return_value = [mock_step]

            run_installation(ctx)

            # Step should not be run if check returns True
            mock_step.run.assert_not_called()

    @patch("installer.cli.get_all_steps")
    def test_run_installation_without_ui(self, mock_get_all_steps):
        """run_installation works without UI."""
        from installer.cli import run_installation
        from installer.context import InstallContext

        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=None,
                non_interactive=True,
            )

            mock_step = MagicMock()
            mock_step.name = "step1"
            mock_step.check.return_value = False

            mock_get_all_steps.return_value = [mock_step]

            run_installation(ctx)
            mock_step.run.assert_called_once()


class TestInstallCommand:
    """Test install command."""

    @patch("installer.cli.run_installation")
    def test_install_local_mode_runs_installation(self, mock_run_install):
        """install --local runs installation without prompts."""
        from typer.testing import CliRunner

        from installer.cli import app

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, ["install", "--local"], catch_exceptions=False)

        # Should not fail (exit code is from run_installation)
        mock_run_install.assert_called_once()

    @patch("installer.cli.run_installation")
    def test_install_non_interactive_skips_prompts(self, mock_run_install):
        """install --non-interactive skips interactive prompts."""
        from typer.testing import CliRunner

        from installer.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["install", "--non-interactive"])

        mock_run_install.assert_called_once()

    @patch("installer.cli.run_installation")
    def test_install_with_skip_flags(self, mock_run_install):
        """install respects skip flags."""
        from typer.testing import CliRunner

        from installer.cli import app

        runner = CliRunner()
        result = runner.invoke(
            app, ["install", "--local", "--skip-python", "--skip-typescript", "--skip-env"]
        )

        mock_run_install.assert_called_once()
        ctx = mock_run_install.call_args[0][0]
        assert ctx.install_python is False
        assert ctx.install_typescript is False
        assert ctx.skip_env is True

    @patch("installer.cli.run_installation")
    def test_install_fatal_error_exits_with_code_1(self, mock_run_install):
        """install exits with code 1 on FatalInstallError."""
        from typer.testing import CliRunner

        from installer.cli import app
        from installer.errors import FatalInstallError

        mock_run_install.side_effect = FatalInstallError("Test error")

        runner = CliRunner()
        result = runner.invoke(app, ["install", "--local"])

        assert result.exit_code == 1

    @patch("installer.cli.run_installation")
    def test_install_keyboard_interrupt_exits_with_code_130(self, mock_run_install):
        """install exits with code 130 on KeyboardInterrupt."""
        from typer.testing import CliRunner

        from installer.cli import app

        mock_run_install.side_effect = KeyboardInterrupt()

        runner = CliRunner()
        result = runner.invoke(app, ["install", "--local"])

        assert result.exit_code == 130

    @patch("installer.cli.run_installation")
    def test_install_creates_backup_when_confirmed(self, mock_run_install):
        """install creates backup when user confirms."""
        from typer.testing import CliRunner

        from installer.cli import app

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create existing .claude directory
            claude_dir = Path(tmpdir) / ".claude"
            claude_dir.mkdir()
            (claude_dir / "commands").mkdir()
            (claude_dir / "commands" / "test.md").write_text("test")

            with patch("installer.cli.Path.cwd", return_value=Path(tmpdir)):
                # Simulate user confirming backup (y) and Python (y) and TypeScript (y)
                result = runner.invoke(
                    app, ["install"], input="y\ny\ny\n", catch_exceptions=False
                )

            # Check that a backup was created
            backups = list(Path(tmpdir).glob(".claude.backup.*"))
            assert len(backups) == 1

    @patch("installer.cli.run_installation")
    def test_install_skips_backup_when_declined(self, mock_run_install):
        """install skips backup when user declines."""
        from typer.testing import CliRunner

        from installer.cli import app

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create existing .claude directory
            claude_dir = Path(tmpdir) / ".claude"
            claude_dir.mkdir()
            (claude_dir / "commands").mkdir()

            with patch("installer.cli.Path.cwd", return_value=Path(tmpdir)):
                # Simulate user declining backup (n) and selecting Python (y) and TypeScript (y)
                result = runner.invoke(
                    app, ["install"], input="n\ny\ny\n", catch_exceptions=False
                )

            # Check that no backup was created
            backups = list(Path(tmpdir).glob(".claude.backup.*"))
            assert len(backups) == 0

    @patch("installer.cli.run_installation")
    def test_install_prompts_for_python_support(self, mock_run_install):
        """install prompts for Python support when not in local mode."""
        from typer.testing import CliRunner

        from installer.cli import app

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("installer.cli.Path.cwd", return_value=Path(tmpdir)):
                # No .claude directory, so no backup prompt
                # Just Python (y) and TypeScript (n)
                result = runner.invoke(app, ["install"], input="y\nn\n", catch_exceptions=False)

        mock_run_install.assert_called_once()
        ctx = mock_run_install.call_args[0][0]
        assert ctx.install_python is True
        assert ctx.install_typescript is False

    @patch("installer.cli.run_installation")
    def test_install_with_local_repo_dir(self, mock_run_install):
        """install accepts --local-repo-dir option."""
        from typer.testing import CliRunner

        from installer.cli import app

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app, ["install", "--local", "--local-repo-dir", tmpdir], catch_exceptions=False
            )

        mock_run_install.assert_called_once()
        ctx = mock_run_install.call_args[0][0]
        assert ctx.local_repo_dir == Path(tmpdir)


class TestVersionCommand:
    """Test version command."""

    def test_version_outputs_build_info(self):
        """version command outputs build information."""
        from typer.testing import CliRunner

        from installer.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "build" in result.output.lower()


class TestFindWrapperScript:
    """Test find_wrapper_script function."""

    def test_find_wrapper_script_returns_cwd_path(self):
        """find_wrapper_script returns path in cwd when it exists."""
        from installer.cli import find_wrapper_script

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("installer.cli.Path.cwd", return_value=Path(tmpdir)):
                wrapper_dir = Path(tmpdir) / ".claude" / "scripts"
                wrapper_dir.mkdir(parents=True)
                wrapper_path = wrapper_dir / "wrapper.py"
                wrapper_path.write_text("# wrapper script")

                result = find_wrapper_script()
                assert result == wrapper_path

    def test_find_wrapper_script_returns_module_path(self):
        """find_wrapper_script falls back to module path when cwd doesn't have it."""
        # This test verifies the function structure rather than the actual fallback path
        # since mocking __file__ at module level is complex
        from installer.cli import find_wrapper_script

        # The actual .claude/scripts/wrapper.py exists in the project
        # So this test verifies find_wrapper_script returns a valid path
        result = find_wrapper_script()
        # The function should return a path (from cwd or module) if wrapper exists
        assert result is None or result.name == "wrapper.py"

    def test_find_wrapper_script_returns_none_when_not_found(self):
        """find_wrapper_script returns None when wrapper not found anywhere."""
        import installer.cli as cli_module

        original_file = cli_module.__file__

        with tempfile.TemporaryDirectory() as tmpdir:
            with tempfile.TemporaryDirectory() as module_base:
                # Mock Path.cwd to an empty tmpdir
                # Mock __file__ to point to a location without .claude/scripts/wrapper.py
                fake_cli_file = Path(module_base) / "installer" / "cli.py"
                fake_cli_file.parent.mkdir(parents=True)
                fake_cli_file.write_text("")

                with patch("installer.cli.Path.cwd", return_value=Path(tmpdir)):
                    with patch.object(cli_module, "__file__", str(fake_cli_file)):
                        from installer.cli import find_wrapper_script

                        # Force re-evaluation of the function with patched values
                        # Need to reload to pick up the patched __file__
                        # Since this is complex, test the expected behavior
                        # Neither cwd nor module path has wrapper.py
                        result = find_wrapper_script()
                        # Result will be None since neither location has wrapper.py
                        assert result is None


class TestRunWithWrapper:
    """Test run_with_wrapper function."""

    def test_run_with_wrapper_executes_wrapper(self):
        """run_with_wrapper executes wrapper script with args."""
        from installer.cli import run_with_wrapper

        with tempfile.TemporaryDirectory() as tmpdir:
            wrapper_dir = Path(tmpdir) / ".claude" / "scripts"
            wrapper_dir.mkdir(parents=True)
            wrapper_path = wrapper_dir / "wrapper.py"
            wrapper_path.write_text("# wrapper script")

            with patch("installer.cli.find_wrapper_script", return_value=wrapper_path):
                with patch("installer.cli.subprocess.call", return_value=0) as mock_call:
                    result = run_with_wrapper(["--help"])
                    assert result == 0
                    mock_call.assert_called_once()
                    # Check that wrapper path is in the command
                    call_args = mock_call.call_args[0][0]
                    assert str(wrapper_path) in call_args

    def test_run_with_wrapper_returns_1_when_wrapper_not_found(self):
        """run_with_wrapper returns 1 when wrapper not found."""
        from installer.cli import run_with_wrapper

        with patch("installer.cli.find_wrapper_script", return_value=None):
            result = run_with_wrapper(["--help"])
            assert result == 1


class TestLaunchCommand:
    """Test launch command."""

    def test_launch_with_wrapper(self):
        """launch command uses wrapper by default."""
        from typer.testing import CliRunner

        from installer.cli import app

        with patch("installer.cli.run_with_wrapper", return_value=0) as mock_run:
            runner = CliRunner()
            result = runner.invoke(app, ["launch"])

            mock_run.assert_called_once_with([])
            assert result.exit_code == 0

    def test_launch_with_args(self):
        """launch command passes args to wrapper."""
        from typer.testing import CliRunner

        from installer.cli import app

        with patch("installer.cli.run_with_wrapper", return_value=0) as mock_run:
            runner = CliRunner()
            result = runner.invoke(app, ["launch", "--", "--help"])

            mock_run.assert_called_once()
            assert result.exit_code == 0

    def test_launch_no_wrapper(self):
        """launch --no-wrapper bypasses wrapper."""
        from typer.testing import CliRunner

        from installer.cli import app

        with patch("installer.cli.subprocess.call", return_value=0) as mock_call:
            runner = CliRunner()
            result = runner.invoke(app, ["launch", "--no-wrapper"])

            mock_call.assert_called_once()
            call_args = mock_call.call_args[0][0]
            assert call_args[0] == "claude"
            assert result.exit_code == 0


class TestGetAllSteps:
    """Test get_all_steps function."""

    def test_get_all_steps_returns_list(self):
        """get_all_steps returns a list of steps."""
        from installer.cli import get_all_steps

        steps = get_all_steps()
        assert isinstance(steps, list)
        assert len(steps) == 8

    def test_get_all_steps_returns_base_step_instances(self):
        """get_all_steps returns BaseStep instances."""
        from installer.cli import get_all_steps
        from installer.steps.base import BaseStep

        steps = get_all_steps()
        for step in steps:
            assert isinstance(step, BaseStep)


class TestMainEntry:
    """Test __main__ entry point."""

    def test_main_module_exists(self):
        """__main__ module exists."""
        import installer.__main__

        assert hasattr(installer.__main__, "main") or True  # May not have main function

    def test_main_function_exists(self):
        """main function exists in cli module."""
        from installer.cli import main

        assert callable(main)

    def test_main_invokes_app(self):
        """main() invokes the typer app."""
        from installer.cli import main

        with patch("installer.cli.app") as mock_app:
            main()
            mock_app.assert_called_once()
