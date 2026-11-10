"""Application data model and JSON persistence."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .color_utils import DISPLAY_FORMATS, ColorError, normalize_hex

DATA_VERSION = 1


def new_id() -> str:
    return uuid.uuid4().hex


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_data_dir() -> Path:
    """Return a platform-appropriate application data directory."""
    if sys.platform == "win32":
        root = os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming"
        return Path(root) / "vColor"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "vColor"
    root = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(root) / "vColor"


@dataclass(slots=True)
class ColorEntry:
    name: str
    hex: str
    id: str = field(default_factory=new_id)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "hex": self.hex,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ColorEntry":
        try:
            value = normalize_hex(str(raw.get("hex") or "#000000"))
        except ColorError:
            value = "#000000"
        return cls(
            id=str(raw.get("id") or new_id()),
            name=str(raw.get("name") or "Untitled color"),
            hex=value,
            created_at=str(raw.get("created_at") or utc_now()),
        )


@dataclass(slots=True)
class Project:
    name: str
    id: str = field(default_factory=new_id)
    colors: list[ColorEntry] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "colors": [color.to_dict() for color in self.colors],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Project":
        colors = [
            ColorEntry.from_dict(item)
            for item in raw.get("colors", [])
            if isinstance(item, dict)
        ]
        return cls(
            id=str(raw.get("id") or new_id()),
            name=str(raw.get("name") or "Untitled project"),
            colors=colors,
            created_at=str(raw.get("created_at") or utc_now()),
            updated_at=str(raw.get("updated_at") or utc_now()),
        )


@dataclass(slots=True)
class AppData:
    projects: list[Project] = field(default_factory=list)
    active_project_id: str | None = None
    display_format: str = "HEX"
    show_hex_hash: bool = True
    update_check: bool = True
    last_update_check: str | None = None
    skipped_version: str | None = None
    version: int = DATA_VERSION

    @property
    def active_project(self) -> Project | None:
        if not self.active_project_id:
            return None
        return next(
            (project for project in self.projects if project.id == self.active_project_id),
            None,
        )

    def find_project(self, project_id: str) -> Project | None:
        return next((project for project in self.projects if project.id == project_id), None)

    def ensure_active_project(self) -> Project | None:
        project = self.active_project
        if project is None and self.projects:
            self.active_project_id = self.projects[0].id
            project = self.projects[0]
        if project is None:
            self.active_project_id = None
        return project

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": DATA_VERSION,
            "active_project_id": self.active_project_id,
            "display_format": self.display_format,
            "show_hex_hash": self.show_hex_hash,
            "update_check": self.update_check,
            "last_update_check": self.last_update_check,
            "skipped_version": self.skipped_version,
            "projects": [project.to_dict() for project in self.projects],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "AppData":
        projects = [
            Project.from_dict(item)
            for item in raw.get("projects", [])
            if isinstance(item, dict)
        ]
        active = raw.get("active_project_id")
        active = str(active) if active else None
        display_format = str(raw.get("display_format") or "HEX").upper()
        if display_format not in DISPLAY_FORMATS:
            display_format = "HEX"
        update_check = raw.get("update_check")
        if not isinstance(update_check, bool):
            update_check = True
        show_hex_hash = raw.get("show_hex_hash")
        if not isinstance(show_hex_hash, bool):
            show_hex_hash = True
        last_check = raw.get("last_update_check")
        skipped = raw.get("skipped_version")
        data = cls(
            projects=projects,
            active_project_id=active,
            display_format=display_format,
            show_hex_hash=show_hex_hash,
            update_check=update_check,
            last_update_check=str(last_check) if last_check else None,
            skipped_version=str(skipped) if skipped else None,
        )
        data.ensure_active_project()
        return data


class StoreError(RuntimeError):
    pass


class PaletteStore:
    """Atomic JSON storage with a safe fallback for corrupt files."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.last_backup_path: Path | None = None

    def load(self) -> AppData:
        if not self.path.exists():
            return AppData()

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("Root JSON value is not an object")
            return AppData.from_dict(raw)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            self.last_backup_path = self._backup_corrupt_file()
            if self.last_backup_path:
                print(
                    f"vColor: could not read {self.path}; "
                    f"backup written to {self.last_backup_path}",
                    file=sys.stderr,
                )
            else:
                print(f"vColor: could not read {self.path}: {exc}", file=sys.stderr)
            return AppData()

    def save(self, data: AppData) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data.to_dict(), indent=2, ensure_ascii=False) + "\n"

        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.path)
        except OSError as exc:
            if temporary_path and temporary_path.exists():
                try:
                    temporary_path.unlink()
                except OSError:
                    pass
            raise StoreError(f"Could not save projects: {exc}") from exc

    def _backup_corrupt_file(self) -> Path | None:
        if not self.path.exists():
            return None
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = self.path.with_name(f"{self.path.stem}.corrupt-{stamp}.json")
        try:
            os.replace(self.path, backup)
        except OSError:
            return None
        return backup
