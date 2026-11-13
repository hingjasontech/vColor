"""Helpers for importing palette files as projects.

A project is just a name plus a list of colors. The name comes from the file
name (``catppuccin-mocha.css`` becomes ``Catppuccin Mocha``), so palette files
never need to carry project metadata. Users import files explicitly from the
sidebar or by dragging them onto the window; vColor does not watch folders.
"""

from __future__ import annotations

import re
from pathlib import Path

from .models import AppData, ColorEntry, Project
from .palette_formats import import_palette

MAX_PROJECT_BYTES = 2_000_000


def project_name_from_path(path: str | Path) -> str:
    """Turn a file name into a readable project name."""
    return humanize_filename(Path(path).stem)


def humanize_filename(value: str) -> str:
    """Convert ``catppuccin-mocha`` or ``TokyoNight`` to a title-cased name."""
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    text = re.sub(r"[-_.]+", " ", text)
    words: list[str] = []
    for word in text.split():
        if word.isdigit() or (word.isupper() and len(word) <= 4):
            words.append(word)
        else:
            words.append(word[:1].upper() + word[1:].lower())
    return " ".join(words).strip() or "Project"


def unique_project_name(data: AppData, name: str) -> str:
    """Return ``name`` or the next available ``Name (2)`` style copy."""
    base = name.strip() or "Project"
    existing = {project.name.strip().casefold() for project in data.projects}
    if base.casefold() not in existing:
        return base

    index = 2
    while f"{base} ({index})".casefold() in existing:
        index += 1
    return f"{base} ({index})"


def project_from_palette(
    data: AppData, path: str | Path, colors: list[ColorEntry]
) -> Project:
    """Create a new project named after ``path``, preserving existing projects."""
    project = Project(
        name=unique_project_name(data, project_name_from_path(path)),
        colors=[
            ColorEntry(name=color.name, hex=color.hex) for color in colors
        ],
    )
    data.projects.append(project)
    return project


def read_project_file(path: str | Path) -> list[ColorEntry]:
    """Read a palette file, rejecting oversized files."""
    path = Path(path)
    stat = path.stat()
    if stat.st_size > MAX_PROJECT_BYTES:
        raise ValueError(
            f"File is larger than {MAX_PROJECT_BYTES // 1_000_000} MB"
        )
    return import_palette(path)
