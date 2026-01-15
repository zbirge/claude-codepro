"""User configuration persistence for installer preferences."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

CONFIG_DIR = ".claude/config"
CONFIG_FILE = "ccp-config.json"


def get_config_path(project_dir: Path) -> Path:
    """Get the path to the config file."""
    return project_dir / CONFIG_DIR / CONFIG_FILE


def load_config(project_dir: Path) -> dict[str, Any]:
    """Load user configuration from .claude/config/ccp-config.json."""
    config_path = get_config_path(project_dir)
    if config_path.exists():
        try:
            return json.loads(config_path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_config(project_dir: Path, config: dict[str, Any]) -> bool:
    """Save user configuration to .claude/config/ccp-config.json."""
    config_path = get_config_path(project_dir)
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config, indent=2) + "\n")
        return True
    except OSError:
        return False


def get_preference(project_dir: Path, key: str, default: Any = None) -> Any:
    """Get a single preference value."""
    config = load_config(project_dir)
    return config.get(key, default)


def set_preference(project_dir: Path, key: str, value: Any) -> bool:
    """Set a single preference value."""
    config = load_config(project_dir)
    config[key] = value
    return save_config(project_dir, config)


LICENSE_DIR = Path.home() / ".config" / "claude-codepro"
LICENSE_FILE = ".state"
_LICENSE_SALT = "ccp_v1_"


def _compute_signature(data: str) -> str:
    """Compute signature for license data."""
    return hashlib.sha256((_LICENSE_SALT + data).encode()).hexdigest()[:16]


def get_license_path() -> Path:
    """Get the path to the user-level license file."""
    return LICENSE_DIR / LICENSE_FILE


def load_license() -> dict[str, Any]:
    """Load license info from user-level config (obfuscated format)."""
    license_path = get_license_path()
    if license_path.exists():
        try:
            content = license_path.read_text().strip()
            if ":" not in content:
                return {}
            sig, encoded = content.split(":", 1)
            decoded = base64.b64decode(encoded).decode()
            if _compute_signature(decoded) != sig:
                return {}
            return json.loads(decoded)
        except (json.JSONDecodeError, OSError, ValueError):
            return {}
    return {}


def save_license(license_data: dict[str, Any]) -> bool:
    """Save license info to user-level config (obfuscated format)."""
    license_path = get_license_path()
    try:
        license_path.parent.mkdir(parents=True, exist_ok=True)
        data_json = json.dumps(license_data, separators=(",", ":"))
        encoded = base64.b64encode(data_json.encode()).decode()
        sig = _compute_signature(data_json)
        license_path.write_text(f"{sig}:{encoded}\n")
        return True
    except OSError:
        return False


def is_license_acknowledged() -> bool:
    """Check if license has been acknowledged."""
    license_data = load_license()
    return license_data.get("acknowledged", False)


def get_license_type() -> str:
    """Get the license type (free, commercial_eval, commercial)."""
    license_data = load_license()
    return license_data.get("type", "unknown")


def acknowledge_license(license_type: str) -> bool:
    """Acknowledge the license with a given type."""
    return save_license({"acknowledged": True, "type": license_type})
