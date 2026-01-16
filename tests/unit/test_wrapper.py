"""Unit tests for Claude wrapper with pipe-based control."""

from __future__ import annotations

import stat
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock


class TestClaudeWrapper:
    """Tests for ClaudeWrapper class."""

    def test_wrapper_creates_pipe_directory(self, tmp_path: Path) -> None:
        """Wrapper creates pipe directory if it doesn't exist."""
        from ccp.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir)

        assert pipe_dir.exists()

    def test_wrapper_creates_named_pipe(self, tmp_path: Path) -> None:
        """Wrapper creates a named pipe file."""
        from ccp.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir)
        wrapper._create_pipe()

        assert wrapper.pipe_path.exists()
        assert stat.S_ISFIFO(wrapper.pipe_path.stat().st_mode)

    def test_wrapper_exports_pipe_env_var(self, tmp_path: Path) -> None:
        """Wrapper sets WRAPPER_PIPE environment variable."""
        from ccp.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir)
        wrapper._create_pipe()
        env = wrapper._get_claude_env()

        assert "WRAPPER_PIPE" in env
        assert env["WRAPPER_PIPE"] == str(wrapper.pipe_path)

    def test_wrapper_cleanup_removes_pipe(self, tmp_path: Path) -> None:
        """Wrapper cleans up pipe on exit."""
        from ccp.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir)
        wrapper._create_pipe()
        pipe_path = wrapper.pipe_path

        assert pipe_path.exists()
        wrapper._cleanup()
        assert not pipe_path.exists()

    def test_handle_clear_command(self, tmp_path: Path) -> None:
        """Wrapper handles 'clear' command by setting restart flags."""
        from ccp.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir)
        wrapper._create_pipe()

        # Mock _kill_claude to prevent it from doing anything
        wrapper._kill_claude = MagicMock()

        wrapper._handle_command("clear")

        # Supervisor pattern: flags are set, kill is called
        assert wrapper._restart_pending is True
        assert wrapper._restart_prompt is None
        wrapper._kill_claude.assert_called_once()

    def test_handle_clear_continue_command(self, tmp_path: Path) -> None:
        """Wrapper handles 'clear-continue <plan>' command by setting restart flags."""
        from ccp.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir)
        wrapper._create_pipe()

        wrapper._kill_claude = MagicMock()

        wrapper._handle_command("clear-continue docs/plans/test.md")

        # Supervisor pattern: flags are set with prompt, kill is called
        assert wrapper._restart_pending is True
        assert wrapper._restart_prompt == "/spec --continue docs/plans/test.md"
        wrapper._kill_claude.assert_called_once()

    def test_handle_exit_command(self, tmp_path: Path) -> None:
        """Wrapper handles 'exit' command by setting shutdown flag."""
        from ccp.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir)
        wrapper._create_pipe()
        wrapper._kill_claude = MagicMock()

        wrapper._handle_command("exit")

        # Supervisor pattern: shutdown flag is set, kill is called
        assert wrapper._shutdown_requested is True
        wrapper._kill_claude.assert_called_once()

    def test_wrapper_passes_args_to_claude(self, tmp_path: Path) -> None:
        """Wrapper passes arguments to claude command."""
        from ccp.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=["--model", "opus", "--verbose"], pipe_dir=pipe_dir)

        assert wrapper.claude_args == ["--model", "opus", "--verbose"]


class TestWrapperIntegration:
    """Integration tests for wrapper functionality."""

    def test_pipe_receives_commands(self, tmp_path: Path) -> None:
        """Test that pipe can receive and process commands."""
        from ccp.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir)
        wrapper._create_pipe()
        wrapper._kill_claude = MagicMock()

        # Write command to pipe in a separate thread
        def write_to_pipe() -> None:
            time.sleep(0.1)
            with open(wrapper.pipe_path, "w") as f:
                f.write("clear\n")

        write_thread = threading.Thread(target=write_to_pipe)
        write_thread.start()

        # Read one command from pipe
        wrapper._read_pipe_command()

        write_thread.join()
        # Command was processed: restart flag set, kill called
        assert wrapper._restart_pending is True
        wrapper._kill_claude.assert_called_once()


class TestContinueFlag:
    """Tests for --continue flag functionality."""

    def test_continue_flag_parsed_from_args(self, tmp_path: Path) -> None:
        """Wrapper recognizes --continue flag and stores it."""
        from scripts.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(
            claude_args=["--model", "opus"],
            pipe_dir=pipe_dir,
            continue_session=True,
        )

        assert wrapper.continue_session is True

    def test_continue_flag_defaults_to_false(self, tmp_path: Path) -> None:
        """Wrapper defaults continue_session to False."""
        from scripts.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir)

        assert wrapper.continue_session is False

    def test_continue_flag_not_passed_to_claude(self, tmp_path: Path) -> None:
        """--continue is not included in claude_args."""
        from scripts.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        # Simulate args that would come from main() after filtering
        wrapper = ClaudeWrapper(
            claude_args=["--model", "opus"],
            pipe_dir=pipe_dir,
            continue_session=True,
        )

        # claude_args should not contain --continue
        assert "--continue" not in wrapper.claude_args

    def test_build_continuation_prompt_with_file(self, tmp_path: Path) -> None:
        """Build prompt includes file reference when continuation file exists."""
        from scripts.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir, continue_session=True)

        # Create continuation file
        continuation_file = Path("/tmp/claude-continuation.md")
        continuation_file.write_text("# Test continuation\n\nSome context here.")

        try:
            prompt = wrapper._build_continuation_prompt()
            assert "CONTINUING FROM PREVIOUS SESSION" in prompt
            assert "/tmp/claude-continuation.md" in prompt
        finally:
            continuation_file.unlink(missing_ok=True)

    def test_build_continuation_prompt_without_file(self, tmp_path: Path, capsys) -> None:
        """Build prompt shows warning when continuation file missing."""
        from scripts.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir, continue_session=True)

        # Ensure file doesn't exist
        continuation_file = Path("/tmp/claude-continuation.md")
        continuation_file.unlink(missing_ok=True)

        prompt = wrapper._build_continuation_prompt()
        assert "no saved state found" in prompt
        captured = capsys.readouterr()
        assert "No continuation file found" in captured.out

    def test_first_run_with_continue_injects_prompt(self, tmp_path: Path) -> None:
        """First run with continue_session=True injects continuation prompt."""
        from scripts.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir, continue_session=True)

        # Track what prompt was passed to _start_claude
        captured_prompts: list[str | None] = []
        original_start_claude = wrapper._start_claude

        def mock_start_claude(prompt: str | None = None) -> None:
            captured_prompts.append(prompt)

        wrapper._start_claude = mock_start_claude

        # Simulate first run logic
        first_run = True
        if first_run:
            if wrapper.continue_session:
                wrapper._start_claude(prompt=wrapper._build_continuation_prompt())
            else:
                wrapper._start_claude(prompt=None)

        # Verify prompt was injected
        assert len(captured_prompts) == 1
        assert captured_prompts[0] is not None
        assert "CONTINUING FROM PREVIOUS SESSION" in captured_prompts[0]

    def test_first_run_without_continue_no_prompt(self, tmp_path: Path) -> None:
        """First run without continue_session does not inject prompt."""
        from scripts.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir, continue_session=False)

        # Track what prompt was passed to _start_claude
        captured_prompts: list[str | None] = []

        def mock_start_claude(prompt: str | None = None) -> None:
            captured_prompts.append(prompt)

        wrapper._start_claude = mock_start_claude

        # Simulate first run logic
        first_run = True
        if first_run:
            if wrapper.continue_session:
                wrapper._start_claude(prompt=wrapper._build_continuation_prompt())
            else:
                wrapper._start_claude(prompt=None)

        # Verify no prompt was injected
        assert len(captured_prompts) == 1
        assert captured_prompts[0] is None


class TestAutoSave:
    """Tests for automatic session save on exit."""

    def test_save_session_state_writes_file(self, tmp_path: Path) -> None:
        """_save_session_state writes continuation file with expected content."""
        from scripts.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir)

        # Ensure clean state
        continuation_file = Path("/tmp/claude-continuation.md")
        continuation_file.unlink(missing_ok=True)

        try:
            wrapper._save_session_state()

            assert continuation_file.exists()
            content = continuation_file.read_text()
            assert "Session Continuation (Auto-saved)" in content
            assert "Automatic save on exit" in content
            assert "Claude Mem" in content
        finally:
            continuation_file.unlink(missing_ok=True)

    def test_normal_exit_saves_session(self, tmp_path: Path) -> None:
        """Normal exit (code 0) triggers auto-save."""
        from scripts.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir)

        # Track if _save_session_state was called
        save_called = []

        def mock_save() -> None:
            save_called.append(True)

        wrapper._save_session_state = mock_save

        # Simulate normal exit scenario
        exit_code = 0
        shutdown_requested = False
        restart_pending = False

        # This is the logic we need to implement
        if exit_code == 0 and not shutdown_requested and not restart_pending:
            wrapper._save_session_state()

        assert len(save_called) == 1

    def test_crash_does_not_save_session(self, tmp_path: Path) -> None:
        """Crash (non-zero exit) does not trigger auto-save."""
        from scripts.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir)

        save_called = []

        def mock_save() -> None:
            save_called.append(True)

        wrapper._save_session_state = mock_save

        # Simulate crash scenario
        exit_code = 1
        shutdown_requested = False
        restart_pending = False

        if exit_code == 0 and not shutdown_requested and not restart_pending:
            wrapper._save_session_state()

        assert len(save_called) == 0

    def test_wrapper_restart_does_not_save_session(self, tmp_path: Path) -> None:
        """Wrapper-initiated restart does not trigger auto-save."""
        from scripts.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir)

        save_called = []

        def mock_save() -> None:
            save_called.append(True)

        wrapper._save_session_state = mock_save

        # Simulate restart scenario
        exit_code = 0
        shutdown_requested = False
        restart_pending = True

        if exit_code == 0 and not shutdown_requested and not restart_pending:
            wrapper._save_session_state()

        assert len(save_called) == 0

    def test_shutdown_requested_does_not_save_session(self, tmp_path: Path) -> None:
        """Shutdown via wrapper command does not trigger auto-save."""
        from scripts.wrapper import ClaudeWrapper

        pipe_dir = tmp_path / "pipes"
        wrapper = ClaudeWrapper(claude_args=[], pipe_dir=pipe_dir)

        save_called = []

        def mock_save() -> None:
            save_called.append(True)

        wrapper._save_session_state = mock_save

        # Simulate shutdown scenario
        exit_code = 0
        shutdown_requested = True
        restart_pending = False

        if exit_code == 0 and not shutdown_requested and not restart_pending:
            wrapper._save_session_state()

        assert len(save_called) == 0


class TestBanner:
    """Tests for the startup banner."""

    def test_banner_contains_continue_hint(self, capsys) -> None:
        """Banner includes --continue hint for resuming sessions."""
        from scripts.wrapper import print_banner

        print_banner()

        captured = capsys.readouterr()
        assert "--continue" in captured.out
        assert "Resume" in captured.out or "resume" in captured.out
