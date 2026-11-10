"""Helpers for importing portable project files.

A project file is the ``vcolor.palette`` JSON document described in
``docs/PROJECTS.md``. Users import it explicitly from the sidebar, drag it onto
the window, or export one from a project's context menu. vColor does not watch
a folder and never writes instructions or schemas into the user's data
directory.
"""

from __future__ import annotations

from pathlib import Path

from .models import AppData, Project
from .palette_format import PortablePalette, load_palette

MAX_PROJECT_BYTES = 2_000_000


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


def project_from_portable(data: AppData, portable: PortablePalette) -> Project:
    """Create a new project in ``data``, preserving existing projects."""
    project = portable.to_project(name=unique_project_name(data, portable.name))
    data.projects.append(project)
    return project


def read_project_file(path: Path) -> PortablePalette:
    """Read a project file, rejecting oversized files."""
    stat = Path(path).stat()
    if stat.st_size > MAX_PROJECT_BYTES:
        raise ValueError(
            f"File is larger than {MAX_PROJECT_BYTES // 1_000_000} MB"
        )
    return load_palette(path)
