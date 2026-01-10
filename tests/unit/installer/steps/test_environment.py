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

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=False,
                skip_env=False,
                ui=mock_ui,
            )

            # Patch environment to ensure keys are not set
            with patch.dict(os.environ, {}, clear=False):
                # Remove any existing API keys from environment for this test
                env_copy = os.environ.copy()
                for key in ["OPENAI_API_KEY", "FIRECRAWL_API_KEY"]:
                    os.environ.pop(key, None)
                try:
                    step.run(ctx)
                finally:
                    os.environ.update(env_copy)

            # Should have prompted for both API keys
            assert mock_ui.input.call_count == 2
            mock_ui.section.assert_called_once()

    def test_environment_run_skips_existing_keys(self):
        """EnvironmentStep.run skips prompts for keys that already exist."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("OPENAI_API_KEY=existing\nFIRECRAWL_API_KEY=existing\n")

            mock_ui = MagicMock()
            mock_ui.input.return_value = "new_key"

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=False,
                skip_env=False,
                ui=mock_ui,
            )

            step.run(ctx)

            # Should not have prompted for any keys
            mock_ui.input.assert_not_called()
            # Should have called success for skipped keys
            assert mock_ui.success.call_count >= 2

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
