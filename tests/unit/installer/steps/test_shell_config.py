"""Tests for shell config step."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestShellConfigStep:
    """Test ShellConfigStep class."""

    def test_shell_config_step_has_correct_name(self):
        """ShellConfigStep has name 'shell_config'."""
        from installer.steps.shell_config import ShellConfigStep

        step = ShellConfigStep()
        assert step.name == "shell_config"

    def test_shell_config_check_always_returns_false(self):
        """ShellConfigStep.check always returns False to ensure alias updates."""
        from installer.context import InstallContext
        from installer.steps.shell_config import ShellConfigStep
        from installer.ui import Console

        step = ShellConfigStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            # Must always return False so run() is called on every install
            assert step.check(ctx) is False

    @patch("installer.steps.shell_config.get_shell_config_files")
    def test_shell_config_check_returns_false_even_with_existing_alias(self, mock_get_files):
        """ShellConfigStep.check returns False even when alias exists."""
        from installer.context import InstallContext
        from installer.steps.shell_config import ShellConfigStep
        from installer.ui import Console

        step = ShellConfigStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create shell config with OLD alias
            bashrc = Path(tmpdir) / ".bashrc"
            bashrc.write_text("# Claude CodePro alias\nalias ccp='old version'\n")
            mock_get_files.return_value = [bashrc]

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            # Must return False so the alias gets updated
            assert step.check(ctx) is False

    @patch("installer.steps.shell_config.get_shell_config_files")
    def test_shell_config_run_adds_alias(self, mock_get_files):
        """ShellConfigStep.run adds ccp alias to shell configs."""
        from installer.context import InstallContext
        from installer.steps.shell_config import ShellConfigStep
        from installer.ui import Console

        step = ShellConfigStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create shell config file
            bashrc = Path(tmpdir) / ".bashrc"
            bashrc.write_text("# existing config\n")
            mock_get_files.return_value = [bashrc]

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

            content = bashrc.read_text()
            # Should contain alias
            assert "ccp" in content or "claude-code" in content

    def test_shell_config_handles_fish_syntax(self):
        """ShellConfigStep uses fish syntax for fish shell."""
        from installer.steps.shell_config import get_alias_line

        bash_line = get_alias_line("bash")
        fish_line = get_alias_line("fish")

        assert "alias" in bash_line
        assert "function" in fish_line or "alias" in fish_line


class TestAliasHelpers:
    """Test shell alias helper functions."""

    def test_get_alias_line_returns_string(self):
        """get_alias_line returns a string."""
        from installer.steps.shell_config import get_alias_line

        result = get_alias_line("bash")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_alias_contains_ccp(self):
        """Alias line contains ccp command."""
        from installer.steps.shell_config import get_alias_line

        result = get_alias_line("bash")
        assert "ccp" in result

    def test_alias_uses_dotenvx(self):
        """Alias uses dotenvx to load environment variables."""
        from installer.steps.shell_config import get_alias_line

        result = get_alias_line("bash")
        assert "dotenvx run --" in result

    def test_alias_uses_nvm(self):
        """Alias sets Node.js version via nvm."""
        from installer.steps.shell_config import get_alias_line

        result = get_alias_line("bash")
        assert "nvm use 22" in result

    def test_alias_detects_ccp_project(self):
        """Alias checks for CCP project before running."""
        from installer.steps.shell_config import get_alias_line

        result = get_alias_line("bash")
        assert ".claude/rules" in result
        assert "/workspaces" in result

    def test_fish_alias_uses_correct_syntax(self):
        """Fish alias uses 'and' instead of '&&' and fish-specific syntax."""
        from installer.steps.shell_config import get_alias_line

        result = get_alias_line("fish")
        # Fish uses 'and' for chaining commands, 'test' instead of '[]'
        assert "test -d" in result or "and" in result
        assert "dotenvx run --" in result
        assert "nvm use 22" in result

    def test_get_alias_line_bash_includes_marker(self):
        """get_alias_line for bash includes CCP_ALIAS_MARKER."""
        from installer.steps.shell_config import CCP_ALIAS_MARKER, get_alias_line

        result = get_alias_line("bash")
        assert CCP_ALIAS_MARKER in result

    def test_get_alias_line_fish_includes_marker(self):
        """get_alias_line for fish includes CCP_ALIAS_MARKER."""
        from installer.steps.shell_config import CCP_ALIAS_MARKER, get_alias_line

        result = get_alias_line("fish")
        assert CCP_ALIAS_MARKER in result


class TestAliasExistsInFile:
    """Test alias_exists_in_file function."""

    def test_alias_exists_in_file_returns_false_for_missing_file(self):
        """alias_exists_in_file returns False when file doesn't exist."""
        from installer.steps.shell_config import alias_exists_in_file

        result = alias_exists_in_file(Path("/nonexistent/file"))
        assert result is False

    def test_alias_exists_in_file_returns_true_when_marker_present(self):
        """alias_exists_in_file returns True when CCP_ALIAS_MARKER present."""
        from installer.steps.shell_config import CCP_ALIAS_MARKER, alias_exists_in_file

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".bashrc"
            config_file.write_text(f"some content\n{CCP_ALIAS_MARKER}\nalias ccp='test'\n")

            result = alias_exists_in_file(config_file)
            assert result is True

    def test_alias_exists_in_file_returns_true_when_alias_present(self):
        """alias_exists_in_file returns True when 'alias ccp' present."""
        from installer.steps.shell_config import alias_exists_in_file

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".bashrc"
            config_file.write_text("alias ccp='some command'\n")

            result = alias_exists_in_file(config_file)
            assert result is True

    def test_alias_exists_in_file_returns_false_when_no_alias(self):
        """alias_exists_in_file returns False when no alias present."""
        from installer.steps.shell_config import alias_exists_in_file

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".bashrc"
            config_file.write_text("export PATH=/usr/bin\n")

            result = alias_exists_in_file(config_file)
            assert result is False


class TestRemoveOldAlias:
    """Test remove_old_alias function."""

    def test_remove_old_alias_returns_false_for_missing_file(self):
        """remove_old_alias returns False when file doesn't exist."""
        from installer.steps.shell_config import remove_old_alias

        result = remove_old_alias(Path("/nonexistent/file"))
        assert result is False

    def test_remove_old_alias_returns_false_when_no_alias(self):
        """remove_old_alias returns False when no alias present."""
        from installer.steps.shell_config import remove_old_alias

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".bashrc"
            config_file.write_text("export PATH=/usr/bin\n")

            result = remove_old_alias(config_file)
            assert result is False

    def test_remove_old_alias_removes_marker_and_alias(self):
        """remove_old_alias removes the marker and alias lines."""
        from installer.steps.shell_config import CCP_ALIAS_MARKER, remove_old_alias

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".bashrc"
            config_file.write_text(
                f"export PATH=/usr/bin\n{CCP_ALIAS_MARKER}\nalias ccp='old command'\nsome other line\n"
            )

            result = remove_old_alias(config_file)
            assert result is True

            content = config_file.read_text()
            assert CCP_ALIAS_MARKER not in content
            assert "alias ccp" not in content
            assert "export PATH=/usr/bin" in content
            assert "some other line" in content

    def test_remove_old_alias_handles_multiline_alias(self):
        """remove_old_alias handles multi-line alias definitions."""
        from installer.steps.shell_config import CCP_ALIAS_MARKER, remove_old_alias

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".bashrc"
            # Multi-line alias that ends with '
            config_file.write_text(
                f"export PATH=/usr/bin\n{CCP_ALIAS_MARKER}\nalias ccp='if [ -d .claude/rules ]; then echo ok; fi'\nother content\n"
            )

            result = remove_old_alias(config_file)
            assert result is True

            content = config_file.read_text()
            assert CCP_ALIAS_MARKER not in content

    def test_remove_old_alias_removes_standalone_alias(self):
        """remove_old_alias removes standalone alias without marker."""
        from installer.steps.shell_config import remove_old_alias

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".bashrc"
            config_file.write_text("export PATH=/usr/bin\nalias ccp='old command'\nother content\n")

            result = remove_old_alias(config_file)
            assert result is True

            content = config_file.read_text()
            assert "alias ccp" not in content


class TestConfigureZshFzf:
    """Test _configure_zsh_fzf function."""

    def test_configure_zsh_fzf_returns_false_if_file_missing(self):
        """_configure_zsh_fzf returns False if file doesn't exist."""
        from installer.steps.shell_config import _configure_zsh_fzf

        result = _configure_zsh_fzf(Path("/nonexistent/file"), None)
        assert result is False

    def test_configure_zsh_fzf_adds_source_line(self):
        """_configure_zsh_fzf adds fzf source line."""
        from installer.steps.shell_config import FZF_MARKER, _configure_zsh_fzf

        with tempfile.TemporaryDirectory() as tmpdir:
            zshrc = Path(tmpdir) / ".zshrc"
            zshrc.write_text("export ZSH=/home/user/.oh-my-zsh\n")

            result = _configure_zsh_fzf(zshrc, None)
            assert result is True

            content = zshrc.read_text()
            assert FZF_MARKER in content

    def test_configure_zsh_fzf_skips_if_already_present(self):
        """_configure_zsh_fzf skips if already configured."""
        from installer.steps.shell_config import FZF_MARKER, _configure_zsh_fzf
        from installer.ui import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            zshrc = Path(tmpdir) / ".zshrc"
            zshrc.write_text(f"export ZSH=/home/user/.oh-my-zsh\n{FZF_MARKER}\n")

            ui = Console(non_interactive=True)
            result = _configure_zsh_fzf(zshrc, ui)
            assert result is False


class TestConfigureZshDotenv:
    """Test _configure_zsh_dotenv function."""

    def test_configure_zsh_dotenv_returns_false_if_file_missing(self):
        """_configure_zsh_dotenv returns False if file doesn't exist."""
        from installer.steps.shell_config import _configure_zsh_dotenv

        result = _configure_zsh_dotenv(Path("/nonexistent/file"), None)
        assert result is False

    def test_configure_zsh_dotenv_adds_plugin(self):
        """_configure_zsh_dotenv adds dotenv plugin."""
        from installer.steps.shell_config import _configure_zsh_dotenv

        with tempfile.TemporaryDirectory() as tmpdir:
            zshrc = Path(tmpdir) / ".zshrc"
            zshrc.write_text("plugins=(git)\nsource $ZSH/oh-my-zsh.sh\n")

            result = _configure_zsh_dotenv(zshrc, None)
            assert result is True

            content = zshrc.read_text()
            assert "dotenv" in content
            assert "ZSH_DOTENV_PROMPT" in content

    def test_configure_zsh_dotenv_skips_if_already_configured(self):
        """_configure_zsh_dotenv skips if already configured."""
        from installer.steps.shell_config import DOTENV_MARKER, _configure_zsh_dotenv
        from installer.ui import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            zshrc = Path(tmpdir) / ".zshrc"
            zshrc.write_text(f"plugins=(git dotenv)\n{DOTENV_MARKER}=false\n")

            ui = Console(non_interactive=True)
            result = _configure_zsh_dotenv(zshrc, ui)
            assert result is False

    def test_configure_zsh_dotenv_appends_if_no_oh_my_zsh_source(self):
        """_configure_zsh_dotenv appends setting if no oh-my-zsh source line."""
        from installer.steps.shell_config import DOTENV_MARKER, _configure_zsh_dotenv

        with tempfile.TemporaryDirectory() as tmpdir:
            zshrc = Path(tmpdir) / ".zshrc"
            zshrc.write_text("export PATH=/usr/bin\n")

            result = _configure_zsh_dotenv(zshrc, None)
            assert result is True

            content = zshrc.read_text()
            assert "ZSH_DOTENV_PROMPT" in content


class TestConfigureQltyPath:
    """Test _configure_qlty_path function."""

    def test_configure_qlty_path_returns_false_if_file_missing(self):
        """_configure_qlty_path returns False if file doesn't exist."""
        from installer.steps.shell_config import _configure_qlty_path

        result = _configure_qlty_path(Path("/nonexistent/file"), None)
        assert result is False

    def test_configure_qlty_path_adds_path_line(self):
        """_configure_qlty_path adds qlty PATH line."""
        from installer.steps.shell_config import QLTY_PATH_MARKER, _configure_qlty_path

        with tempfile.TemporaryDirectory() as tmpdir:
            bashrc = Path(tmpdir) / ".bashrc"
            bashrc.write_text("export PATH=/usr/bin\n")

            result = _configure_qlty_path(bashrc, None)
            assert result is True

            content = bashrc.read_text()
            assert QLTY_PATH_MARKER in content
            assert ".qlty/bin" in content

    def test_configure_qlty_path_skips_if_present(self):
        """_configure_qlty_path skips if already configured."""
        from installer.steps.shell_config import QLTY_PATH_MARKER, _configure_qlty_path
        from installer.ui import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            bashrc = Path(tmpdir) / ".bashrc"
            bashrc.write_text(f"export PATH=/usr/bin\n{QLTY_PATH_MARKER}\nexport PATH=$HOME/.qlty/bin:$PATH\n")

            ui = Console(non_interactive=True)
            result = _configure_qlty_path(bashrc, ui)
            assert result is False

    def test_configure_qlty_path_uses_fish_syntax(self):
        """_configure_qlty_path uses fish syntax for fish config."""
        from installer.steps.shell_config import _configure_qlty_path

        with tempfile.TemporaryDirectory() as tmpdir:
            fish_config = Path(tmpdir) / "config.fish"
            fish_config.write_text("set -gx PATH /usr/bin $PATH\n")

            result = _configure_qlty_path(fish_config, None)
            assert result is True

            content = fish_config.read_text()
            assert "set -gx PATH" in content
            assert ".qlty/bin" in content


class TestSetZshDefaultShell:
    """Test _set_zsh_default_shell function."""

    @patch.dict("os.environ", {"SHELL": "/bin/zsh"})
    def test_set_zsh_default_shell_skips_if_already_zsh(self):
        """_set_zsh_default_shell skips if already zsh."""
        from installer.steps.shell_config import _set_zsh_default_shell
        from installer.ui import Console

        ui = Console(non_interactive=True)
        result = _set_zsh_default_shell(ui)
        assert result is False

    @patch.dict("os.environ", {"SHELL": "/bin/bash"})
    @patch("installer.steps.shell_config.subprocess.run")
    def test_set_zsh_default_shell_returns_false_if_zsh_not_found(self, mock_run):
        """_set_zsh_default_shell returns False if zsh not found."""
        from installer.steps.shell_config import _set_zsh_default_shell
        from installer.ui import Console

        # Mock 'which zsh' returning empty
        mock_run.return_value.stdout = ""

        ui = Console(non_interactive=True)
        result = _set_zsh_default_shell(ui)
        assert result is False

    @patch.dict("os.environ", {"SHELL": "/bin/bash"})
    @patch("installer.steps.shell_config.subprocess.run")
    def test_set_zsh_default_shell_changes_shell(self, mock_run):
        """_set_zsh_default_shell changes shell to zsh."""
        from installer.steps.shell_config import _set_zsh_default_shell
        from installer.ui import Console

        # Mock 'which zsh' returning path, 'chsh' succeeding
        mock_run.side_effect = [
            type("Result", (), {"stdout": "/usr/bin/zsh"})(),  # which zsh
            None,  # chsh succeeds
        ]

        ui = Console(non_interactive=True)
        result = _set_zsh_default_shell(ui)
        assert result is True

    @patch.dict("os.environ", {"SHELL": "/bin/bash"})
    @patch("installer.steps.shell_config.subprocess.run")
    def test_set_zsh_default_shell_handles_chsh_error(self, mock_run):
        """_set_zsh_default_shell handles chsh failure."""
        import subprocess

        from installer.steps.shell_config import _set_zsh_default_shell
        from installer.ui import Console

        # Mock 'which zsh' returning path, 'chsh' failing
        mock_run.side_effect = [
            type("Result", (), {"stdout": "/usr/bin/zsh"})(),  # which zsh
            subprocess.CalledProcessError(1, "chsh"),  # chsh fails
        ]

        ui = Console(non_interactive=True)
        result = _set_zsh_default_shell(ui)
        assert result is False


class TestShellConfigRollback:
    """Test ShellConfigStep rollback."""

    @patch("installer.steps.shell_config.get_shell_config_files")
    def test_rollback_removes_alias(self, mock_get_files):
        """rollback removes alias from modified config files."""
        from installer.context import InstallContext
        from installer.steps.shell_config import CCP_ALIAS_MARKER, ShellConfigStep
        from installer.ui import Console

        step = ShellConfigStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            bashrc = Path(tmpdir) / ".bashrc"
            bashrc.write_text(f"export PATH=/usr/bin\n{CCP_ALIAS_MARKER}\nalias ccp='test'\nother content\n")
            mock_get_files.return_value = [bashrc]

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            ctx.config["modified_shell_configs"] = [str(bashrc)]

            step.rollback(ctx)

            content = bashrc.read_text()
            assert CCP_ALIAS_MARKER not in content
            assert "alias ccp" not in content
            assert "export PATH=/usr/bin" in content
            assert "other content" in content

    def test_rollback_handles_missing_file(self):
        """rollback handles case where config file no longer exists."""
        from installer.context import InstallContext
        from installer.steps.shell_config import ShellConfigStep
        from installer.ui import Console

        step = ShellConfigStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            ctx.config["modified_shell_configs"] = ["/nonexistent/.bashrc"]

            # Should not raise
            step.rollback(ctx)

    def test_rollback_handles_empty_config(self):
        """rollback handles case where no files were modified."""
        from installer.context import InstallContext
        from installer.steps.shell_config import ShellConfigStep
        from installer.ui import Console

        step = ShellConfigStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            # No modified_shell_configs in ctx.config

            # Should not raise
            step.rollback(ctx)


class TestShellConfigRunBranches:
    """Test ShellConfigStep.run branch coverage."""

    @patch("installer.steps.shell_config.get_shell_config_files")
    @patch("installer.steps.shell_config.is_in_devcontainer")
    def test_run_configures_zsh_in_devcontainer(self, mock_is_devcontainer, mock_get_files):
        """run configures zsh fzf and dotenv when in devcontainer."""
        from installer.context import InstallContext
        from installer.steps.shell_config import ShellConfigStep
        from installer.ui import Console

        mock_is_devcontainer.return_value = True

        step = ShellConfigStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create zshrc for devcontainer configuration
            zshrc = Path(tmpdir) / ".zshrc"
            zshrc.write_text("plugins=(git)\nsource $ZSH/oh-my-zsh.sh\n")

            with patch("installer.steps.shell_config.Path.home", return_value=Path(tmpdir)):
                mock_get_files.return_value = []

                ctx = InstallContext(
                    project_dir=Path(tmpdir),
                    ui=Console(non_interactive=True),
                )

                step.run(ctx)

                content = zshrc.read_text()
                assert "fzf" in content or "dotenv" in content

    @patch("installer.steps.shell_config.get_shell_config_files")
    def test_run_handles_fish_config(self, mock_get_files):
        """run uses fish syntax for fish config files."""
        from installer.context import InstallContext
        from installer.steps.shell_config import ShellConfigStep
        from installer.ui import Console

        step = ShellConfigStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            fish_config = Path(tmpdir) / "config.fish"
            fish_config.write_text("set -gx PATH /usr/bin $PATH\n")
            mock_get_files.return_value = [fish_config]

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

            content = fish_config.read_text()
            assert "alias ccp" in content
            # Fish syntax should use 'test -d' not '[ -d'
            assert "test -d" in content

    @patch("installer.steps.shell_config.get_shell_config_files")
    def test_run_updates_existing_alias(self, mock_get_files):
        """run updates existing alias when present."""
        from installer.context import InstallContext
        from installer.steps.shell_config import CCP_ALIAS_MARKER, ShellConfigStep
        from installer.ui import Console

        step = ShellConfigStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            bashrc = Path(tmpdir) / ".bashrc"
            bashrc.write_text(f"export PATH=/usr/bin\n{CCP_ALIAS_MARKER}\nalias ccp='old version'\n")
            mock_get_files.return_value = [bashrc]

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

            content = bashrc.read_text()
            # Should have new alias, not old
            assert "nvm use 22" in content
            assert str(bashrc) in ctx.config["modified_shell_configs"]

    @patch("installer.steps.shell_config.get_shell_config_files")
    @patch("installer.steps.shell_config._configure_qlty_path")
    @patch("installer.steps.shell_config.is_in_devcontainer")
    def test_run_handles_write_error(self, mock_is_devcontainer, mock_qlty_path, mock_get_files):
        """run handles OSError when writing config."""
        from installer.context import InstallContext
        from installer.steps.shell_config import ShellConfigStep
        from installer.ui import Console

        mock_is_devcontainer.return_value = False
        mock_qlty_path.return_value = False

        step = ShellConfigStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            bashrc = Path(tmpdir) / ".bashrc"
            bashrc.write_text("export PATH=/usr/bin\n")
            mock_get_files.return_value = [bashrc]

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )

            # Make the file read-only to trigger write error
            bashrc.chmod(0o444)

            try:
                # Should not raise, just log warning
                step.run(ctx)
            finally:
                # Restore permissions for cleanup
                bashrc.chmod(0o644)
