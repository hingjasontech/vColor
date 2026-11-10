from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from vcolor.inbox import (
    FailedPalette,
    PaletteInbox,
    project_from_palette,
    read_palette_file,
    unique_project_name,
)
from vcolor.models import AppData, ColorEntry
from vcolor.palette_format import PortablePalette, save_palette


class PaletteInboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.data_dir = self.directory / "data"
        self.inbox = PaletteInbox(self.data_dir, partial_write_grace=0.0)
        self.data = AppData()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def palette(self, name: str = "Test Theme") -> PortablePalette:
        return PortablePalette(
            id="test-theme",
            name=name,
            colors=[
                ColorEntry(name="Background", hex="#101014"),
                ColorEntry(name="Accent", hex="#0a84ff"),
            ],
        )

    def write_palette(self, filename: str = "test-theme.json", name: str = "Test Theme") -> Path:
        return save_palette(self.palette(name), self.inbox.root / filename)

    def write_invalid(self, filename: str = "broken.json") -> Path:
        self.inbox.ensure()
        path = self.inbox.root / filename
        path.write_text('{"name": "Broken"}\n', encoding="utf-8")
        return path

    def age(self, path: Path, seconds: float = 60) -> None:
        timestamp = time.time() - seconds
        os.utime(path, (timestamp, timestamp))

    def test_ensure_creates_folders_and_documentation(self) -> None:
        self.assertTrue(self.inbox.ensure())
        self.assertTrue(self.inbox.root.is_dir())
        self.assertTrue(self.inbox.imported_dir.is_dir())
        self.assertTrue(self.inbox.failed_dir.is_dir())
        self.assertTrue((self.inbox.root / "AGENTS.md").is_file())
        schema = json.loads(
            (self.inbox.root / "palette-schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(schema["required"], ["name", "colors"])
        self.assertEqual(schema["properties"]["format"]["const"], "vcolor.palette")

    def test_valid_palette_is_imported_and_archived(self) -> None:
        source = self.write_palette()

        result = self.inbox.scan(self.data)

        self.assertEqual(len(result.imported), 1)
        self.assertEqual(result.failed, [])
        self.assertFalse(source.exists())
        self.assertTrue((self.inbox.imported_dir / "test-theme.json").is_file())
        self.assertEqual(len(self.data.projects), 1)
        project = self.data.projects[0]
        self.assertEqual(project.name, "Test Theme")
        self.assertEqual(
            [color.hex for color in project.colors], ["#101014", "#0a84ff"]
        )

    def test_duplicate_names_get_numbered_copies(self) -> None:
        self.write_palette("first.json")
        self.inbox.scan(self.data)
        self.write_palette("second.json")
        self.inbox.scan(self.data)
        self.write_palette("third.json")
        self.inbox.scan(self.data)

        self.assertEqual(
            [project.name for project in self.data.projects],
            ["Test Theme", "Test Theme (2)", "Test Theme (3)"],
        )

    def test_duplicate_filenames_are_archived_without_overwriting(self) -> None:
        self.write_palette("theme.json")
        self.inbox.scan(self.data)
        self.write_palette("theme.json", name="Other Theme")
        self.inbox.scan(self.data)

        self.assertTrue((self.inbox.imported_dir / "theme.json").is_file())
        self.assertTrue((self.inbox.imported_dir / "theme-2.json").is_file())
        self.assertEqual(len(self.data.projects), 2)

    def test_invalid_file_moves_to_failed(self) -> None:
        source = self.write_invalid()
        self.age(source)

        result = self.inbox.scan(self.data)

        self.assertEqual(result.imported, [])
        self.assertEqual(len(result.failed), 1)
        self.assertFalse(source.exists())
        failed = self.inbox.failed_dir / "broken.json"
        self.assertTrue(failed.is_file())
        self.assertIn("no valid colors", result.failed[0].error)

    def test_recent_invalid_file_is_left_for_the_next_scan(self) -> None:
        source = self.write_invalid()
        inbox = PaletteInbox(self.data_dir)

        result = inbox.scan(self.data)

        self.assertEqual(result.failed, [])
        self.assertEqual(result.pending, [source])
        self.assertTrue(source.exists())
        self.assertEqual(self.data.projects, [])

    def test_reserved_and_non_palette_files_are_ignored(self) -> None:
        self.inbox.ensure()
        (self.inbox.root / "notes.txt").write_text("not a palette", encoding="utf-8")
        (self.inbox.root / ".hidden.json").write_text("{}", encoding="utf-8")
        (self.inbox.root / "imported").mkdir(exist_ok=True)

        result = self.inbox.scan(self.data)

        self.assertEqual(result.imported, [])
        self.assertEqual(result.failed, [])
        self.assertEqual(self.data.projects, [])

    def test_failed_archive_name_does_not_overwrite_an_earlier_failure(self) -> None:
        first = self.write_invalid("broken.json")
        self.age(first)
        self.inbox.scan(self.data)
        second = self.write_invalid("broken.json")
        self.age(second)
        self.inbox.scan(self.data)

        self.assertTrue((self.inbox.failed_dir / "broken.json").is_file())
        self.assertTrue((self.inbox.failed_dir / "broken-2.json").is_file())

    def test_scan_imports_good_files_while_a_recent_file_is_pending(self) -> None:
        self.write_palette()
        recent = self.write_invalid("recent.json")
        inbox = PaletteInbox(self.data_dir)

        result = inbox.scan(self.data)

        self.assertEqual(len(result.imported), 1)
        self.assertEqual(result.pending, [recent])
        self.assertEqual(len(self.data.projects), 1)

    def test_unique_project_name_ignores_case(self) -> None:
        self.data.projects.append(project_from_palette(self.data, self.palette("Theme")))
        self.assertEqual(unique_project_name(self.data, "theme"), "theme (2)")

    def test_read_palette_file_rejects_large_files(self) -> None:
        path = self.inbox.root / "huge.json"
        self.inbox.ensure()
        path.write_text("x" * 2_000_001, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "larger than"):
            read_palette_file(path)

    def test_imported_palette_keeps_colors_and_does_not_need_metadata(self) -> None:
        source = self.write_palette()
        palette = read_palette_file(source)
        project = project_from_palette(self.data, palette)
        self.assertEqual(project.name, "Test Theme")
        self.assertEqual(len(project.colors), 2)

    def test_failed_palette_records_the_archive_path(self) -> None:
        source = self.write_invalid()
        self.age(source)
        result = self.inbox.scan(self.data)
        failed: FailedPalette = result.failed[0]
        self.assertEqual(failed.archive, self.inbox.failed_dir / "broken.json")


if __name__ == "__main__":
    unittest.main()
