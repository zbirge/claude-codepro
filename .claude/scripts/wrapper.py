#!/usr/bin/env python3
"""Claude Code wrapper with pipe-based control for session management.

Supervisor pattern: wrapper stays running and can restart Claude multiple times.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import FrameType


class ClaudeWrapper:
    """Wrapper that launches Claude with pipe-based control."""

    SESSION_RESTART_DELAY_SECONDS = 5.0

    GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS = 10.0

    def __init__(
        self,
        claude_args: list[str],
        pipe_dir: Path | None = None,
    ) -> None:
        """Initialize wrapper with claude arguments."""
        self.claude_args = claude_args
        self.pipe_dir = pipe_dir or self._default_pipe_dir()
        self.pipe_path: Path = self.pipe_dir / f"claude-{os.getpid()}.pipe"
        self.claude_process: subprocess.Popen[bytes] | None = None
        self._running = False
        self._shutdown_requested = False
        self._restart_pending = False
        self._restart_prompt: str | None = None
        self._reader_thread: threading.Thread | None = None
        self._lock = threading.Lock()

        self.pipe_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _default_pipe_dir() -> Path:
        """Get default pipe directory."""
        return Path.cwd() / ".claude" / "tmp" / "pipes"

    def _create_pipe(self) -> None:
        """Create named pipe for receiving commands."""
        if self.pipe_path.exists():
            self.pipe_path.unlink()
        os.mkfifo(self.pipe_path)

    def _cleanup(self) -> None:
        """Clean up pipe and resources."""
        if self.pipe_path.exists():
            try:
                self.pipe_path.unlink()
            except OSError:
                pass

        try:
            if self.pipe_dir.exists() and not any(self.pipe_dir.iterdir()):
                self.pipe_dir.rmdir()
        except OSError:
            pass

    def _get_claude_env(self) -> dict[str, str]:
        """Get environment variables for Claude process."""
        env = os.environ.copy()
        env["WRAPPER_PIPE"] = str(self.pipe_path)
        return env

    def _handle_command(self, command: str) -> None:
        """Handle command received via pipe."""
        parts = command.strip().split(maxsplit=1)
        if not parts:
            return

        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else None

        if cmd == "exit":
            print("\n[Wrapper] Exit command received")
            with self._lock:
                self._shutdown_requested = True
            self._kill_claude()

        elif cmd == "clear":
            print("\n[Wrapper] Clear command received - restarting with fresh session")
            with self._lock:
                self._restart_pending = True
                self._restart_prompt = None
            self._kill_claude()

        elif cmd == "clear-continue":
            if arg:
                print(f"\n[Wrapper] Clear-continue command received for: {arg}")
                with self._lock:
                    self._restart_pending = True
                    self._restart_prompt = f"/ccp --continue {arg}"
            else:
                print("\n[Wrapper] Clear-continue missing plan path, doing plain clear")
                with self._lock:
                    self._restart_pending = True
                    self._restart_prompt = None
            self._kill_claude()

        else:
            print(f"\n[Wrapper] Unknown command: {cmd}", file=sys.stderr)

    def _kill_claude(self) -> None:
        """Kill the Claude process gracefully, allowing SessionEnd hooks to complete."""
        if self.claude_process and self.claude_process.poll() is None:
            print("[Wrapper] Sending SIGTERM, waiting for graceful shutdown...")
            self.claude_process.terminate()
            try:
                self.claude_process.wait(timeout=self.GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS)
                print("[Wrapper] Claude exited gracefully")
            except subprocess.TimeoutExpired:
                print("[Wrapper] Timeout, force killing...")
                self.claude_process.kill()
                self.claude_process.wait()

    def _start_claude(self, prompt: str | None = None) -> None:
        """Start a new Claude process."""
        cmd = ["claude"] + self.claude_args
        if prompt:
            cmd.append(prompt)

        print(f"\n[Wrapper] Starting Claude...")
        print(f"[Wrapper] Command: {' '.join(cmd)}")
        print("-" * 60)

        self.claude_process = subprocess.Popen(
            cmd,
            env=self._get_claude_env(),
        )

        print(f"[Wrapper] Claude PID: {self.claude_process.pid}")
        print("-" * 60)

    def _read_pipe_command(self) -> None:
        """Read a single command from the pipe."""
        try:
            with open(self.pipe_path) as f:
                line = f.readline()
                if line:
                    self._handle_command(line)
        except OSError:
            pass

    def _pipe_reader_loop(self) -> None:
        """Background thread that reads commands from pipe."""
        while self._running:
            try:
                self._read_pipe_command()
            except Exception as e:
                if self._running:
                    print(f"[Wrapper] Pipe read error: {e}", file=sys.stderr)

    def _signal_handler(self, signum: int, frame: FrameType | None) -> None:
        """Handle termination signals."""
        _ = frame
        print(f"\n[Wrapper] Received signal {signum}, shutting down...")
        with self._lock:
            self._shutdown_requested = True
            self._running = False
        self._kill_claude()

    def start(self) -> int:
        """Start the wrapper and Claude process with supervisor loop."""
        self._create_pipe()

        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        print("=" * 60)
        print("Claude Code Wrapper (Supervisor Mode)")
        print("=" * 60)
        print(f"Wrapper PID: {os.getpid()}")
        print(f"Control pipe: {self.pipe_path}")
        print("Commands: clear, clear-continue <plan>, exit")
        print("-" * 60)

        self._running = True
        self._reader_thread = threading.Thread(target=self._pipe_reader_loop, daemon=True)
        self._reader_thread.start()

        exit_code = 0
        first_run = True

        while True:
            with self._lock:
                if self._shutdown_requested:
                    break

            with self._lock:
                prompt = self._restart_prompt
                self._restart_prompt = None
                self._restart_pending = False

            if first_run:
                self._start_claude(prompt=None)
                first_run = False
            else:
                self._start_claude(prompt=prompt)

            try:
                exit_code = self.claude_process.wait() if self.claude_process else 0
            except KeyboardInterrupt:
                with self._lock:
                    self._shutdown_requested = True
                self._kill_claude()
                exit_code = 130
                break

            with self._lock:
                if self._shutdown_requested:
                    break
                if self._restart_pending:
                    print("\n[Wrapper] Restart pending, waiting for Claude MEM to process...")
                    print(f"[Wrapper] Sleeping {self.SESSION_RESTART_DELAY_SECONDS}s for session hooks...")
                    time.sleep(self.SESSION_RESTART_DELAY_SECONDS)
                    print("[Wrapper] Starting new Claude session...")
                    continue
                break

        self._running = False
        self._cleanup()

        return exit_code

    def run(self) -> int:
        """Run the wrapper (alias for start)."""
        return self.start()


def main() -> int:
    """Main entry point for wrapper script."""
    claude_args = sys.argv[1:]

    wrapper = ClaudeWrapper(claude_args=claude_args)
    return wrapper.start()


if __name__ == "__main__":
    sys.exit(main())
