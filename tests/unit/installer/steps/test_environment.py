"""Tests for environment step."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestRemoveEnvKey:
    """Test remove_env_key function."""

    def test_remove_env_key_removes_existing_key(self):
        """remove_env_key removes key from file and returns True."""
        from installer.steps.environment import remove_env_key

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("KEY1=value1\nKEY2=value2\nKEY3=value3\n")

            result = remove_env_key("KEY2", env_file)

            assert result is True
            content = env_file.read_text()
            assert "KEY1=value1" in content
            assert "KEY2=value2" not in content
            assert "KEY3=value3" in content

    def test_remove_env_key_returns_false_for_nonexistent_file(self):
        """remove_env_key returns False when file doesn't exist."""
        from installer.steps.environment import remove_env_key

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"

            result = remove_env_key("KEY", env_file)

            assert result is False

    def test_remove_env_key_returns_false_when_key_not_found(self):
        """remove_env_key returns False when key not in file."""
        from installer.steps.environment import remove_env_key

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("OTHER_KEY=value\n")

            result = remove_env_key("MISSING_KEY", env_file)

            assert result is False

    def test_remove_env_key_handles_empty_result(self):
        """remove_env_key handles case where file becomes empty."""
        from installer.steps.environment import remove_env_key

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("ONLY_KEY=value\n")

            result = remove_env_key("ONLY_KEY", env_file)

            assert result is True
            assert env_file.read_text() == ""


class TestSetEnvKey:
    """Test set_env_key function."""

    def test_set_env_key_creates_file_if_not_exists(self):
        """set_env_key creates new file with key."""
        from installer.steps.environment import set_env_key

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"

            set_env_key("NEW_KEY", "new_value", env_file)

            assert env_file.exists()
            assert env_file.read_text() == "NEW_KEY=new_value\n"

    def test_set_env_key_replaces_existing_key(self):
        """set_env_key replaces existing key value."""
        from installer.steps.environment import set_env_key

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("KEY=old_value\nOTHER=other\n")

            set_env_key("KEY", "new_value", env_file)

            content = env_file.read_text()
            assert "KEY=new_value" in content
            assert "KEY=old_value" not in content
            assert "OTHER=other" in content

    def test_set_env_key_appends_new_key(self):
        """set_env_key appends new key to existing file."""
        from installer.steps.environment import set_env_key

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("EXISTING=value\n")

            set_env_key("NEW_KEY", "new_value", env_file)

            content = env_file.read_text()
            assert "EXISTING=value" in content
            assert "NEW_KEY=new_value" in content


class TestCleanupObsoleteEnvKeys:
    """Test cleanup_obsolete_env_keys function."""

    def test_cleanup_obsolete_env_keys_removes_known_keys(self):
        """cleanup_obsolete_env_keys removes all obsolete keys."""
        from installer.steps.environment import OBSOLETE_ENV_KEYS, cleanup_obsolete_env_keys

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            # Add some obsolete keys and a valid one
            content = "MILVUS_TOKEN=token\nEXA_API_KEY=key\nVALID_KEY=keep\n"
            env_file.write_text(content)

            removed = cleanup_obsolete_env_keys(env_file)

            assert "MILVUS_TOKEN" in removed
            assert "EXA_API_KEY" in removed
            final_content = env_file.read_text()
            assert "VALID_KEY=keep" in final_content
            assert "MILVUS_TOKEN" not in final_content

    def test_cleanup_obsolete_env_keys_returns_empty_when_none_found(self):
        """cleanup_obsolete_env_keys returns empty list when no obsolete keys."""
        from installer.steps.environment import cleanup_obsolete_env_keys

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("VALID_KEY=value\n")

            removed = cleanup_obsolete_env_keys(env_file)

            assert removed == []


class TestKeyExistsInFile:
    """Test key_exists_in_file function."""

    def test_key_exists_in_file_returns_true_for_existing_key(self):
        """key_exists_in_file returns True for key with value."""
        from installer.steps.environment import key_exists_in_file

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("MY_KEY=my_value\n")

            result = key_exists_in_file("MY_KEY", env_file)

            assert result is True

    def test_key_exists_in_file_returns_false_for_empty_value(self):
        """key_exists_in_file returns False for key with empty value."""
        from installer.steps.environment import key_exists_in_file

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("MY_KEY=\n")

            result = key_exists_in_file("MY_KEY", env_file)

            assert result is False

    def test_key_exists_in_file_returns_false_for_missing_key(self):
        """key_exists_in_file returns False when key not in file."""
        from installer.steps.environment import key_exists_in_file

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("OTHER_KEY=value\n")

            result = key_exists_in_file("MY_KEY", env_file)

            assert result is False

    def test_key_exists_in_file_returns_false_for_missing_file(self):
        """key_exists_in_file returns False when file doesn't exist."""
        from installer.steps.environment import key_exists_in_file

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"

            result = key_exists_in_file("MY_KEY", env_file)

            assert result is False


class TestKeyIsSet:
    """Test key_is_set function."""

    def test_key_is_set_returns_true_when_env_var_set(self):
        """key_is_set returns True when key is set as environment variable."""
        from installer.steps.environment import key_is_set

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            # File doesn't have key

            with patch.dict(os.environ, {"TEST_ENV_KEY": "value"}):
                result = key_is_set("TEST_ENV_KEY", env_file)

            assert result is True

    def test_key_is_set_returns_true_when_in_file(self):
        """key_is_set returns True when key is in file."""
        from installer.steps.environment import key_is_set

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("FILE_KEY=file_value\n")

            # Ensure not in environment
            env_backup = os.environ.get("FILE_KEY")
            if "FILE_KEY" in os.environ:
                del os.environ["FILE_KEY"]

            try:
                result = key_is_set("FILE_KEY", env_file)
                assert result is True
            finally:
                if env_backup:
                    os.environ["FILE_KEY"] = env_backup

    def test_key_is_set_returns_false_when_not_found(self):
        """key_is_set returns False when key not in env or file."""
        from installer.steps.environment import key_is_set

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("OTHER=value\n")

            # Ensure not in environment
            if "MISSING_KEY_12345" in os.environ:
                del os.environ["MISSING_KEY_12345"]

            result = key_is_set("MISSING_KEY_12345", env_file)

            assert result is False


class TestAddEnvKey:
    """Test add_env_key function."""

    def test_add_env_key_appends_to_file(self):
        """add_env_key appends key to existing file."""
        from installer.steps.environment import add_env_key

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("EXISTING=value\n")

            add_env_key("NEW_KEY", "new_value", env_file)

            content = env_file.read_text()
            assert "EXISTING=value" in content
            assert "NEW_KEY=new_value" in content

    def test_add_env_key_skips_existing_key(self):
        """add_env_key does not duplicate existing key."""
        from installer.steps.environment import add_env_key

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("MY_KEY=original\n")

            add_env_key("MY_KEY", "new_value", env_file)

            content = env_file.read_text()
            assert content.count("MY_KEY") == 1
            assert "MY_KEY=original" in content

    def test_add_env_key_creates_file_if_missing(self):
        """add_env_key creates file if it doesn't exist."""
        from installer.steps.environment import add_env_key

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"

            add_env_key("NEW_KEY", "value", env_file)

            assert env_file.exists()
            assert "NEW_KEY=value" in env_file.read_text()


class TestCreateClaudeConfig:
    """Test create_claude_config function."""

    def test_create_claude_config_creates_file(self):
        """create_claude_config creates ~/.claude.json with correct content."""
        import json
        from unittest.mock import patch

        from installer.steps.environment import create_claude_config

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home = Path(tmpdir)
            with patch("installer.steps.environment.Path.home", return_value=mock_home):
                result = create_claude_config()

            config_file = mock_home / ".claude.json"
            assert result is True
            assert config_file.exists()
            content = json.loads(config_file.read_text())
            assert content["hasCompletedOnboarding"] is True

    def test_create_claude_config_merges_with_existing(self):
        """create_claude_config preserves existing config values."""
        import json
        from unittest.mock import patch

        from installer.steps.environment import create_claude_config

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home = Path(tmpdir)
            config_file = mock_home / ".claude.json"
            config_file.write_text('{"theme": "dark", "existingKey": "value"}')

            with patch("installer.steps.environment.Path.home", return_value=mock_home):
                result = create_claude_config()

            assert result is True
            content = json.loads(config_file.read_text())
            assert content["hasCompletedOnboarding"] is True
            assert content["theme"] == "dark"
            assert content["existingKey"] == "value"

    def test_create_claude_config_returns_false_on_error(self):
        """create_claude_config returns False on permission error."""
        from unittest.mock import MagicMock, patch

        from installer.steps.environment import create_claude_config

        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_path.write_text.side_effect = PermissionError("No permission")

        with patch("installer.steps.environment.Path.home", return_value=MagicMock(__truediv__=lambda s, x: mock_path)):
            result = create_claude_config()

        assert result is False


class TestEnvironmentStep:
    """Test EnvironmentStep class."""

    def test_environment_step_has_correct_name(self):
        """EnvironmentStep has name 'environment'."""
        from installer.steps.environment import EnvironmentStep

        step = EnvironmentStep()
        assert step.name == "environment"

    def test_environment_check_always_returns_false(self):
        """EnvironmentStep.check always returns False to check for missing keys."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep
        from installer.ui import Console

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("OPENAI_API_KEY=key\nFIRECRAWL_API_KEY=key\n")

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            result = step.check(ctx)
            assert result is False

    def test_environment_run_skips_in_non_interactive(self):
        """EnvironmentStep.run skips prompts in non-interactive mode."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep
        from installer.ui import Console

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=True,
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

    def test_environment_run_skips_when_skip_env_true(self):
        """EnvironmentStep.run skips when skip_env is True."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep
        from installer.ui import Console

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                skip_env=True,
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

    def test_environment_appends_to_existing_env(self):
        """EnvironmentStep appends to existing .env file."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep
        from installer.ui import Console

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("EXISTING_KEY=existing_value\n")

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=True,
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

            content = env_file.read_text()
            assert "EXISTING_KEY=existing_value" in content

    def test_environment_run_with_mocked_ui_prompts_for_keys(self):
        """EnvironmentStep.run prompts for missing keys with mocked UI."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_ui = MagicMock()
            mock_ui.input.return_value = "test_api_key"
            mock_ui.confirm.return_value = True  # Accept OAuth prompt

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=False,
                skip_env=False,
                ui=mock_ui,
            )

            mock_home = Path(tmpdir) / "home"
            mock_home.mkdir()

            # Patch environment to ensure keys are not set
            with patch.dict(os.environ, {}, clear=False):
                # Remove any existing API keys from environment for this test
                env_copy = os.environ.copy()
                for key in ["OPENAI_API_KEY", "FIRECRAWL_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"]:
                    os.environ.pop(key, None)
                try:
                    with patch("installer.steps.environment.Path.home", return_value=mock_home):
                        step.run(ctx)
                finally:
                    os.environ.update(env_copy)

            # Should have prompted for OPENAI, FIRECRAWL, and OAuth token (3 inputs)
            assert mock_ui.input.call_count == 3
            mock_ui.section.assert_called_once()

    def test_environment_run_skips_existing_keys(self):
        """EnvironmentStep.run skips prompts for keys that already exist."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            # Include all keys including OAuth token
            env_file.write_text(
                "OPENAI_API_KEY=existing\nFIRECRAWL_API_KEY=existing\nCLAUDE_CODE_OAUTH_TOKEN=existing\n"
            )

            mock_ui = MagicMock()
            mock_ui.input.return_value = "new_key"

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=False,
                skip_env=False,
                ui=mock_ui,
            )

            step.run(ctx)

            # Should not have prompted for any keys (all exist)
            mock_ui.input.assert_not_called()
            mock_ui.confirm.assert_not_called()
            # Should have called success for skipped keys (OPENAI, FIRECRAWL, OAUTH, final success)
            assert mock_ui.success.call_count >= 3

    def test_environment_run_removes_obsolete_keys(self):
        """EnvironmentStep.run removes obsolete keys from existing file."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("MILVUS_TOKEN=old\nOPENAI_API_KEY=valid\nFIRECRAWL_API_KEY=valid\n")

            mock_ui = MagicMock()

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=False,
                skip_env=False,
                ui=mock_ui,
            )

            step.run(ctx)

            content = env_file.read_text()
            assert "MILVUS_TOKEN" not in content
            assert "OPENAI_API_KEY=valid" in content

    def test_environment_rollback_does_nothing(self):
        """EnvironmentStep.rollback does nothing."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep
        from installer.ui import Console

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )

            # Should not raise
            step.rollback(ctx)

    def test_environment_run_without_ui(self):
        """EnvironmentStep.run handles case where ui is None."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=True,
                ui=None,
            )

            # Should not raise even without UI
            step.run(ctx)

    def test_environment_prompts_for_oauth_when_not_set(self):
        """EnvironmentStep prompts for OAuth token when not set."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Pre-set other keys so we skip to OAuth section
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("OPENAI_API_KEY=key\nFIRECRAWL_API_KEY=key\n")

            mock_ui = MagicMock()
            mock_ui.confirm.return_value = False  # User declines OAuth

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=False,
                skip_env=False,
                ui=mock_ui,
            )

            # Mock credentials_exist and ensure CLAUDE_CODE_OAUTH_TOKEN not in env
            mock_environ = os.environ.copy()
            mock_environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
            with (
                patch("installer.steps.environment.credentials_exist", return_value=False),
                patch.dict("os.environ", mock_environ, clear=True),
            ):
                step.run(ctx)

            # Should have called confirm for OAuth
            mock_ui.confirm.assert_called_once()
            call_args = mock_ui.confirm.call_args
            assert "Long Lasting Token" in call_args[0][0]

    def test_environment_skips_oauth_when_already_set(self):
        """EnvironmentStep skips OAuth prompt when credentials already exist."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("OPENAI_API_KEY=key\nFIRECRAWL_API_KEY=key\nCLAUDE_CODE_OAUTH_TOKEN=existing\n")

            mock_ui = MagicMock()

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=False,
                skip_env=False,
                ui=mock_ui,
            )

            # Mock credentials_exist to return True (credentials already configured)
            with patch("installer.steps.environment.credentials_exist", return_value=True):
                step.run(ctx)

            # Should NOT have called confirm for OAuth (credentials already exist)
            mock_ui.confirm.assert_not_called()
            # Should have shown success message about already configured
            success_calls = [str(c) for c in mock_ui.success.call_args_list]
            assert any("already configured" in str(c) for c in success_calls)

    def test_environment_saves_oauth_token_when_user_confirms(self):
        """EnvironmentStep saves token to .env and creates credentials file."""
        import json

        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("OPENAI_API_KEY=key\nFIRECRAWL_API_KEY=key\n")

            mock_ui = MagicMock()
            mock_ui.confirm.return_value = True  # User accepts OAuth
            mock_ui.input.return_value = "test_oauth_token_123"

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=False,
                skip_env=False,
                ui=mock_ui,
            )

            mock_home = Path(tmpdir) / "home"
            mock_home.mkdir()

            # Ensure CLAUDE_CODE_OAUTH_TOKEN not in env so prompt is shown
            mock_environ = os.environ.copy()
            mock_environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
            with (
                patch("installer.steps.environment.Path.home", return_value=mock_home),
                patch.dict("os.environ", mock_environ, clear=True),
            ):
                step.run(ctx)

            # Token should be saved to .env
            content = env_file.read_text()
            assert "CLAUDE_CODE_OAUTH_TOKEN=test_oauth_token_123" in content

            # Claude config should be created
            config_file = mock_home / ".claude.json"
            assert config_file.exists()

            # Credentials file should be created with correct structure
            creds_file = mock_home / ".claude" / ".credentials.json"
            assert creds_file.exists()
            creds_content = json.loads(creds_file.read_text())
            assert creds_content["claudeAiOauth"]["accessToken"] == "test_oauth_token_123"
            assert creds_content["claudeAiOauth"]["refreshToken"] == "test_oauth_token_123"

    def test_environment_skips_oauth_save_when_user_declines(self):
        """EnvironmentStep skips token save when user says no."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("OPENAI_API_KEY=key\nFIRECRAWL_API_KEY=key\n")

            mock_ui = MagicMock()
            mock_ui.confirm.return_value = False  # User declines OAuth

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=False,
                skip_env=False,
                ui=mock_ui,
            )

            # Ensure CLAUDE_CODE_OAUTH_TOKEN not in env so prompt is shown
            mock_environ = os.environ.copy()
            mock_environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
            with (
                patch("installer.steps.environment.credentials_exist", return_value=False),
                patch.dict("os.environ", mock_environ, clear=True),
            ):
                step.run(ctx)

            # Token should NOT be in .env
            content = env_file.read_text()
            assert "CLAUDE_CODE_OAUTH_TOKEN" not in content

            # Input should not have been called for token value
            # (confirm was called, but not input for the token)
            input_calls = [str(c) for c in mock_ui.input.call_args_list]
            assert not any("OAUTH" in str(c) for c in input_calls)

    def test_environment_warns_about_anthropic_api_key_conflict(self):
        """EnvironmentStep warns when ANTHROPIC_API_KEY may conflict with OAuth."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            # ANTHROPIC_API_KEY is set, which can conflict with OAuth
            env_file.write_text("OPENAI_API_KEY=key\nFIRECRAWL_API_KEY=key\nANTHROPIC_API_KEY=sk-ant-xxx\n")

            mock_ui = MagicMock()
            mock_ui.confirm.return_value = True  # User accepts OAuth
            mock_ui.input.return_value = "test_oauth_token"

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=False,
                skip_env=False,
                ui=mock_ui,
            )

            mock_home = Path(tmpdir) / "home"
            mock_home.mkdir()

            # Ensure CLAUDE_CODE_OAUTH_TOKEN not in env so prompt is shown
            mock_environ = os.environ.copy()
            mock_environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
            with (
                patch("installer.steps.environment.Path.home", return_value=mock_home),
                patch.dict("os.environ", mock_environ, clear=True),
            ):
                step.run(ctx)

            # Should have warned about ANTHROPIC_API_KEY conflict
            warning_calls = [str(c) for c in mock_ui.warning.call_args_list]
            assert any("ANTHROPIC_API_KEY" in str(c) for c in warning_calls)

    def test_environment_auto_restores_credentials_from_env(self):
        """EnvironmentStep auto-restores credentials when token in .env but creds file missing."""
        import json

        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            # Token exists in .env (persisted from previous install)
            env_file.write_text(
                "OPENAI_API_KEY=key\nFIRECRAWL_API_KEY=key\nCLAUDE_CODE_OAUTH_TOKEN=restored_token_123\n"
            )

            mock_ui = MagicMock()

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=False,
                skip_env=False,
                ui=mock_ui,
            )

            mock_home = Path(tmpdir) / "home"
            mock_home.mkdir()

            with patch("installer.steps.environment.Path.home", return_value=mock_home):
                step.run(ctx)

            # Should NOT have prompted for OAuth (token exists in .env)
            mock_ui.confirm.assert_not_called()

            # Credentials file should have been auto-restored
            creds_file = mock_home / ".claude" / ".credentials.json"
            assert creds_file.exists()
            creds_content = json.loads(creds_file.read_text())
            assert creds_content["claudeAiOauth"]["accessToken"] == "restored_token_123"

            # Should have shown restore success message
            success_calls = [str(c) for c in mock_ui.success.call_args_list]
            assert any("restored" in str(c).lower() for c in success_calls)


class TestCredentialsExist:
    """Test credentials_exist function."""

    def test_credentials_exist_returns_false_when_file_missing(self):
        """credentials_exist returns False when credentials file doesn't exist."""
        from installer.steps.environment import credentials_exist

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home = Path(tmpdir) / "home"
            mock_home.mkdir()

            with patch("installer.steps.environment.Path.home", return_value=mock_home):
                result = credentials_exist()

            assert result is False

    def test_credentials_exist_returns_false_for_invalid_json(self):
        """credentials_exist returns False when file contains invalid JSON."""
        from installer.steps.environment import credentials_exist

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home = Path(tmpdir) / "home"
            claude_dir = mock_home / ".claude"
            claude_dir.mkdir(parents=True)
            creds_file = claude_dir / ".credentials.json"
            creds_file.write_text("not valid json {{{")

            with patch("installer.steps.environment.Path.home", return_value=mock_home):
                result = credentials_exist()

            assert result is False

    def test_credentials_exist_returns_false_when_missing_oauth_key(self):
        """credentials_exist returns False when claudeAiOauth key is missing."""
        from installer.steps.environment import credentials_exist

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home = Path(tmpdir) / "home"
            claude_dir = mock_home / ".claude"
            claude_dir.mkdir(parents=True)
            creds_file = claude_dir / ".credentials.json"
            creds_file.write_text('{"someOtherKey": "value"}')

            with patch("installer.steps.environment.Path.home", return_value=mock_home):
                result = credentials_exist()

            assert result is False

    def test_credentials_exist_returns_false_when_access_token_empty(self):
        """credentials_exist returns False when accessToken is empty."""
        from installer.steps.environment import credentials_exist

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home = Path(tmpdir) / "home"
            claude_dir = mock_home / ".claude"
            claude_dir.mkdir(parents=True)
            creds_file = claude_dir / ".credentials.json"
            creds_file.write_text('{"claudeAiOauth": {"accessToken": ""}}')

            with patch("installer.steps.environment.Path.home", return_value=mock_home):
                result = credentials_exist()

            assert result is False

    def test_credentials_exist_returns_true_for_valid_credentials(self):
        """credentials_exist returns True when valid credentials exist."""
        from installer.steps.environment import credentials_exist

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home = Path(tmpdir) / "home"
            claude_dir = mock_home / ".claude"
            claude_dir.mkdir(parents=True)
            creds_file = claude_dir / ".credentials.json"
            creds_file.write_text('{"claudeAiOauth": {"accessToken": "sk-ant-test-token"}}')

            with patch("installer.steps.environment.Path.home", return_value=mock_home):
                result = credentials_exist()

            assert result is True


class TestCreateClaudeCredentials:
    """Test create_claude_credentials function."""

    def test_create_claude_credentials_creates_directory_and_file(self):
        """create_claude_credentials creates ~/.claude directory and credentials file."""
        from installer.steps.environment import create_claude_credentials

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home = Path(tmpdir) / "home"
            mock_home.mkdir()

            with patch("installer.steps.environment.Path.home", return_value=mock_home):
                result = create_claude_credentials("test-token-123")

            assert result is True
            creds_file = mock_home / ".claude" / ".credentials.json"
            assert creds_file.exists()

    def test_create_claude_credentials_writes_correct_structure(self):
        """create_claude_credentials writes correct JSON structure."""
        import json

        from installer.steps.environment import create_claude_credentials

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home = Path(tmpdir) / "home"
            mock_home.mkdir()

            with patch("installer.steps.environment.Path.home", return_value=mock_home):
                create_claude_credentials("my-oauth-token")

            creds_file = mock_home / ".claude" / ".credentials.json"
            content = json.loads(creds_file.read_text())

            assert "claudeAiOauth" in content
            oauth = content["claudeAiOauth"]
            assert oauth["accessToken"] == "my-oauth-token"
            assert oauth["refreshToken"] == "my-oauth-token"
            assert "expiresAt" in oauth
            assert oauth["scopes"] == ["user:inference", "user:profile", "user:sessions:claude_code"]
            assert oauth["subscriptionType"] == "max"
            assert oauth["rateLimitTier"] == "default_claude_max_20x"

    def test_create_claude_credentials_sets_expiry_365_days(self):
        """create_claude_credentials sets expiry to 365 days from now."""
        import json
        import time

        from installer.steps.environment import create_claude_credentials

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home = Path(tmpdir) / "home"
            mock_home.mkdir()

            before_time = int(time.time() * 1000)
            with patch("installer.steps.environment.Path.home", return_value=mock_home):
                create_claude_credentials("token")
            after_time = int(time.time() * 1000)

            creds_file = mock_home / ".claude" / ".credentials.json"
            content = json.loads(creds_file.read_text())
            expires_at = content["claudeAiOauth"]["expiresAt"]

            # Should be ~365 days from now (within 1 second tolerance)
            days_365_ms = 365 * 24 * 60 * 60 * 1000
            assert expires_at >= before_time + days_365_ms
            assert expires_at <= after_time + days_365_ms

    def test_create_claude_credentials_sets_file_permissions(self):
        """create_claude_credentials sets restrictive file permissions."""
        import stat

        from installer.steps.environment import create_claude_credentials

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home = Path(tmpdir) / "home"
            mock_home.mkdir()

            with patch("installer.steps.environment.Path.home", return_value=mock_home):
                create_claude_credentials("token")

            creds_file = mock_home / ".claude" / ".credentials.json"
            mode = creds_file.stat().st_mode & 0o777
            # File should be readable/writable only by owner (0o600)
            assert mode == 0o600

    def test_create_claude_credentials_returns_false_on_error(self):
        """create_claude_credentials returns False when it cannot write."""
        from installer.steps.environment import create_claude_credentials

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home = Path(tmpdir) / "home"
            mock_home.mkdir()
            # Create a file where directory should be (will cause error)
            blocking_file = mock_home / ".claude"
            blocking_file.write_text("not a directory")

            with patch("installer.steps.environment.Path.home", return_value=mock_home):
                result = create_claude_credentials("token")

            assert result is False

    def test_create_claude_credentials_overwrites_existing(self):
        """create_claude_credentials overwrites existing credentials file."""
        import json

        from installer.steps.environment import create_claude_credentials

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home = Path(tmpdir) / "home"
            claude_dir = mock_home / ".claude"
            claude_dir.mkdir(parents=True)
            creds_file = claude_dir / ".credentials.json"
            creds_file.write_text('{"claudeAiOauth": {"accessToken": "old-token"}}')

            with patch("installer.steps.environment.Path.home", return_value=mock_home):
                result = create_claude_credentials("new-token")

            assert result is True
            content = json.loads(creds_file.read_text())
            assert content["claudeAiOauth"]["accessToken"] == "new-token"
