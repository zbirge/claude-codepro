"""Tests for dependencies step."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestDependenciesStep:
    """Test DependenciesStep class."""

    def test_dependencies_step_has_correct_name(self):
        """DependenciesStep has name 'dependencies'."""
        from installer.steps.dependencies import DependenciesStep

        step = DependenciesStep()
        assert step.name == "dependencies"

    def test_dependencies_check_returns_false(self):
        """DependenciesStep.check returns False (always runs)."""
        from installer.context import InstallContext
        from installer.steps.dependencies import DependenciesStep
        from installer.ui import Console

        step = DependenciesStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            # Dependencies always need to be checked
            assert step.check(ctx) is False

    @patch("installer.steps.dependencies.install_dotenvx")
    @patch("installer.steps.dependencies.run_qlty_check")
    @patch("installer.steps.dependencies.install_qlty")
    @patch("installer.steps.dependencies.install_vexor")
    @patch("installer.steps.dependencies.install_context7")
    @patch("installer.steps.dependencies.install_claude_mem")
    @patch("installer.steps.dependencies.install_typescript_lsp")
    @patch("installer.steps.dependencies.install_claude_code")
    @patch("installer.steps.dependencies.install_nodejs")
    def test_dependencies_run_installs_core(
        self,
        mock_nodejs,
        mock_claude,
        mock_typescript_lsp,
        mock_claude_mem,
        mock_context7,
        mock_vexor,
        mock_qlty,
        mock_qlty_check,
        mock_dotenvx,
    ):
        """DependenciesStep installs core dependencies."""
        from installer.context import InstallContext
        from installer.steps.dependencies import DependenciesStep
        from installer.ui import Console

        # Setup mocks
        mock_nodejs.return_value = True
        mock_claude.return_value = (True, "latest")  # Returns (success, version)
        mock_typescript_lsp.return_value = True
        mock_claude_mem.return_value = True
        mock_context7.return_value = True
        mock_vexor.return_value = True
        mock_qlty.return_value = (True, False)
        mock_dotenvx.return_value = True

        step = DependenciesStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                install_python=False,
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

            # Core dependencies should be installed
            mock_nodejs.assert_called_once()
            mock_typescript_lsp.assert_called_once()
            mock_claude.assert_called_once()

    @patch("installer.steps.dependencies.install_dotenvx")
    @patch("installer.steps.dependencies.run_qlty_check")
    @patch("installer.steps.dependencies.install_qlty")
    @patch("installer.steps.dependencies.install_vexor")
    @patch("installer.steps.dependencies.install_context7")
    @patch("installer.steps.dependencies.install_claude_mem")
    @patch("installer.steps.dependencies.install_pyright_lsp")
    @patch("installer.steps.dependencies.install_typescript_lsp")
    @patch("installer.steps.dependencies.install_claude_code")
    @patch("installer.steps.dependencies.install_python_tools")
    @patch("installer.steps.dependencies.install_uv")
    @patch("installer.steps.dependencies.install_nodejs")
    def test_dependencies_installs_python_when_enabled(
        self,
        mock_nodejs,
        mock_uv,
        mock_python_tools,
        mock_claude,
        mock_typescript_lsp,
        mock_pyright_lsp,
        mock_claude_mem,
        mock_context7,
        mock_vexor,
        mock_qlty,
        mock_qlty_check,
        mock_dotenvx,
    ):
        """DependenciesStep installs Python tools when enabled."""
        from installer.context import InstallContext
        from installer.steps.dependencies import DependenciesStep
        from installer.ui import Console

        # Setup mocks
        mock_nodejs.return_value = True
        mock_uv.return_value = True
        mock_python_tools.return_value = True
        mock_claude.return_value = (True, "latest")  # Returns (success, version)
        mock_typescript_lsp.return_value = True
        mock_pyright_lsp.return_value = True
        mock_claude_mem.return_value = True
        mock_context7.return_value = True
        mock_vexor.return_value = True
        mock_qlty.return_value = (True, False)
        mock_dotenvx.return_value = True

        step = DependenciesStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                install_python=True,
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

            # Python tools should be installed
            mock_uv.assert_called_once()
            mock_python_tools.assert_called_once()
            mock_pyright_lsp.assert_called_once()


class TestDependencyInstallFunctions:
    """Test individual dependency install functions."""

    def test_install_nodejs_exists(self):
        """install_nodejs function exists."""
        from installer.steps.dependencies import install_nodejs

        assert callable(install_nodejs)

    def test_install_claude_code_exists(self):
        """install_claude_code function exists."""
        from installer.steps.dependencies import install_claude_code

        assert callable(install_claude_code)

    def test_install_uv_exists(self):
        """install_uv function exists."""
        from installer.steps.dependencies import install_uv

        assert callable(install_uv)

    def test_install_python_tools_exists(self):
        """install_python_tools function exists."""
        from installer.steps.dependencies import install_python_tools

        assert callable(install_python_tools)

    def test_install_dotenvx_exists(self):
        """install_dotenvx function exists."""
        from installer.steps.dependencies import install_dotenvx

        assert callable(install_dotenvx)


class TestClaudeCodeInstall:
    """Test Claude Code installation."""

    @patch("installer.steps.dependencies._get_forced_claude_version", return_value=None)
    @patch("installer.steps.dependencies._configure_gitlab_mcp")
    @patch("installer.steps.dependencies._configure_github_mcp")
    @patch("installer.steps.dependencies._configure_firecrawl_mcp")
    @patch("installer.steps.dependencies._configure_claude_defaults")
    @patch("subprocess.run")
    @patch("installer.steps.dependencies._remove_native_claude_binaries")
    def test_install_claude_code_removes_native_binaries(
        self, mock_remove, mock_run, mock_config, mock_firecrawl, mock_github, mock_gitlab, mock_version
    ):
        """install_claude_code removes native binaries before npm install."""
        from installer.steps.dependencies import install_claude_code

        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            install_claude_code(Path(tmpdir))

        mock_remove.assert_called_once()

    @patch("installer.steps.dependencies._get_forced_claude_version", return_value=None)
    @patch("installer.steps.dependencies._configure_gitlab_mcp")
    @patch("installer.steps.dependencies._configure_github_mcp")
    @patch("installer.steps.dependencies._configure_firecrawl_mcp")
    @patch("installer.steps.dependencies._configure_claude_defaults")
    @patch("subprocess.run")
    @patch("installer.steps.dependencies._remove_native_claude_binaries")
    def test_install_claude_code_always_runs_npm_install(
        self, mock_remove, mock_run, mock_config, mock_firecrawl, mock_github, mock_gitlab, mock_version
    ):
        """install_claude_code always runs npm install (upgrades if exists)."""
        from installer.steps.dependencies import install_claude_code

        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            success, version = install_claude_code(Path(tmpdir))

        assert success is True
        assert version == "latest"
        # Verify npm install was called
        npm_calls = [c for c in mock_run.call_args_list if "npm install" in str(c)]
        assert len(npm_calls) >= 1

    @patch("installer.steps.dependencies._get_forced_claude_version", return_value=None)
    @patch("installer.steps.dependencies._configure_gitlab_mcp")
    @patch("installer.steps.dependencies._configure_github_mcp")
    @patch("installer.steps.dependencies._configure_firecrawl_mcp")
    @patch("installer.steps.dependencies._configure_claude_defaults")
    @patch("subprocess.run")
    @patch("installer.steps.dependencies._remove_native_claude_binaries")
    def test_install_claude_code_configures_defaults(
        self, mock_remove, mock_run, mock_config, mock_firecrawl, mock_github, mock_gitlab, mock_version
    ):
        """install_claude_code configures Claude defaults after npm install."""
        from installer.steps.dependencies import install_claude_code

        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            install_claude_code(Path(tmpdir))

        mock_config.assert_called_once()

    @patch("installer.steps.dependencies._get_forced_claude_version", return_value=None)
    @patch("installer.steps.dependencies._configure_gitlab_mcp")
    @patch("installer.steps.dependencies._configure_github_mcp")
    @patch("installer.steps.dependencies._configure_firecrawl_mcp")
    @patch("installer.steps.dependencies._configure_claude_defaults")
    @patch("subprocess.run")
    @patch("installer.steps.dependencies._remove_native_claude_binaries")
    def test_install_claude_code_configures_firecrawl_mcp(
        self, mock_remove, mock_run, mock_config, mock_firecrawl, mock_github, mock_gitlab, mock_version
    ):
        """install_claude_code configures Firecrawl MCP after npm install."""
        from installer.steps.dependencies import install_claude_code

        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            install_claude_code(Path(tmpdir))

        mock_firecrawl.assert_called_once()

    @patch("installer.steps.dependencies._get_forced_claude_version", return_value=None)
    @patch("installer.steps.dependencies._configure_gitlab_mcp")
    @patch("installer.steps.dependencies._configure_github_mcp")
    @patch("installer.steps.dependencies._configure_firecrawl_mcp")
    @patch("installer.steps.dependencies._configure_claude_defaults")
    @patch("subprocess.run")
    @patch("installer.steps.dependencies._remove_native_claude_binaries")
    def test_install_claude_code_configures_github_mcp(
        self, mock_remove, mock_run, mock_config, mock_firecrawl, mock_github, mock_gitlab, mock_version
    ):
        """install_claude_code configures GitHub MCP after npm install."""
        from installer.steps.dependencies import install_claude_code

        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            install_claude_code(Path(tmpdir))

        mock_github.assert_called_once()

    @patch("installer.steps.dependencies._get_forced_claude_version", return_value=None)
    @patch("installer.steps.dependencies._configure_gitlab_mcp")
    @patch("installer.steps.dependencies._configure_github_mcp")
    @patch("installer.steps.dependencies._configure_firecrawl_mcp")
    @patch("installer.steps.dependencies._configure_claude_defaults")
    @patch("subprocess.run")
    @patch("installer.steps.dependencies._remove_native_claude_binaries")
    def test_install_claude_code_configures_gitlab_mcp(
        self, mock_remove, mock_run, mock_config, mock_firecrawl, mock_github, mock_gitlab, mock_version
    ):
        """install_claude_code configures GitLab MCP after npm install."""
        from installer.steps.dependencies import install_claude_code

        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            install_claude_code(Path(tmpdir))

        mock_gitlab.assert_called_once()

    def test_patch_claude_config_creates_file(self):
        """_patch_claude_config creates config file if it doesn't exist."""
        import json

        from installer.steps.dependencies import _patch_claude_config

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _patch_claude_config({"test_key": "test_value"})

                assert result is True
                config_path = Path(tmpdir) / ".claude.json"
                assert config_path.exists()
                config = json.loads(config_path.read_text())
                assert config["test_key"] == "test_value"

    def test_patch_claude_config_merges_existing(self):
        """_patch_claude_config merges with existing config."""
        import json

        from installer.steps.dependencies import _patch_claude_config

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".claude.json"
            config_path.write_text(json.dumps({"existing_key": "existing_value"}))

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _patch_claude_config({"new_key": "new_value"})

                assert result is True
                config = json.loads(config_path.read_text())
                assert config["existing_key"] == "existing_value"
                assert config["new_key"] == "new_value"

    def test_configure_claude_defaults_sets_respect_gitignore_false(self):
        """_configure_claude_defaults sets respectGitignore to False."""
        import json

        from installer.steps.dependencies import _configure_claude_defaults

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_claude_defaults()

                assert result is True
                config_path = Path(tmpdir) / ".claude.json"
                config = json.loads(config_path.read_text())
                assert config["respectGitignore"] is False


class TestGitHubMcpConfig:
    """Test GitHub MCP server configuration."""

    def test_configure_github_mcp_creates_config(self):
        """_configure_github_mcp creates config with mcpServers if not exists."""
        import json

        from installer.steps.dependencies import _configure_github_mcp

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_github_mcp()

                assert result is True
                config_path = Path(tmpdir) / ".claude.json"
                assert config_path.exists()
                config = json.loads(config_path.read_text())
                assert "mcpServers" in config
                assert "github" in config["mcpServers"]
                assert config["mcpServers"]["github"]["command"] == "npx"
                assert config["mcpServers"]["github"]["args"] == ["-y", "@modelcontextprotocol/server-github"]
                assert config["mcpServers"]["github"]["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] == "${GITHUB_PERSONAL_ACCESS_TOKEN}"

    def test_configure_github_mcp_preserves_existing_mcp_servers(self):
        """_configure_github_mcp preserves other MCP servers."""
        import json

        from installer.steps.dependencies import _configure_github_mcp

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".claude.json"
            existing_config = {"mcpServers": {"other_server": {"command": "other", "args": ["--flag"]}}}
            config_path.write_text(json.dumps(existing_config))

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_github_mcp()

                assert result is True
                config = json.loads(config_path.read_text())
                assert "other_server" in config["mcpServers"]
                assert config["mcpServers"]["other_server"]["command"] == "other"
                assert "github" in config["mcpServers"]

    def test_configure_github_mcp_skips_if_already_exists(self):
        """_configure_github_mcp skips if github already configured."""
        import json

        from installer.steps.dependencies import _configure_github_mcp

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".claude.json"
            existing_config = {"mcpServers": {"github": {"command": "custom", "args": ["custom"]}}}
            config_path.write_text(json.dumps(existing_config))

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_github_mcp()

                assert result is True
                config = json.loads(config_path.read_text())
                # Should preserve custom config, not overwrite
                assert config["mcpServers"]["github"]["command"] == "custom"


class TestGitLabMcpConfig:
    """Test GitLab MCP server configuration."""

    def test_configure_gitlab_mcp_creates_config(self):
        """_configure_gitlab_mcp creates config with mcpServers if not exists."""
        import json

        from installer.steps.dependencies import _configure_gitlab_mcp

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_gitlab_mcp()

                assert result is True
                config_path = Path(tmpdir) / ".claude.json"
                assert config_path.exists()
                config = json.loads(config_path.read_text())
                assert "mcpServers" in config
                assert "gitlab" in config["mcpServers"]
                assert config["mcpServers"]["gitlab"]["command"] == "npx"
                assert config["mcpServers"]["gitlab"]["args"] == ["-y", "@modelcontextprotocol/server-gitlab"]
                assert config["mcpServers"]["gitlab"]["env"]["GITLAB_PERSONAL_ACCESS_TOKEN"] == "${GITLAB_PERSONAL_ACCESS_TOKEN}"

    def test_configure_gitlab_mcp_preserves_existing_mcp_servers(self):
        """_configure_gitlab_mcp preserves other MCP servers."""
        import json

        from installer.steps.dependencies import _configure_gitlab_mcp

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".claude.json"
            existing_config = {"mcpServers": {"firecrawl": {"command": "npx", "args": ["firecrawl-mcp"]}}}
            config_path.write_text(json.dumps(existing_config))

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_gitlab_mcp()

                assert result is True
                config = json.loads(config_path.read_text())
                assert "firecrawl" in config["mcpServers"]
                assert "gitlab" in config["mcpServers"]

    def test_configure_gitlab_mcp_skips_if_already_exists(self):
        """_configure_gitlab_mcp skips if gitlab already configured."""
        import json

        from installer.steps.dependencies import _configure_gitlab_mcp

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".claude.json"
            existing_config = {"mcpServers": {"gitlab": {"command": "custom", "args": ["custom"]}}}
            config_path.write_text(json.dumps(existing_config))

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_gitlab_mcp()

                assert result is True
                config = json.loads(config_path.read_text())
                # Should preserve custom config, not overwrite
                assert config["mcpServers"]["gitlab"]["command"] == "custom"


class TestFirecrawlMcpConfig:
    """Test Firecrawl MCP server configuration."""

    def test_configure_firecrawl_mcp_creates_config(self):
        """_configure_firecrawl_mcp creates config with mcpServers if not exists."""
        import json

        from installer.steps.dependencies import _configure_firecrawl_mcp

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_firecrawl_mcp()

                assert result is True
                config_path = Path(tmpdir) / ".claude.json"
                assert config_path.exists()
                config = json.loads(config_path.read_text())
                assert "mcpServers" in config
                assert "firecrawl" in config["mcpServers"]
                assert config["mcpServers"]["firecrawl"]["command"] == "npx"
                assert config["mcpServers"]["firecrawl"]["args"] == ["-y", "firecrawl-mcp"]
                assert config["mcpServers"]["firecrawl"]["env"]["FIRECRAWL_API_KEY"] == "${FIRECRAWL_API_KEY}"

    def test_configure_firecrawl_mcp_preserves_existing_mcp_servers(self):
        """_configure_firecrawl_mcp preserves other MCP servers."""
        import json

        from installer.steps.dependencies import _configure_firecrawl_mcp

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".claude.json"
            existing_config = {"mcpServers": {"other_server": {"command": "other", "args": ["--flag"]}}}
            config_path.write_text(json.dumps(existing_config))

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_firecrawl_mcp()

                assert result is True
                config = json.loads(config_path.read_text())
                assert "other_server" in config["mcpServers"]
                assert config["mcpServers"]["other_server"]["command"] == "other"
                assert "firecrawl" in config["mcpServers"]

    def test_configure_firecrawl_mcp_skips_if_already_exists(self):
        """_configure_firecrawl_mcp skips if firecrawl already configured."""
        import json

        from installer.steps.dependencies import _configure_firecrawl_mcp

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".claude.json"
            existing_config = {"mcpServers": {"firecrawl": {"command": "custom", "args": ["custom"]}}}
            config_path.write_text(json.dumps(existing_config))

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_firecrawl_mcp()

                assert result is True
                config = json.loads(config_path.read_text())
                # Should preserve custom config, not overwrite
                assert config["mcpServers"]["firecrawl"]["command"] == "custom"

    def test_configure_firecrawl_mcp_adds_to_existing_config(self):
        """_configure_firecrawl_mcp adds mcpServers to existing config."""
        import json

        from installer.steps.dependencies import _configure_firecrawl_mcp

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".claude.json"
            existing_config = {"theme": "dark", "verbose": True}
            config_path.write_text(json.dumps(existing_config))

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_firecrawl_mcp()

                assert result is True
                config = json.loads(config_path.read_text())
                assert config["theme"] == "dark"
                assert config["verbose"] is True
                assert "mcpServers" in config
                assert "firecrawl" in config["mcpServers"]


class TestDotenvxInstall:
    """Test dotenvx installation."""

    @patch("installer.steps.dependencies.command_exists")
    @patch("subprocess.run")
    def test_install_dotenvx_calls_native_installer(self, mock_run, mock_cmd_exists):
        """install_dotenvx calls native shell installer."""
        from installer.steps.dependencies import install_dotenvx

        mock_cmd_exists.return_value = False
        mock_run.return_value = MagicMock(returncode=0)

        result = install_dotenvx()

        # Should call curl shell installer
        mock_run.assert_called()
        call_args = mock_run.call_args[0][0]
        assert "bash" in call_args
        assert "dotenvx.sh" in call_args[2]  # The curl command is the 3rd arg

    @patch("installer.steps.dependencies.command_exists")
    def test_install_dotenvx_skips_if_exists(self, mock_cmd_exists):
        """install_dotenvx skips if already installed."""
        from installer.steps.dependencies import install_dotenvx

        mock_cmd_exists.return_value = True

        result = install_dotenvx()

        assert result is True


class TestTypescriptLspInstall:
    """Test TypeScript language server plugin installation."""

    def test_install_typescript_lsp_exists(self):
        """install_typescript_lsp function exists."""
        from installer.steps.dependencies import install_typescript_lsp

        assert callable(install_typescript_lsp)

    @patch("subprocess.run")
    def test_install_typescript_lsp_calls_npm_and_plugin(self, mock_run):
        """install_typescript_lsp calls npm install and claude plugin install."""
        from installer.steps.dependencies import install_typescript_lsp

        mock_run.return_value = MagicMock(returncode=0)

        result = install_typescript_lsp()

        assert mock_run.call_count >= 2
        # Check npm install call
        first_call = mock_run.call_args_list[0][0][0]
        assert "bash" in first_call
        assert "typescript-language-server" in first_call[2]
        # Check marketplace add call
        second_call = mock_run.call_args_list[1][0][0]
        assert "claude plugin marketplace add anthropics/claude-plugins-official" in second_call[2]
        # Check plugin install call
        third_call = mock_run.call_args_list[2][0][0]
        assert "claude plugin install typescript-lsp" in third_call[2]


class TestPyrightLspInstall:
    """Test Pyright language server plugin installation."""

    def test_install_pyright_lsp_exists(self):
        """install_pyright_lsp function exists."""
        from installer.steps.dependencies import install_pyright_lsp

        assert callable(install_pyright_lsp)

    @patch("subprocess.run")
    def test_install_pyright_lsp_calls_npm_and_plugin(self, mock_run):
        """install_pyright_lsp calls npm install and claude plugin install."""
        from installer.steps.dependencies import install_pyright_lsp

        mock_run.return_value = MagicMock(returncode=0)

        result = install_pyright_lsp()

        assert mock_run.call_count >= 3
        # Check npm install call
        first_call = mock_run.call_args_list[0][0][0]
        assert "bash" in first_call
        assert "pyright" in first_call[2]
        # Check marketplace add call
        second_call = mock_run.call_args_list[1][0][0]
        assert "claude plugin marketplace add anthropics/claude-plugins-official" in second_call[2]
        # Check plugin install call
        third_call = mock_run.call_args_list[2][0][0]
        assert "claude plugin install pyright-lsp" in third_call[2]


class TestClaudeMemInstall:
    """Test claude-mem plugin installation."""

    def test_install_claude_mem_exists(self):
        """install_claude_mem function exists."""
        from installer.steps.dependencies import install_claude_mem

        assert callable(install_claude_mem)

    @patch("subprocess.run")
    def test_install_claude_mem_uses_plugin_system(self, mock_run):
        """install_claude_mem uses claude plugin marketplace and install."""
        from installer.steps.dependencies import install_claude_mem

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = install_claude_mem()

        assert mock_run.call_count >= 2
        # First call adds marketplace
        first_call = mock_run.call_args_list[0][0][0]
        assert "claude plugin marketplace add" in first_call[2]
        assert "maxritter/claude-mem" in first_call[2]
        # Second call installs plugin
        second_call = mock_run.call_args_list[1][0][0]
        assert "claude plugin install claude-mem" in second_call[2]

    @patch("subprocess.run")
    def test_install_claude_mem_succeeds_if_marketplace_already_added(self, mock_run):
        """install_claude_mem succeeds when marketplace already exists."""
        from installer.steps.dependencies import install_claude_mem

        def side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args", [])
            if isinstance(cmd, list) and "marketplace add" in cmd[2]:
                return MagicMock(returncode=1, stderr="already installed", stdout="")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = side_effect

        result = install_claude_mem()

        assert result is True


class TestContext7Install:
    """Test Context7 plugin installation."""

    def test_install_context7_exists(self):
        """install_context7 function exists."""
        from installer.steps.dependencies import install_context7

        assert callable(install_context7)

    @patch("subprocess.run")
    def test_install_context7_calls_plugin_install(self, mock_run):
        """install_context7 calls claude plugin install context7."""
        from installer.steps.dependencies import install_context7

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = install_context7()

        assert result is True
        mock_run.assert_called()
        call_args = mock_run.call_args[0][0]
        assert "claude plugin install context7" in call_args[2]


class TestVexorInstall:
    """Test Vexor semantic search installation."""

    def test_install_vexor_exists(self):
        """install_vexor function exists."""
        from installer.steps.dependencies import install_vexor

        assert callable(install_vexor)

    @patch("installer.steps.dependencies._configure_vexor_defaults")
    @patch("installer.steps.dependencies.has_nvidia_gpu")
    @patch("installer.steps.dependencies.command_exists")
    def test_install_vexor_skips_if_exists(self, mock_cmd_exists, mock_gpu, mock_config):
        """install_vexor skips installation if already installed."""
        from installer.steps.dependencies import install_vexor

        mock_cmd_exists.return_value = True
        mock_gpu.return_value = False
        mock_config.return_value = True

        result = install_vexor()

        assert result is True
        mock_config.assert_called_once_with("cpu", None)

    @patch("installer.steps.dependencies._configure_vexor_defaults")
    @patch("installer.steps.dependencies.has_nvidia_gpu")
    @patch("installer.steps.dependencies.subprocess.run")
    @patch("installer.steps.dependencies.command_exists")
    def test_install_vexor_uses_uv_tool(self, mock_cmd_exists, mock_run, mock_gpu, mock_config):
        """install_vexor uses uv tool install."""
        from installer.steps.dependencies import install_vexor

        mock_cmd_exists.return_value = False
        mock_gpu.return_value = False
        mock_run.return_value = MagicMock(returncode=0)
        mock_config.return_value = True

        result = install_vexor()

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ["uv", "tool", "install", "vexor[local]"]
        mock_config.assert_called_once_with("cpu", None)

    def test_configure_vexor_defaults_creates_config(self):
        """_configure_vexor_defaults creates config file with cpu defaults."""
        import json

        from installer.steps.dependencies import _configure_vexor_defaults

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_vexor_defaults()  # Default is cpu mode

                assert result is True
                config_path = Path(tmpdir) / ".vexor" / "config.json"
                assert config_path.exists()
                config = json.loads(config_path.read_text())
                assert config["provider"] == "local"
                assert config["local_cuda"] is False
                assert config["rerank"] == "bm25"

    def test_configure_vexor_defaults_merges_existing(self):
        """_configure_vexor_defaults merges with existing config."""
        import json

        from installer.steps.dependencies import _configure_vexor_defaults

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".vexor"
            config_dir.mkdir()
            config_path = config_dir / "config.json"
            config_path.write_text(json.dumps({"custom_key": "custom_value"}))

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_vexor_defaults()

                assert result is True
                config = json.loads(config_path.read_text())
                assert config["custom_key"] == "custom_value"
                assert config["provider"] == "local"


class TestVexorCudaSupport:
    """Test vexor CUDA installation logic."""

    @patch("installer.steps.dependencies._configure_vexor_defaults")
    @patch("installer.steps.dependencies._fix_vexor_onnxruntime_conflict")
    @patch("installer.steps.dependencies.has_nvidia_gpu")
    @patch("installer.steps.dependencies.command_exists")
    @patch("installer.steps.dependencies.subprocess.run")
    def test_install_vexor_with_cuda_when_gpu_available(self, mock_run, mock_exists, mock_gpu, mock_fix, mock_config):
        """install_vexor installs with [local-cuda] when GPU available."""
        from installer.steps.dependencies import install_vexor

        mock_exists.return_value = False  # vexor not installed
        mock_gpu.return_value = True  # GPU available
        mock_run.return_value = MagicMock(returncode=0)
        mock_fix.return_value = True
        mock_config.return_value = True

        result = install_vexor()

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "vexor[local-cuda]" in call_args
        mock_fix.assert_called_once()
        mock_config.assert_called_once_with("cuda", None)

    @patch("installer.steps.dependencies._configure_vexor_defaults")
    @patch("installer.steps.dependencies.has_nvidia_gpu")
    @patch("installer.steps.dependencies.command_exists")
    @patch("installer.steps.dependencies.subprocess.run")
    def test_install_vexor_without_cuda_when_no_gpu(self, mock_run, mock_exists, mock_gpu, mock_config):
        """install_vexor installs without CUDA when no GPU."""
        from installer.steps.dependencies import install_vexor

        mock_exists.return_value = False  # vexor not installed
        mock_gpu.return_value = False  # No GPU
        mock_run.return_value = MagicMock(returncode=0)
        mock_config.return_value = True

        result = install_vexor()

        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "vexor[local]" in call_args
        assert "[local-cuda]" not in str(call_args)
        mock_config.assert_called_once_with("cpu", None)

    @patch("installer.steps.dependencies._fix_vexor_onnxruntime_conflict")
    @patch("installer.steps.dependencies._configure_vexor_defaults")
    @patch("installer.steps.dependencies.has_nvidia_gpu")
    @patch("installer.steps.dependencies.command_exists")
    def test_install_vexor_existing_with_gpu_fixes_conflict(self, mock_exists, mock_gpu, mock_config, mock_fix):
        """install_vexor fixes onnxruntime conflict when vexor already installed with GPU."""
        from installer.steps.dependencies import install_vexor

        mock_exists.return_value = True  # vexor already installed
        mock_gpu.return_value = True  # GPU available
        mock_config.return_value = True
        mock_fix.return_value = True

        result = install_vexor()

        assert result is True
        mock_fix.assert_called_once()
        mock_config.assert_called_once_with("cuda", None)

    @patch("installer.steps.dependencies._configure_vexor_defaults")
    @patch("installer.steps.dependencies.has_nvidia_gpu")
    @patch("installer.steps.dependencies.command_exists")
    def test_install_vexor_existing_without_gpu_no_conflict_fix(self, mock_exists, mock_gpu, mock_config):
        """install_vexor skips conflict fix when vexor already installed without GPU."""
        from installer.steps.dependencies import install_vexor

        mock_exists.return_value = True  # vexor already installed
        mock_gpu.return_value = False  # No GPU
        mock_config.return_value = True

        result = install_vexor()

        assert result is True
        mock_config.assert_called_once_with("cpu", None)

    def test_configure_vexor_defaults_cuda_mode(self):
        """_configure_vexor_defaults sets local_cuda True, provider local, and e5 model for cuda mode."""
        import json

        from installer.steps.dependencies import _configure_vexor_defaults

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_vexor_defaults(provider_mode="cuda")

                assert result is True
                config_path = Path(tmpdir) / ".vexor" / "config.json"
                config = json.loads(config_path.read_text())
                assert config["local_cuda"] is True
                assert config["provider"] == "local"
                assert config["model"] == "intfloat/multilingual-e5-small"

    def test_configure_vexor_defaults_cpu_mode(self):
        """_configure_vexor_defaults sets local_cuda False, provider local, and e5 model for cpu mode."""
        import json

        from installer.steps.dependencies import _configure_vexor_defaults

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_vexor_defaults(provider_mode="cpu")

                assert result is True
                config_path = Path(tmpdir) / ".vexor" / "config.json"
                config = json.loads(config_path.read_text())
                assert config["local_cuda"] is False
                assert config["provider"] == "local"
                assert config["model"] == "intfloat/multilingual-e5-small"

    def test_configure_vexor_defaults_openai_mode_with_key(self):
        """_configure_vexor_defaults sets openai provider and saves api_key."""
        import json

        from installer.steps.dependencies import _configure_vexor_defaults

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_vexor_defaults(provider_mode="openai", api_key="sk-test123")

                assert result is True
                config_path = Path(tmpdir) / ".vexor" / "config.json"
                config = json.loads(config_path.read_text())
                assert config["local_cuda"] is False
                assert config["provider"] == "openai"
                assert config["api_key"] == "sk-test123"
                assert config["model"] == "text-embedding-3-small"

    def test_configure_vexor_defaults_openai_mode_without_key(self):
        """_configure_vexor_defaults sets openai provider without api_key if not provided."""
        import json

        from installer.steps.dependencies import _configure_vexor_defaults

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _configure_vexor_defaults(provider_mode="openai")

                assert result is True
                config_path = Path(tmpdir) / ".vexor" / "config.json"
                config = json.loads(config_path.read_text())
                assert config["local_cuda"] is False
                assert config["provider"] == "openai"
                assert "api_key" not in config
                assert config["model"] == "text-embedding-3-small"


class TestGetOpenaiApiKey:
    """Test _get_openai_api_key function."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test123"})
    def test_returns_key_when_set(self):
        """_get_openai_api_key returns key when environment variable is set."""
        from installer.steps.dependencies import _get_openai_api_key

        assert _get_openai_api_key() == "sk-test123"

    @patch.dict("os.environ", {}, clear=True)
    def test_returns_none_when_not_set(self):
        """_get_openai_api_key returns None when environment variable is not set."""
        from installer.steps.dependencies import _get_openai_api_key

        assert _get_openai_api_key() is None


class TestVexorOnnxruntimeConflictFix:
    """Test onnxruntime conflict fix helpers."""

    def test_get_vexor_pip_path_returns_path_when_exists(self):
        """_get_vexor_pip_path returns Path when vexor pip exists."""
        from installer.steps.dependencies import _get_vexor_pip_path

        with tempfile.TemporaryDirectory() as tmpdir:
            vexor_dir = Path(tmpdir) / ".local" / "share" / "uv" / "tools" / "vexor" / "bin"
            vexor_dir.mkdir(parents=True)
            vexor_pip = vexor_dir / "pip"
            vexor_pip.touch()

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _get_vexor_pip_path()

                assert result is not None
                assert result.name == "pip"

    def test_get_vexor_pip_path_returns_none_when_not_exists(self):
        """_get_vexor_pip_path returns None when vexor pip doesn't exist."""
        from installer.steps.dependencies import _get_vexor_pip_path

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(Path, "home", return_value=Path(tmpdir)):
                result = _get_vexor_pip_path()

                assert result is None

    @patch("installer.steps.dependencies._get_vexor_pip_path")
    @patch("installer.steps.dependencies.subprocess.run")
    def test_fix_vexor_onnxruntime_conflict_removes_cpu_package(self, mock_run, mock_pip_path):
        """_fix_vexor_onnxruntime_conflict removes onnxruntime when both packages present."""
        from installer.steps.dependencies import _fix_vexor_onnxruntime_conflict

        mock_pip_path.return_value = Path("/fake/vexor/bin/pip")
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="onnxruntime       1.17.0\nonnxruntime-gpu   1.17.0\n",
        )

        result = _fix_vexor_onnxruntime_conflict()

        assert result is True
        # Should call pip list and pip uninstall
        assert mock_run.call_count == 2

    @patch("installer.steps.dependencies._get_vexor_pip_path")
    @patch("installer.steps.dependencies.subprocess.run")
    def test_fix_vexor_onnxruntime_conflict_skips_when_no_conflict(self, mock_run, mock_pip_path):
        """_fix_vexor_onnxruntime_conflict skips uninstall when only one package."""
        from installer.steps.dependencies import _fix_vexor_onnxruntime_conflict

        mock_pip_path.return_value = Path("/fake/vexor/bin/pip")
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="onnxruntime-gpu   1.17.0\n",  # Only GPU version
        )

        result = _fix_vexor_onnxruntime_conflict()

        assert result is True
        # Should only call pip list, no uninstall
        assert mock_run.call_count == 1

    @patch("installer.steps.dependencies._get_vexor_pip_path")
    def test_fix_vexor_onnxruntime_conflict_returns_false_when_no_pip(self, mock_pip_path):
        """_fix_vexor_onnxruntime_conflict returns False when vexor pip not found."""
        from installer.steps.dependencies import _fix_vexor_onnxruntime_conflict

        mock_pip_path.return_value = None

        result = _fix_vexor_onnxruntime_conflict()

        assert result is False
