"""Finalize step - runs final cleanup tasks and displays success."""

from __future__ import annotations

from typing import TYPE_CHECKING

from installer import __version__
from installer.steps.base import BaseStep

if TYPE_CHECKING:
    from installer.context import InstallContext


class FinalizeStep(BaseStep):
    """Step that runs final cleanup tasks and displays success panel."""

    name = "finalize"

    def check(self, ctx: InstallContext) -> bool:
        """Always returns False - finalize always runs."""
        return False

    def run(self, ctx: InstallContext) -> None:
        """Run final cleanup tasks and display success."""
        self._display_success(ctx)

    def _display_success(self, ctx: InstallContext) -> None:
        """Display success panel with next steps."""
        ui = ctx.ui

        if not ui:
            return

        installed_items = []
        if ctx.config.get("installed_dependencies"):
            for dep in ctx.config["installed_dependencies"]:
                installed_items.append(dep.replace("_", " ").title())

        installed_items.extend(
            [
                "Claude CodePro rules",
                "Shell alias (ccp)",
                "Endless Mode (session continuity)",
                "Auditor Agent (background rule monitoring)",
            ]
        )

        if ctx.config.get("installed_extensions"):
            installed_items.append(f"VS Code Extensions ({ctx.config['installed_extensions']})")

        if ctx.enable_python:
            installed_items.append("Python development tools")

        if ctx.enable_typescript:
            installed_items.append("TypeScript quality hooks")

        ui.success_box("Installation Complete!", installed_items)

        steps: list[tuple[str, str]] = []

        if ctx.is_local_install:
            steps.append(
                (
                    "Reload your shell",
                    "Run: source ~/.zshrc (or ~/.bashrc, or restart terminal)",
                )
            )
        else:
            project_slug = ctx.project_dir.name.lower().replace(" ", "-").replace("_", "-")
            steps.append(
                (
                    "Connect to dev container",
                    f"Option A: Use VS Code's integrated terminal (required for image pasting)\n"
                    f"     Option B: Use your favorite terminal (iTerm, Warp, etc.) and run:\n"
                    f'     docker exec -it $(docker ps --filter "name={project_slug}" -q) zsh',
                )
            )

        steps.extend(
            [
                ("Start Claude CodePro", "Run: ccp"),
                ("Connect IDE", "Run: /ide → Enables real-time diagnostics"),
            ]
        )

        steps.append(
            (
                "Custom MCP Servers (Optional)",
                "Add your MCP servers to mcp_servers.json, then run /setup\n"
                "     to generate documentation. Use mcp-cli to interact with them.",
            )
        )

        steps.extend(
            [
                (
                    "Spec-Driven Mode",
                    '/spec "your task" → For new features with planning and verification',
                ),
                (
                    "Quick Mode",
                    "Just chat → For bug fixes and small changes without a spec",
                ),
            ]
        )

        ui.next_steps(steps)

        ui.rule()
        ui.print()
        ui.print("  [bold yellow]⭐ Star this repo:[/bold yellow] https://github.com/maxritter/claude-codepro")
        ui.print()
        ui.print(f"  [dim]Installed version: {__version__}[/dim]")
        ui.print()

    def rollback(self, ctx: InstallContext) -> None:
        """Finalize has no rollback (informational only)."""
        pass
