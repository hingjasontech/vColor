"""Detect the operating system accent color.

The app follows the system accent color by default. Detection is best-effort:
when the platform does not expose a usable value, :func:`system_accent_color`
returns the vColor fallback accent.
"""

from __future__ import annotations

import shutil
import subprocess
import sys

from .color_utils import ColorError, DEFAULT_ACCENT, normalize_hex

FALLBACK_ACCENT = DEFAULT_ACCENT

GNOME_ACCENTS = {
    "blue": "#3584e4",
    "teal": "#2190a4",
    "green": "#3a944a",
    "yellow": "#c88800",
    "orange": "#ed5b00",
    "red": "#e62d42",
    "pink": "#d56199",
    "purple": "#9141ac",
    "slate": "#6f8396",
}

MACOS_ACCENTS = {
    "-1": "#8e8e93",
    "0": "#ff3b30",
    "1": "#ff9500",
    "2": "#ffcc00",
    "3": "#34c759",
    "4": "#007aff",
    "5": "#af52de",
    "6": "#ff2d55",
}


def system_accent_color() -> str:
    """Return the current system accent as ``#rrggbb`` or the fallback."""
    try:
        detected = _detect()
    except Exception:
        detected = None
    if not detected:
        return FALLBACK_ACCENT
    try:
        return normalize_hex(detected)
    except (ColorError, AttributeError, TypeError):
        return FALLBACK_ACCENT


def _detect() -> str | None:
    if sys.platform == "win32":
        return _windows_accent()
    if sys.platform == "darwin":
        return _macos_accent()
    return _linux_accent()


def _windows_accent() -> str | None:
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM"
        ) as key:
            raw, _ = winreg.QueryValueEx(key, "ColorizationColor")
    except OSError:
        return None
    return _windows_colorization(int(raw))


def _windows_colorization(raw: int) -> str | None:
    """Convert a Windows ``ColorizationColor`` ARGB value to hex."""
    value = int(raw) & 0xFFFFFFFF
    red = (value >> 16) & 0xFF
    green = (value >> 8) & 0xFF
    blue = value & 0xFF
    if red == green == blue == 0:
        return None
    return f"#{red:02x}{green:02x}{blue:02x}"


def _macos_accent() -> str | None:
    result = _run(
        shutil.which("defaults"), "read", "-g", "AppleHighlightColor"
    )
    if result is not None:
        parsed = _macos_highlight(result)
        if parsed:
            return parsed

    result = _run(shutil.which("defaults"), "read", "-g", "AppleAccentColor")
    if result is not None:
        return MACOS_ACCENTS.get(result.strip().strip("'\""))
    return None


def _macos_highlight(raw: str) -> str | None:
    parts = raw.split()
    if len(parts) < 3:
        return None
    try:
        channels = [round(float(part) * 255.0) for part in parts[:3]]
    except ValueError:
        return None
    return _channels_to_hex(channels)


def _linux_accent() -> str | None:
    result = _run(
        shutil.which("gsettings"),
        "get",
        "org.gnome.desktop.interface",
        "accent-color",
    )
    if result is not None:
        name = result.strip().strip("'\"").lower()
        accent = GNOME_ACCENTS.get(name)
        if accent:
            return accent

    for command in ("kreadconfig6", "kreadconfig5"):
        result = _run(
            shutil.which(command),
            "--file",
            "kdeglobals",
            "--group",
            "General",
            "--key",
            "AccentColor",
        )
        if result is not None:
            accent = _channels_to_hex(result.split(","))
            if accent:
                return accent
    return None


def _channels_to_hex(channels) -> str | None:
    if len(channels) < 3:
        return None
    try:
        values = [round(float(channel)) for channel in channels[:3]]
    except (TypeError, ValueError):
        return None
    if not all(0 <= value <= 255 for value in values):
        return None
    return f"#{values[0]:02x}{values[1]:02x}{values[2]:02x}"


def _run(executable: str | None, *arguments: str) -> str | None:
    if not executable:
        return None
    try:
        completed = subprocess.run(
            [executable, *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout
