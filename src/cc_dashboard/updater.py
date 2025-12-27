"""Auto-update functionality for CC Dashboard."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from typing import Any
from urllib.request import urlopen
from urllib.error import URLError
import json

from . import __version__

GITHUB_REPO = "RedesignedRobot/cc-dashboard"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
REQUEST_TIMEOUT = 5  # seconds


@dataclass
class ReleaseInfo:
    """Information about a GitHub release."""
    version: str
    tag_name: str
    name: str
    body: str  # Release notes / changelog
    html_url: str
    published_at: str

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "ReleaseInfo":
        """Parse GitHub API response into ReleaseInfo."""
        tag = data.get("tag_name", "")
        # Strip leading 'v' if present (e.g., "v1.2.0" -> "1.2.0")
        version = tag.lstrip("v")
        return cls(
            version=version,
            tag_name=tag,
            name=data.get("name", ""),
            body=data.get("body", ""),
            html_url=data.get("html_url", ""),
            published_at=data.get("published_at", ""),
        )


def parse_version(version: str) -> tuple[int, ...]:
    """Parse version string into tuple for comparison.

    Handles versions like "1.2.0", "1.2.0-beta", etc.
    """
    # Take only the numeric part before any dash
    base_version = version.split("-")[0]
    try:
        return tuple(int(x) for x in base_version.split("."))
    except ValueError:
        return (0, 0, 0)


def is_newer_version(latest: str, current: str) -> bool:
    """Check if latest version is newer than current."""
    return parse_version(latest) > parse_version(current)


def check_for_update() -> ReleaseInfo | None:
    """Check GitHub for a newer version.

    Returns ReleaseInfo if update available, None otherwise.
    Fails silently on network errors.
    """
    try:
        with urlopen(GITHUB_API_URL, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))

        release = ReleaseInfo.from_api_response(data)

        if is_newer_version(release.version, __version__):
            return release
        return None

    except (URLError, json.JSONDecodeError, KeyError, TimeoutError):
        # Fail silently - network issues shouldn't break the app
        return None


def perform_update() -> tuple[bool, str]:
    """Perform self-update using pipx.

    Returns (success, message) tuple.
    """
    try:
        # First try pipx upgrade
        result = subprocess.run(
            ["pipx", "upgrade", "cc-dashboard"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            return True, "Update successful! Restart ccd to use the new version."

        # If upgrade failed, try reinstall
        result = subprocess.run(
            ["pipx", "install", "--force", f"git+https://github.com/{GITHUB_REPO}.git"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            return True, "Update successful! Restart ccd to use the new version."

        return False, f"Update failed: {result.stderr}"

    except FileNotFoundError:
        return False, "pipx not found. Install with: pip install pipx"
    except subprocess.TimeoutExpired:
        return False, "Update timed out. Try manually: pipx upgrade cc-dashboard"
    except Exception as e:
        return False, f"Update failed: {e}"


def format_update_message(release: ReleaseInfo) -> str:
    """Format a concise update notification message."""
    lines = [
        f"[bold yellow]Update available![/] v{__version__} → v{release.version}",
    ]

    # Add first line of release notes if available
    if release.body:
        first_line = release.body.strip().split("\n")[0][:60]
        if first_line:
            lines.append(f"[dim]{first_line}...[/]")

    lines.append("[dim]Press 'u' to update or visit:[/]")
    lines.append(f"[cyan]{release.html_url}[/]")

    return "\n".join(lines)
