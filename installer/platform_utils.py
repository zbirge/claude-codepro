"""Cross-platform utilities for the installer."""

from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path

import platformdirs


def has_nvidia_gpu(verbose: bool = False) -> bool | dict:
    """Check if NVIDIA GPU is available via nvidia-smi or /dev/nvidia* fallback.

    Args:
        verbose: If True, return dict with diagnostic info instead of bool.

    Returns:
        bool if verbose=False, dict with detection details if verbose=True.
    """
    result_info: dict = {
        "detected": False,
        "method": None,
        "error": None,
        "nvidia_smi_output": None,
    }

    # Method 1: nvidia-smi command
    try:
        proc = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            timeout=10,
        )
        if proc.returncode == 0:
            result_info["detected"] = True
            result_info["method"] = "nvidia_smi"
            result_info["nvidia_smi_output"] = proc.stdout.decode("utf-8", errors="replace")[:500]
            return result_info if verbose else True
        else:
            result_info["error"] = f"nvidia-smi exited with code {proc.returncode}"
            stderr = proc.stderr.decode("utf-8", errors="replace")[:200]
            if stderr:
                result_info["error"] += f": {stderr}"
    except FileNotFoundError as e:
        result_info["error"] = f"nvidia-smi not found: {e}"
    except subprocess.TimeoutExpired:
        result_info["error"] = "nvidia-smi timed out after 10 seconds"
    except OSError as e:
        result_info["error"] = f"OSError running nvidia-smi: {e}"
    except subprocess.SubprocessError as e:
        result_info["error"] = f"SubprocessError running nvidia-smi: {e}"

    # Method 2: Check for /dev/nvidia* devices (fallback)
    try:
        nvidia_devices = list(Path("/dev").glob("nvidia*"))
        if nvidia_devices:
            result_info["detected"] = True
            result_info["method"] = "dev_nvidia"
            result_info["nvidia_devices"] = [str(d) for d in nvidia_devices[:5]]
            return result_info if verbose else True
    except (OSError, PermissionError) as e:
        if result_info["error"]:
            result_info["error"] += f"; /dev/nvidia* check failed: {e}"
        else:
            result_info["error"] = f"/dev/nvidia* check failed: {e}"

    return result_info if verbose else False


def is_macos() -> bool:
    """Check if running on macOS."""
    return platform.system() == "Darwin"


def is_linux() -> bool:
    """Check if running on Linux."""
    return platform.system() == "Linux"


def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == "Windows"


def is_wsl() -> bool:
    """Check if running in Windows Subsystem for Linux."""
    if not is_linux():
        return False
    try:
        with open("/proc/version") as f:
            return "microsoft" in f.read().lower()
    except (OSError, IOError):
        return False


def is_in_devcontainer() -> bool:
    """Check if running inside a dev container."""
    return Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()


def command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(command) is not None


def get_package_manager() -> str | None:
    """Detect the system package manager."""
    if is_macos():
        if command_exists("brew"):
            return "brew"
    elif is_linux() or is_wsl():
        if command_exists("apt-get"):
            return "apt-get"
        elif command_exists("dnf"):
            return "dnf"
        elif command_exists("yum"):
            return "yum"
        elif command_exists("pacman"):
            return "pacman"
    return None


def get_config_dir() -> Path:
    """Get the user configuration directory using platformdirs."""
    return Path(platformdirs.user_config_dir("claude-codepro"))


def get_data_dir() -> Path:
    """Get the user data directory using platformdirs."""
    return Path(platformdirs.user_data_dir("claude-codepro"))


def get_shell_config_files() -> list[Path]:
    """Get list of shell configuration files for the current user."""
    home = Path.home()
    configs = []

    bashrc = home / ".bashrc"
    bash_profile = home / ".bash_profile"
    if bashrc.exists():
        configs.append(bashrc)
    if bash_profile.exists():
        configs.append(bash_profile)

    zshrc = home / ".zshrc"
    if zshrc.exists():
        configs.append(zshrc)

    fish_config = home / ".config" / "fish" / "config.fish"
    if fish_config.exists():
        configs.append(fish_config)

    if not configs:
        configs = [bashrc, zshrc, fish_config]

    return configs


def get_platform_suffix() -> str:
    """Get platform suffix for binary names (e.g., 'linux-x86_64', 'darwin-arm64')."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if machine in ("amd64", "x86_64"):
        machine = "x86_64"
    elif machine in ("arm64", "aarch64"):
        machine = "arm64"

    return f"{system}-{machine}"


def add_to_path(path: Path) -> None:
    """Add directory to PATH in shell configs."""
    export_line = f'export PATH="{path}:$PATH"'
    fish_line = f'set -gx PATH "{path}" $PATH'

    for config_file in get_shell_config_files():
        if not config_file.exists():
            continue

        content = config_file.read_text()

        if str(path) in content:
            continue

        if "fish" in config_file.name:
            line_to_add = fish_line
        else:
            line_to_add = export_line

        with open(config_file, "a") as f:
            f.write(f"\n{line_to_add}\n")
