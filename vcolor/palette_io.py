"""Import and export helpers for common palette formats."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from .color_utils import ColorError, normalize_hex, slugify
from .models import ColorEntry, Project

HEX_TOKEN_RE = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
CSS_VAR_RE = re.compile(
    r"--([a-zA-Z0-9_-]+)\s*:\s*(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})\b"
)


def export_palette(project: Project, path: Path, kind: str) -> None:
    kind = kind.lower().lstrip(".")
    if kind == "json":
        content = json.dumps(
            {
                "name": project.name,
                "colors": [
                    {"name": color.name, "hex": color.hex} for color in project.colors
                ],
            },
            indent=2,
            ensure_ascii=False,
        ) + "\n"
    elif kind == "css":
        content = _to_css(project)
    elif kind == "gpl":
        content = _to_gpl(project)
    else:
        raise ValueError(f"Unsupported export format: {kind}")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _to_css(project: Project) -> str:
    lines = [f"/* {project.name} - exported from vColor */", ":root {"]
    used: set[str] = set()
    for index, color in enumerate(project.colors, start=1):
        base = slugify(color.name, f"color-{index}")
        name = base
        suffix = 2
        while name in used:
            name = f"{base}-{suffix}"
            suffix += 1
        used.add(name)
        lines.append(f"  --{name}: {color.hex};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _to_gpl(project: Project) -> str:
    lines = [
        "GIMP Palette",
        f"Name: {project.name}",
        "Columns: 4",
        "#",
    ]
    for color in project.colors:
        raw = color.hex.lstrip("#")
        r, g, b = int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
        lines.append(f"{r:3d} {g:3d} {b:3d}\t{color.name}")
    return "\n".join(lines) + "\n"


def import_palette(path: Path) -> list[ColorEntry]:
    """Read colors from JSON, CSS, or GIMP palette files."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")

    suffix = path.suffix.lower()
    if suffix == ".json" or text.lstrip().startswith(("{", "[")):
        colors = _parse_json(text)
    elif suffix == ".gpl" or text.startswith("GIMP Palette"):
        colors = _parse_gpl(text)
    else:
        colors = _parse_css(text)

    if not colors:
        raise ValueError("No colors were found in this file.")
    return colors


def _parse_json(text: str) -> list[ColorEntry]:
    raw = json.loads(text)
    if isinstance(raw, dict):
        items = raw.get("colors") or raw.get("palette") or []
        if isinstance(items, dict):
            items = [{"name": name, "hex": value} for name, value in items.items()]
    elif isinstance(raw, list):
        items = raw
    else:
        items = []

    colors: list[ColorEntry] = []
    if isinstance(items, dict):
        items = [{"name": name, "hex": value} for name, value in items.items()]
    if not isinstance(items, list):
        return colors

    for index, item in enumerate(items, start=1):
        if isinstance(item, str):
            name, value = f"Color {index}", item
        elif isinstance(item, dict):
            value = item.get("hex") or item.get("value") or item.get("color")
            name = item.get("name") or item.get("title") or f"Color {index}"
        else:
            continue
        if not isinstance(value, str):
            continue
        try:
            colors.append(ColorEntry(name=str(name), hex=normalize_hex(value)))
        except ColorError:
            continue
    return colors


def _parse_css(text: str) -> list[ColorEntry]:
    colors: list[ColorEntry] = []
    seen: set[tuple[str, str]] = set()
    for match in CSS_VAR_RE.finditer(text):
        name = match.group(1).replace("-", " ").replace("_", " ").strip().title()
        try:
            value = normalize_hex(match.group(2))
        except ColorError:
            continue
        key = (name, value)
        if key not in seen:
            seen.add(key)
            colors.append(ColorEntry(name=name, hex=value))

    for index, match in enumerate(HEX_TOKEN_RE.finditer(text), start=1):
        try:
            value = normalize_hex(match.group(0))
        except ColorError:
            continue
        if any(color.hex == value for color in colors):
            continue
        colors.append(ColorEntry(name=f"Color {index}", hex=value))
    return colors


def _parse_gpl(text: str) -> list[ColorEntry]:
    colors: list[ColorEntry] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.lower().startswith(("gimp", "name:", "columns:")):
            continue
        parts = line.split(None, 3)
        if len(parts) < 3:
            continue
        try:
            r, g, b = (int(part) for part in parts[:3])
        except ValueError:
            continue
        if not all(0 <= channel <= 255 for channel in (r, g, b)):
            continue
        name = parts[3].strip() if len(parts) > 3 else "Color"
        colors.append(ColorEntry(name=name, hex=f"#{r:02x}{g:02x}{b:02x}"))
    return colors


def colors_from_strings(items: Iterable[tuple[str, str]]) -> list[ColorEntry]:
    """Small helper used by tests and future clipboard import."""
    colors: list[ColorEntry] = []
    for name, value in items:
        try:
            colors.append(ColorEntry(name=name, hex=normalize_hex(value)))
        except ColorError:
            continue
    return colors
