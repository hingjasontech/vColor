"""Portable palette documents.

A ``vcolor.palette`` JSON file is the interchange format used by the CLI and
by palette files exported from the app. It deliberately keeps only data that
is meaningful outside vColor: a name, colors, and optional source metadata.
Internal ids and timestamps stay in the application database.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .color_utils import ColorError, normalize_hex, slugify
from .models import ColorEntry, Project

FORMAT = "vcolor.palette"
FORMAT_VERSION = 1

PALETTE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "vColor portable palette",
    "type": "object",
    "required": ["name", "colors"],
    "properties": {
        "format": {"const": FORMAT},
        "version": {"type": "integer", "minimum": 1},
        "id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9_-]*$"},
        "name": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "source": {"type": "string"},
        "license": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "colors": {
            "oneOf": [
                {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "oneOf": [
                            {"$ref": "#/$defs/color"},
                            {"type": "string"},
                        ]
                    },
                },
                {
                    "type": "object",
                    "minProperties": 1,
                    "additionalProperties": {"type": "string"},
                },
            ]
        },
    },
    "additionalProperties": True,
    "$defs": {
        "color": {
            "type": "object",
            "required": ["name", "hex"],
            "properties": {
                "name": {"type": "string"},
                "hex": {
                    "type": "string",
                    "pattern": "^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$",
                },
            },
        }
    },
}


@dataclass(slots=True)
class PortablePalette:
    """A single palette that can live outside the app database."""

    id: str
    name: str
    colors: list[ColorEntry]
    description: str = ""
    source: str = ""
    license: str = ""
    tags: list[str] = field(default_factory=list)
    version: int = FORMAT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": FORMAT,
            "version": self.version,
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "license": self.license,
            "tags": list(self.tags),
            "colors": [
                {"name": color.name, "hex": color.hex} for color in self.colors
            ],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "PortablePalette":
        if not isinstance(raw, dict):
            raise ValueError("Palette file must contain a JSON object")
        palette_format = raw.get("format")
        if palette_format not in (None, FORMAT):
            raise ValueError(f"Unsupported palette format: {palette_format!r}")
        name = str(raw.get("name") or "").strip()
        if not name:
            raise ValueError("Palette file is missing a name")
        colors = _parse_colors(raw.get("colors"))
        if not colors:
            raise ValueError(f"Palette {name!r} contains no valid colors")
        try:
            version = int(raw.get("version", FORMAT_VERSION))
        except (TypeError, ValueError):
            version = FORMAT_VERSION
        tags = raw.get("tags") or []
        if not isinstance(tags, list):
            tags = []
        return cls(
            id=str(raw.get("id") or slugify(name, "palette")),
            name=name,
            colors=colors,
            description=str(raw.get("description") or ""),
            source=str(raw.get("source") or ""),
            license=str(raw.get("license") or ""),
            tags=[str(tag) for tag in tags],
            version=version,
        )

    @classmethod
    def from_project(
        cls, project: Project, *, palette_id: str | None = None
    ) -> "PortablePalette":
        return cls(
            id=palette_id or slugify(project.name, "palette"),
            name=project.name,
            colors=list(project.colors),
        )

    def to_project(self, *, name: str | None = None) -> Project:
        return Project(
            name=name or self.name,
            colors=[
                ColorEntry(name=color.name, hex=color.hex) for color in self.colors
            ],
        )


def _parse_colors(items: Any) -> list[ColorEntry]:
    if isinstance(items, dict):
        items = [{"name": name, "hex": value} for name, value in items.items()]
    if not isinstance(items, list):
        return []

    colors: list[ColorEntry] = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, str):
            name, value = f"Color {index}", item
        elif isinstance(item, dict):
            name = str(item.get("name") or f"Color {index}")
            value = item.get("hex") or item.get("value") or item.get("color")
        else:
            continue
        if not isinstance(value, str):
            continue
        try:
            colors.append(ColorEntry(name=name, hex=normalize_hex(value)))
        except ColorError:
            continue
    return colors


def load_palette(path: str | Path) -> PortablePalette:
    """Read a portable palette file."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc
    return PortablePalette.from_dict(raw)


def save_palette(palette: PortablePalette, path: str | Path) -> Path:
    """Write a palette as portable JSON and return the path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(palette.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path
