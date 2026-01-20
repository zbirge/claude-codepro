#!/usr/bin/env python3
"""Build script for ccp-installer binary using PyInstaller."""

import platform
import subprocess
import sys
from pathlib import Path


def get_binary_name() -> str:
    """Get the platform-specific binary name."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        os_name = "darwin"
    elif system == "linux":
        os_name = "linux"
    else:
        os_name = system

    if machine in ("x86_64", "amd64"):
        arch = "x86_64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        arch = machine

    return f"ccp-installer-{os_name}-{arch}"


def build() -> None:
    """Build the installer binary."""
    script_dir = Path(__file__).parent
    binary_name = get_binary_name()
    dist_dir = script_dir / "dist"

    dist_dir.mkdir(exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        binary_name,
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(script_dir / "build"),
        "--specpath",
        str(script_dir),
        "--clean",
        "--noconfirm",
        str(script_dir / "__main__.py"),
    ]

    print(f"Building {binary_name}...")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"Build failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    binary_path = dist_dir / binary_name
    if binary_path.exists():
        print(f"Successfully built: {binary_path}")
    else:
        print(f"Error: Binary not found at {binary_path}")
        sys.exit(1)


if __name__ == "__main__":
    build()
