"""Watched palette inbox.

The inbox is the hand-off point between an AI assistant and the running app.
An assistant writes a portable ``vcolor.palette`` JSON file into the inbox;
vColor validates it, creates a new project, and moves the file into
``imported/``. Invalid files are moved into ``failed/`` after a short grace
period so an in-progress write is not rejected by accident.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from .models import AppData, Project
from .palette_format import PALETTE_SCHEMA, PortablePalette, load_palette

INBOX_DIR_NAME = "inbox"
IMPORTED_DIR_NAME = "imported"
FAILED_DIR_NAME = "failed"

# Files the app writes into the inbox. They are documentation, not palettes.
RESERVED_NAMES = frozenset({"agents.md", "readme.md", "palette-schema.json"})

MAX_PALETTE_BYTES = 2_000_000
DEFAULT_PARTIAL_WRITE_GRACE = 3.0

INBOX_AGENTS_MARKDOWN = """# vColor palette inbox

vColor watches this folder. When a valid palette file appears, the app adds it
as a project and moves the file into `imported/`. If vColor is closed, the file
is imported the next time the app starts. Invalid files move into `failed/`
after a short grace period.

## Write a palette

Create a JSON file with this shape. `palette-schema.json` in this folder has
the full schema.

```json
{
  "format": "vcolor.palette",
  "version": 1,
  "id": "my-theme",
  "name": "My Theme",
  "description": "One-line summary.",
  "source": "https://example.com/my-theme",
  "license": "MIT",
  "tags": ["dark"],
  "colors": [
    { "name": "background", "hex": "#101014" },
    { "name": "foreground", "hex": "#f2f2f7" }
  ]
}
```

Only `name` and at least one valid color are required. Use `#rrggbb` hex
values and keep the upstream `source` and `license` when they exist.

## Deliver the file safely

Write the complete document to a temporary file in this folder, then rename it
to a `.json` name. Do not write directly to the final name: vColor may read the
file before it is complete. Temporary files whose names start with `.` are
ignored.

## Import rules

- Every valid file becomes a new project and becomes active.
- If a project with the same name already exists, the new project is named
  `Name (2)`, `Name (3)`, and so on. Existing projects are never overwritten.
- vColor stores only the project name and colors. Keep `source`, `license`,
  and `tags` in the JSON file as the source of truth.
- Invalid files are moved into `failed/`.
- `AGENTS.md` and `palette-schema.json` are reserved and are never imported.
"""


@dataclass(slots=True)
class ImportedPalette:
    source: Path
    archive: Path
    project: Project


@dataclass(slots=True)
class FailedPalette:
    source: Path
    archive: Path | None
    error: str


@dataclass(slots=True)
class InboxScan:
    imported: list[ImportedPalette] = field(default_factory=list)
    failed: list[FailedPalette] = field(default_factory=list)
    pending: list[Path] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.imported or self.failed)


class PaletteInbox:
    """A folder of portable palette files waiting to be imported."""

    def __init__(
        self,
        data_dir: Path,
        *,
        partial_write_grace: float = DEFAULT_PARTIAL_WRITE_GRACE,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.root = self.data_dir / INBOX_DIR_NAME
        self.imported_dir = self.root / IMPORTED_DIR_NAME
        self.failed_dir = self.root / FAILED_DIR_NAME
        self.partial_write_grace = max(0.0, partial_write_grace)

    def ensure(self) -> bool:
        """Create the inbox and its documentation. Returns False on I/O errors."""
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            self.imported_dir.mkdir(parents=True, exist_ok=True)
            self.failed_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            return False

        self._write_if_changed(self.root / "AGENTS.md", INBOX_AGENTS_MARKDOWN)
        self._write_if_changed(
            self.root / "palette-schema.json",
            json.dumps(PALETTE_SCHEMA, indent=2, ensure_ascii=False) + "\n",
        )
        return True

    def scan(self, data: AppData) -> InboxScan:
        """Import every ready palette file into ``data``.

        Files that cannot be parsed yet but were modified very recently are
        left in place and reported as ``pending``. This makes a non-atomic
        writer safe without permanently keeping broken files.
        """
        result = InboxScan()
        if not self.ensure():
            return result

        for path in self._candidate_paths():
            try:
                stat = path.stat()
            except OSError:
                continue

            if stat.st_size > MAX_PALETTE_BYTES:
                self._reject(
                    path,
                    result,
                    f"File is larger than {MAX_PALETTE_BYTES // 1_000_000} MB",
                )
                continue

            try:
                palette = load_palette(path)
            except ValueError as exc:
                if self._is_recent(stat):
                    result.pending.append(path)
                else:
                    self._reject(path, result, str(exc))
                continue
            except OSError:
                continue

            project = palette.to_project(
                name=unique_project_name(data, palette.name)
            )
            archive = self._archive(path, self.imported_dir)
            if archive is None:
                result.pending.append(path)
                continue

            data.projects.append(project)
            result.imported.append(
                ImportedPalette(source=path, archive=archive, project=project)
            )

        return result

    def _candidate_paths(self) -> list[Path]:
        try:
            entries = list(self.root.iterdir())
        except OSError:
            return []

        paths: list[Path] = []
        for path in entries:
            try:
                if not path.is_file():
                    continue
            except OSError:
                continue
            name = path.name.casefold()
            if name.startswith(".") or name in RESERVED_NAMES:
                continue
            if path.suffix.casefold() != ".json":
                continue
            paths.append(path)
        return sorted(paths, key=lambda item: (_mtime(item), item.name.casefold()))

    def _is_recent(self, stat: os.stat_result) -> bool:
        if self.partial_write_grace <= 0:
            return False
        return time.time() - stat.st_mtime < self.partial_write_grace

    def _reject(self, path: Path, result: InboxScan, error: str) -> None:
        archive = self._archive(path, self.failed_dir)
        if archive is None:
            result.pending.append(path)
            return
        result.failed.append(FailedPalette(source=path, archive=archive, error=error))

    @staticmethod
    def _archive(path: Path, directory: Path) -> Path | None:
        target = unique_path(directory, path.name)
        try:
            os.replace(path, target)
        except OSError:
            try:
                shutil.move(str(path), str(target))
            except OSError:
                return None
        return target

    @staticmethod
    def _write_if_changed(path: Path, content: str) -> None:
        try:
            if path.is_file() and path.read_text(encoding="utf-8") == content:
                return
        except OSError:
            pass

        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        try:
            temporary.write_text(content, encoding="utf-8")
            os.replace(temporary, path)
        except OSError:
            try:
                temporary.unlink()
            except OSError:
                pass


def unique_project_name(data: AppData, name: str) -> str:
    """Return ``name`` or the next available ``Name (2)`` style copy."""
    base = name.strip() or "Palette"
    existing = {project.name.strip().casefold() for project in data.projects}
    if base.casefold() not in existing:
        return base

    index = 2
    while f"{base} ({index})".casefold() in existing:
        index += 1
    return f"{base} ({index})"


def unique_path(directory: Path, filename: str) -> Path:
    """Return a non-existing path in ``directory`` based on ``filename``."""
    candidate = directory / filename
    if not candidate.exists():
        return candidate

    path = Path(filename)
    stem = path.stem or "palette"
    suffix = path.suffix
    index = 2
    while True:
        candidate = directory / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def project_from_palette(data: AppData, palette: PortablePalette) -> Project:
    """Create a new project in ``data``, preserving existing projects."""
    project = palette.to_project(name=unique_project_name(data, palette.name))
    data.projects.append(project)
    return project


def read_palette_file(path: Path) -> PortablePalette:
    """Read a palette file for drag-and-drop, rejecting oversized files."""
    stat = Path(path).stat()
    if stat.st_size > MAX_PALETTE_BYTES:
        raise ValueError(
            f"File is larger than {MAX_PALETTE_BYTES // 1_000_000} MB"
        )
    return load_palette(path)


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0
