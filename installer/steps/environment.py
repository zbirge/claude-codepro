"""Environment step - sets up .env file with API keys."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from installer.steps.base import BaseStep

if TYPE_CHECKING:
    from installer.context import InstallContext


OBSOLETE_ENV_KEYS = [
    "MILVUS_TOKEN",
    "MILVUS_ADDRESS",
    "VECTOR_STORE_USERNAME",
    "VECTOR_STORE_PASSWORD",
    "EXA_API_KEY",
    "GEMINI_API_KEY",
]

GITHUB_TOKEN_KEY = "GITHUB_PERSONAL_ACCESS_TOKEN"
GITLAB_TOKEN_KEY = "GITLAB_PERSONAL_ACCESS_TOKEN"


def detect_git_hosting(project_dir: Path) -> tuple[bool, bool]:
    """Detect if project uses GitHub or GitLab based on git remotes.

    Returns:
        Tuple of (is_github, is_gitlab) based on remote URLs.
    """
    import subprocess

    is_github = False
    is_gitlab = False

    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            remotes = result.stdout.lower()
            is_github = "github.com" in remotes
            is_gitlab = "gitlab.com" in remotes or "gitlab." in remotes
    except (subprocess.SubprocessError, OSError):
        pass

    return is_github, is_gitlab


def remove_env_key(key: str, env_file: Path) -> bool:
    """Remove an environment key from .env file. Returns True if key was removed."""
    if not env_file.exists():
        return False

    lines = env_file.read_text().splitlines()
    new_lines = [line for line in lines if not line.strip().startswith(f"{key}=")]

    if len(new_lines) != len(lines):
        env_file.write_text("\n".join(new_lines) + "\n" if new_lines else "")
        return True
    return False


def set_env_key(key: str, value: str, env_file: Path) -> None:
    """Set an environment key in .env file, replacing if it exists."""
    if not env_file.exists():
        env_file.write_text(f"{key}={value}\n")
        return

    lines = env_file.read_text().splitlines()
    new_lines = [line for line in lines if not line.strip().startswith(f"{key}=")]
    new_lines.append(f"{key}={value}")
    env_file.write_text("\n".join(new_lines) + "\n")


def cleanup_obsolete_env_keys(env_file: Path) -> list[str]:
    """Remove obsolete environment keys from .env file. Returns list of removed keys."""
    removed = []
    for key in OBSOLETE_ENV_KEYS:
        if remove_env_key(key, env_file):
            removed.append(key)
    return removed


def key_exists_in_file(key: str, env_file: Path) -> bool:
    """Check if key exists in .env file with a non-empty value."""
    if not env_file.exists():
        return False

    content = env_file.read_text()
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith(f"{key}="):
            value = line[len(key) + 1 :].strip()
            return bool(value)
    return False


def get_env_value(key: str, env_file: Path) -> str | None:
    """Get the value of a key from .env file, or None if not found."""
    if not env_file.exists():
        return None

    content = env_file.read_text()
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith(f"{key}="):
            value = line[len(key) + 1 :].strip()
            return value if value else None
    return None


def key_is_set(key: str, env_file: Path) -> bool:
    """Check if key exists in .env file OR is already set as environment variable."""
    if os.environ.get(key):
        return True
    return key_exists_in_file(key, env_file)


def add_env_key(key: str, value: str, env_file: Path) -> None:
    """Add environment key to .env file if it doesn't exist."""
    if key_exists_in_file(key, env_file):
        return

    with open(env_file, "a") as f:
        f.write(f"{key}={value}\n")


def create_claude_config() -> bool:
    """Create ~/.claude.json with hasCompletedOnboarding flag.

    Returns True if file was created/updated, False on error.
    """
    import json

    config_path = Path.home() / ".claude.json"
    config = {"hasCompletedOnboarding": True}

    try:
        if config_path.exists():
            existing = json.loads(config_path.read_text())
            existing.update(config)
            config = existing

        config_path.write_text(json.dumps(config, indent=2) + "\n")
        return True
    except Exception:
        return False


def credentials_exist() -> bool:
    """Check if valid Claude credentials exist in ~/.claude/.credentials.json.

    Returns True if file exists with a non-empty accessToken, False otherwise.
    """
    import json

    creds_path = Path.home() / ".claude" / ".credentials.json"

    try:
        if not creds_path.exists():
            return False

        content = json.loads(creds_path.read_text())
        oauth = content.get("claudeAiOauth", {})
        access_token = oauth.get("accessToken", "")
        return bool(access_token)
    except (json.JSONDecodeError, OSError):
        return False


def create_claude_credentials(token: str) -> bool:
    """Create ~/.claude/.credentials.json with OAuth token.

    Creates the ~/.claude/ directory if needed and writes credentials
    with restrictive permissions (0o600 for file, 0o700 for directory).

    Args:
        token: The OAuth token (used for both accessToken and refreshToken)

    Returns:
        True if credentials were created successfully, False on error.
    """
    import json
    import time

    claude_dir = Path.home() / ".claude"
    creds_path = claude_dir / ".credentials.json"

    # Calculate expiry: 365 days from now in milliseconds
    expires_at = int(time.time() * 1000) + (365 * 24 * 60 * 60 * 1000)

    credentials = {
        "claudeAiOauth": {
            "accessToken": token,
            "refreshToken": token,
            "expiresAt": expires_at,
            "scopes": ["user:inference", "user:profile", "user:sessions:claude_code"],
            "subscriptionType": "max",
            "rateLimitTier": "default_claude_max_20x",
        }
    }

    try:
        # Create directory with restrictive permissions
        claude_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

        # Write credentials file
        creds_path.write_text(json.dumps(credentials, indent=2) + "\n")

        # Set restrictive file permissions (read/write only by owner)
        creds_path.chmod(0o600)

        return True
    except (OSError, IOError):
        return False


def _prompt_github_token(ctx: InstallContext) -> str | None:
    """Prompt user for GitHub Personal Access Token."""
    ui = ctx.ui
    if not ui or ui.non_interactive:
        return None

    if not ui.confirm("Configure GitHub MCP Server?", default=True):
        return None

    ui.info("GitHub token requires 'repo' and 'read:org' scopes minimum")
    ui.info("Create at: https://github.com/settings/personal-access-tokens/new")

    token = ui.password("GitHub Personal Access Token")
    return token if token else None


def _prompt_gitlab_token(ctx: InstallContext) -> str | None:
    """Prompt user for GitLab Personal Access Token."""
    ui = ctx.ui
    if not ui or ui.non_interactive:
        return None

    if not ui.confirm("Configure GitLab MCP Server?", default=True):
        return None

    ui.info("GitLab token requires 'api' scope minimum")
    ui.info("Create at: https://gitlab.com/-/user_settings/personal_access_tokens")

    token = ui.password("GitLab Personal Access Token")
    return token if token else None


class EnvironmentStep(BaseStep):
    """Step that sets up the .env file for API keys."""

    name = "environment"

    def check(self, ctx: InstallContext) -> bool:
        """Always returns False - environment step should always run to check for missing keys."""
        return False

    def run(self, ctx: InstallContext) -> None:
        """Set up .env file with API keys."""
        ui = ctx.ui
        env_file = ctx.project_dir / ".env"

        if ctx.skip_env or ctx.non_interactive:
            if ui:
                ui.status("Skipping .env setup")
            return

        if ui:
            ui.section("API Keys Setup")

        append_mode = env_file.exists()

        if append_mode:
            removed_keys = cleanup_obsolete_env_keys(env_file)
            if removed_keys and ui:
                ui.print(f"  [dim]Removed obsolete keys: {', '.join(removed_keys)}[/dim]")

        if append_mode:
            if ui:
                ui.success("Found existing .env file")
                ui.print("  We'll append Claude CodePro configuration to your existing file.")
                ui.print()
        else:
            if ui:
                ui.print("  Let's set up your API keys. I'll guide you through each one.")
                ui.print()

        openai_api_key = ""

        if not key_is_set("OPENAI_API_KEY", env_file):
            if ui:
                ui.print()
                ui.rule("OpenAI API Key - Semantic Code Search")
                ui.print()
                ui.print("  [bold]Used for:[/bold] Generating embeddings for Vexor semantic search (cheap)")
                ui.print("  [bold]Why:[/bold] Powers fast, intelligent code search across your codebase")
                ui.print("  [bold]Create at:[/bold] [cyan]https://platform.openai.com/api-keys[/cyan]")
                ui.print()

                openai_api_key = ui.input("OPENAI_API_KEY", default="")
        else:
            if ui:
                ui.success("OPENAI_API_KEY already set, skipping")

        add_env_key("OPENAI_API_KEY", openai_api_key, env_file)

        firecrawl_api_key = ""

        if not key_is_set("FIRECRAWL_API_KEY", env_file):
            if ui:
                ui.print()
                ui.rule("Firecrawl API Key - Web Scraping & Search")
                ui.print()
                ui.print("  [bold]Used for:[/bold] Web scraping, search, and content extraction")
                ui.print("  [bold]Why:[/bold] Powers intelligent web research and documentation fetching")
                ui.print(
                    "  [bold]Create at:[/bold] [cyan]https://www.firecrawl.dev/app/api-keys[/cyan] (free tier available)"
                )
                ui.print()

                firecrawl_api_key = ui.input("FIRECRAWL_API_KEY", default="")
        else:
            if ui:
                ui.success("FIRECRAWL_API_KEY already set, skipping")

        add_env_key("FIRECRAWL_API_KEY", firecrawl_api_key, env_file)

        # Claude OAuth Token (optional - for long-lasting sessions)
        # Check both .env file AND credentials file
        token_in_env = key_is_set("CLAUDE_CODE_OAUTH_TOKEN", env_file)
        token_in_creds = credentials_exist()

        if token_in_env and not token_in_creds:
            # Auto-restore: token in .env but credentials file missing (devcontainer rebuilt)
            existing_token = get_env_value("CLAUDE_CODE_OAUTH_TOKEN", env_file)
            if existing_token and ui:
                ui.status("Restoring OAuth credentials from .env...")
                if create_claude_credentials(existing_token):
                    create_claude_config()
                    ui.success("OAuth credentials restored to ~/.claude/.credentials.json")
                else:
                    ui.warning("Could not restore credentials file")

        if not token_in_env and not token_in_creds:
            if ui:
                ui.print()
                ui.rule("Claude Long Lasting Token (Optional)")
                ui.print()
                ui.print("  [bold]Used for:[/bold] Persistent OAuth authentication (Max subscription)")
                ui.print("  [bold]Why:[/bold] Avoids repeated OAuth prompts in container environments")
                ui.print("  [bold]Get token:[/bold] Run [cyan]claude setup-token[/cyan] outside container")
                ui.print()

                use_oauth = ui.confirm("Use Claude Long Lasting Token?", default=False)

                if use_oauth:
                    oauth_token = ui.input("CLAUDE_CODE_OAUTH_TOKEN", default="")
                    if oauth_token:
                        # Store in .env for persistence across devcontainer rebuilds
                        add_env_key("CLAUDE_CODE_OAUTH_TOKEN", oauth_token, env_file)
                        # Write credentials file for Claude Code to use
                        if create_claude_credentials(oauth_token):
                            create_claude_config()
                            ui.success("OAuth credentials saved to .env and ~/.claude/.credentials.json")
                        else:
                            ui.warning("Token saved to .env but could not create credentials file")
                        # Warn about ANTHROPIC_API_KEY conflict
                        if key_is_set("ANTHROPIC_API_KEY", env_file):
                            ui.warning("ANTHROPIC_API_KEY is set - it may override OAuth token!")
                else:
                    ui.info("Skipping OAuth token setup")
        elif token_in_env or token_in_creds:
            if ui:
                if token_in_creds:
                    ui.success("OAuth credentials already configured, skipping")
                else:
                    ui.success("CLAUDE_CODE_OAUTH_TOKEN in .env, skipping")

        # MCP Server tokens (GitHub/GitLab) - smart detection based on git remotes
        is_github, is_gitlab = detect_git_hosting(ctx.project_dir)

        # GitHub MCP token
        if not key_is_set(GITHUB_TOKEN_KEY, env_file):
            if is_github or not is_gitlab:  # Prompt if GitHub detected OR if neither detected
                if ui:
                    ui.print()
                    ui.rule("GitHub MCP Server (Optional)")
                github_token = _prompt_github_token(ctx)
                if github_token:
                    add_env_key(GITHUB_TOKEN_KEY, github_token, env_file)
                    ctx.config["github_mcp_configured"] = True
                    if ui:
                        ui.success("GitHub token saved to .env")
        else:
            if ui:
                ui.success(f"{GITHUB_TOKEN_KEY} already set, skipping")
            ctx.config["github_mcp_configured"] = True

        # GitLab MCP token
        if not key_is_set(GITLAB_TOKEN_KEY, env_file):
            if is_gitlab or not is_github:  # Prompt if GitLab detected OR if neither detected
                if ui:
                    ui.print()
                    ui.rule("GitLab MCP Server (Optional)")
                gitlab_token = _prompt_gitlab_token(ctx)
                if gitlab_token:
                    add_env_key(GITLAB_TOKEN_KEY, gitlab_token, env_file)
                    ctx.config["gitlab_mcp_configured"] = True
                    if ui:
                        ui.success("GitLab token saved to .env")
        else:
            if ui:
                ui.success(f"{GITLAB_TOKEN_KEY} already set, skipping")
            ctx.config["gitlab_mcp_configured"] = True

        if ui:
            if append_mode:
                ui.success("Updated .env file with Claude CodePro configuration")
            else:
                ui.success("Created .env file with your API keys")

    def rollback(self, ctx: InstallContext) -> None:
        """No rollback for environment setup."""
        pass
