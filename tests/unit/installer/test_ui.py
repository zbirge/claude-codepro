"""Tests for installer UI abstraction layer."""

from __future__ import annotations

import io
import sys
from unittest.mock import MagicMock, mock_open, patch

import pytest


class TestGetTtyInput:
    """Test _get_tty_input function."""

    def test_get_tty_input_returns_stdin_when_tty(self):
        """_get_tty_input returns stdin when stdin is a tty."""
        from installer.ui import _get_tty_input

        with patch.object(sys.stdin, "isatty", return_value=True):
            result = _get_tty_input()
            assert result is sys.stdin

    def test_get_tty_input_opens_dev_tty_when_piped(self):
        """_get_tty_input opens /dev/tty when stdin is piped."""
        from installer.ui import _get_tty_input

        mock_file = MagicMock()
        with patch.object(sys.stdin, "isatty", return_value=False):
            with patch("builtins.open", return_value=mock_file) as mock_open_fn:
                result = _get_tty_input()
                mock_open_fn.assert_called_once_with("/dev/tty", "r")
                assert result is mock_file

    def test_get_tty_input_falls_back_to_stdin_on_error(self):
        """_get_tty_input falls back to stdin if /dev/tty fails."""
        from installer.ui import _get_tty_input

        with patch.object(sys.stdin, "isatty", return_value=False):
            with patch("builtins.open", side_effect=OSError("No such device")):
                result = _get_tty_input()
                assert result is sys.stdin


class TestProgressTask:
    """Test ProgressTask wrapper class."""

    def test_progress_task_advance_calls_progress(self):
        """ProgressTask.advance calls underlying progress.advance."""
        from installer.ui import ProgressTask

        mock_progress = MagicMock()
        task_id = 1
        task = ProgressTask(mock_progress, task_id)

        task.advance(5)

        mock_progress.advance.assert_called_once_with(task_id, advance=5)

    def test_progress_task_update_sets_completed(self):
        """ProgressTask.update calls underlying progress.update."""
        from installer.ui import ProgressTask

        mock_progress = MagicMock()
        task_id = 1
        task = ProgressTask(mock_progress, task_id)

        task.update(50)

        mock_progress.update.assert_called_once_with(task_id, completed=50)


class TestConsole:
    """Test Console wrapper class."""

    def test_console_non_interactive_property(self):
        """Console.non_interactive returns correct value."""
        from installer.ui import Console

        console = Console(non_interactive=False)
        assert console.non_interactive is False

        console2 = Console(non_interactive=True)
        assert console2.non_interactive is True

    def test_console_status_outputs_blue_text(self):
        """Console.status should output styled message."""
        from installer.ui import Console

        console = Console()
        console.status("Installing...")

    def test_console_success_outputs_green_checkmark(self):
        """Console.success should output green checkmark message."""
        from installer.ui import Console

        console = Console()
        console.success("Installed successfully")

    def test_console_warning_outputs_yellow_warning(self):
        """Console.warning should output yellow warning message."""
        from installer.ui import Console

        console = Console()
        console.warning("This might cause issues")

    def test_console_error_outputs_red_error(self):
        """Console.error should output red error message."""
        from installer.ui import Console

        console = Console()
        console.error("Installation failed")

    def test_console_info_outputs_dim_text(self):
        """Console.info should output dim info message."""
        from installer.ui import Console

        console = Console()
        console.info("Information message")

    def test_console_section_creates_panel(self):
        """Console.section should create a bordered panel."""
        from installer.ui import Console

        console = Console()
        console.section("Installing Dependencies")

    def test_console_progress_context_manager(self):
        """Console.progress should return a context manager."""
        from installer.ui import Console

        console = Console()
        with console.progress(total=10, description="Downloading") as progress:
            progress.advance(5)
            progress.advance(5)

    def test_console_banner_prints_logo(self):
        """Console.banner prints logo and features."""
        from installer.ui import Console

        console = Console()
        console.banner()

    def test_console_set_total_steps_and_step(self):
        """Console.set_total_steps and step work together."""
        from installer.ui import Console

        console = Console()
        console.set_total_steps(5)
        console.step("Step One")
        console.step("Step Two")
        # Verify internal state
        assert console._current_step == 2

    def test_console_box_creates_panel(self):
        """Console.box creates a styled panel."""
        from installer.ui import Console

        console = Console()
        console.box("Content here", title="Title", style="green")

    def test_console_success_box_with_items(self):
        """Console.success_box creates success panel with items."""
        from installer.ui import Console

        console = Console()
        console.success_box("Success!", ["Item 1", "Item 2"])

    def test_console_error_box_with_items(self):
        """Console.error_box creates error panel with items."""
        from installer.ui import Console

        console = Console()
        console.error_box("Error!", ["Error 1", "Error 2"])

    def test_console_next_steps(self):
        """Console.next_steps prints formatted steps."""
        from installer.ui import Console

        console = Console()
        console.next_steps([
            ("Step 1", "Description 1"),
            ("Step 2", "Description 2"),
        ])

    def test_console_spinner_context_manager(self):
        """Console.spinner provides a spinner context manager."""
        from installer.ui import Console

        console = Console()
        with console.spinner("Loading..."):
            pass

    def test_console_checklist_with_items(self):
        """Console.checklist prints pass/fail items."""
        from installer.ui import Console

        console = Console()
        console.checklist("Checks", [
            ("Check 1", True),
            ("Check 2", False),
        ])

    def test_console_print_plain_message(self):
        """Console.print outputs plain message."""
        from installer.ui import Console

        console = Console()
        console.print("Plain message")
        console.print()  # Empty message

    def test_console_rule_prints_divider(self):
        """Console.rule prints horizontal divider."""
        from installer.ui import Console

        console = Console()
        console.rule("Section")
        console.rule()  # Without title

    def test_console_newline_prints_empty_lines(self):
        """Console.newline prints specified number of empty lines."""
        from installer.ui import Console

        console = Console()
        console.newline()
        console.newline(3)

    def test_console_close_closes_tty_handle(self):
        """Console.close closes TTY handle if opened."""
        from installer.ui import Console

        console = Console()
        mock_tty = MagicMock()
        console._tty = mock_tty

        console.close()

        mock_tty.close.assert_called_once()
        assert console._tty is None

    def test_console_close_does_not_close_stdin(self):
        """Console.close does not close sys.stdin - it leaves _tty unchanged."""
        from installer.ui import Console

        mock_stdin = MagicMock()

        console = Console()
        with patch.object(sys, "stdin", mock_stdin):
            console._tty = sys.stdin  # Now sys.stdin is mock_stdin
            console.close()
            # Should not have called close on stdin
            mock_stdin.close.assert_not_called()
            # _tty stays as-is when it's stdin (not set to None)
            assert console._tty is mock_stdin

    def test_console_close_does_nothing_if_no_tty(self):
        """Console.close does nothing if no TTY opened."""
        from installer.ui import Console

        console = Console()
        console._tty = None

        console.close()

        assert console._tty is None


class TestConsoleNonInteractive:
    """Test Console in non-interactive mode."""

    def test_confirm_returns_default_in_non_interactive(self):
        """In non-interactive mode, confirm returns default."""
        from installer.ui import Console

        console = Console(non_interactive=True)
        assert console.confirm("Continue?", default=True) is True
        assert console.confirm("Continue?", default=False) is False

    def test_select_returns_first_in_non_interactive(self):
        """In non-interactive mode, select returns first choice."""
        from installer.ui import Console

        console = Console(non_interactive=True)
        result = console.select("Choose:", choices=["A", "B", "C"])
        assert result == "A"

    def test_select_returns_empty_for_empty_choices(self):
        """In non-interactive mode, select returns empty string for empty choices."""
        from installer.ui import Console

        console = Console(non_interactive=True)
        result = console.select("Choose:", choices=[])
        assert result == ""

    def test_input_returns_default_in_non_interactive(self):
        """In non-interactive mode, input returns default."""
        from installer.ui import Console

        console = Console(non_interactive=True)
        result = console.input("Enter value:", default="default_value")
        assert result == "default_value"

    def test_password_returns_empty_in_non_interactive(self):
        """In non-interactive mode, password returns empty string."""
        from installer.ui import Console

        console = Console(non_interactive=True)
        result = console.password("Enter password:")
        assert result == ""


class TestConsoleInteractive:
    """Test Console interactive methods with mocked input."""

    def test_confirm_interactive_returns_true_for_yes(self):
        """confirm returns True when user inputs 'y'."""
        from installer.ui import Console

        console = Console(non_interactive=False)
        mock_tty = MagicMock()
        mock_tty.readline.return_value = "y\n"
        console._tty = mock_tty

        result = console.confirm("Continue?")

        assert result is True

    def test_confirm_interactive_returns_false_for_no(self):
        """confirm returns False when user inputs 'n'."""
        from installer.ui import Console

        console = Console(non_interactive=False)
        mock_tty = MagicMock()
        mock_tty.readline.return_value = "n\n"
        console._tty = mock_tty

        result = console.confirm("Continue?", default=True)

        assert result is False

    def test_confirm_interactive_returns_default_for_empty(self):
        """confirm returns default when user inputs empty."""
        from installer.ui import Console

        console = Console(non_interactive=False)
        mock_tty = MagicMock()
        mock_tty.readline.return_value = "\n"
        console._tty = mock_tty

        result = console.confirm("Continue?", default=True)
        assert result is True

        mock_tty.readline.return_value = "\n"
        result = console.confirm("Continue?", default=False)
        assert result is False

    def test_confirm_handles_eof_error(self):
        """confirm returns default on EOF."""
        from installer.ui import Console

        console = Console(non_interactive=False)
        mock_tty = MagicMock()
        mock_tty.readline.side_effect = EOFError()
        console._tty = mock_tty

        result = console.confirm("Continue?", default=True)
        assert result is True

    def test_select_interactive_returns_selected_choice(self):
        """select returns selected choice based on user input."""
        from installer.ui import Console

        console = Console(non_interactive=False)
        mock_tty = MagicMock()
        mock_tty.readline.return_value = "2\n"
        console._tty = mock_tty

        result = console.select("Choose:", choices=["A", "B", "C"])

        assert result == "B"

    def test_select_interactive_returns_first_for_invalid_input(self):
        """select returns first choice for invalid input."""
        from installer.ui import Console

        console = Console(non_interactive=False)
        mock_tty = MagicMock()
        mock_tty.readline.return_value = "invalid\n"
        console._tty = mock_tty

        result = console.select("Choose:", choices=["A", "B", "C"])

        assert result == "A"

    def test_select_interactive_returns_first_for_out_of_range(self):
        """select returns first choice for out of range input."""
        from installer.ui import Console

        console = Console(non_interactive=False)
        mock_tty = MagicMock()
        mock_tty.readline.return_value = "99\n"
        console._tty = mock_tty

        result = console.select("Choose:", choices=["A", "B", "C"])

        assert result == "A"

    def test_select_handles_eof_error(self):
        """select returns first choice on EOF."""
        from installer.ui import Console

        console = Console(non_interactive=False)
        mock_tty = MagicMock()
        mock_tty.readline.side_effect = EOFError()
        console._tty = mock_tty

        result = console.select("Choose:", choices=["A", "B"])
        assert result == "A"

    def test_input_interactive_returns_user_input(self):
        """input returns user input."""
        from installer.ui import Console

        console = Console(non_interactive=False)
        mock_tty = MagicMock()
        mock_tty.readline.return_value = "user value\n"
        console._tty = mock_tty

        result = console.input("Enter value:")

        assert result == "user value"

    def test_input_interactive_returns_default_for_empty(self):
        """input returns default for empty input."""
        from installer.ui import Console

        console = Console(non_interactive=False)
        mock_tty = MagicMock()
        mock_tty.readline.return_value = "\n"
        console._tty = mock_tty

        result = console.input("Enter value:", default="default")

        assert result == "default"

    def test_input_handles_eof_error(self):
        """input returns default on EOF."""
        from installer.ui import Console

        console = Console(non_interactive=False)
        mock_tty = MagicMock()
        mock_tty.readline.side_effect = EOFError()
        console._tty = mock_tty

        result = console.input("Enter value:", default="fallback")
        assert result == "fallback"

    def test_password_interactive_calls_getpass(self):
        """password calls getpass for hidden input."""
        from installer.ui import Console

        console = Console(non_interactive=False)
        mock_tty = MagicMock()
        console._tty = mock_tty

        with patch("installer.ui.getpass.getpass", return_value="secret") as mock_getpass:
            result = console.password("Enter password:")

            mock_getpass.assert_called_once_with(prompt="", stream=mock_tty)
            assert result == "secret"

    def test_password_handles_eof_error(self):
        """password returns empty string on EOF."""
        from installer.ui import Console

        console = Console(non_interactive=False)
        mock_tty = MagicMock()
        console._tty = mock_tty

        with patch("installer.ui.getpass.getpass", side_effect=EOFError()):
            result = console.password("Enter password:")
            assert result == ""


class TestConsoleTable:
    """Test Console table functionality."""

    def test_console_table_renders_data(self):
        """Console.table should render tabular data."""
        from installer.ui import Console

        console = Console()
        data = [
            {"Step": "Bootstrap", "Status": "Complete"},
            {"Step": "GitSetup", "Status": "Pending"},
        ]
        console.table(data, title="Installation Status")

    def test_console_table_handles_empty_data(self):
        """Console.table handles empty data list."""
        from installer.ui import Console

        console = Console()
        console.table([])

    def test_console_table_without_title(self):
        """Console.table works without title."""
        from installer.ui import Console

        console = Console()
        data = [{"Key": "Value"}]
        console.table(data)
