from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vcolor.models import AppData, ColorEntry
from vcolor.palette_format import PortablePalette, save_palette
from vcolor.project_files import (
    MAX_PROJECT_BYTES,
    project_from_portable,
    read_project_file,
    unique_project_name,
)


class ProjectFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.data = AppData()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def portable(self, name: str = "Test Theme") -> PortablePalette:
        return PortablePalette(
            id="test-theme",
            name=name,
            colors=[
                ColorEntry(name="Background", hex="#101014"),
                ColorEntry(name="Accent", hex="#0a84ff"),
            ],
        )

    def test_read_project_file_preserves_colors(self) -> None:
        path = save_palette(self.portable(), self.directory / "test-theme.json")
        portable = read_project_file(path)
        self.assertEqual(portable.name, "Test Theme")
        self.assertEqual(
            [color.hex for color in portable.colors], ["#101014", "#0a84ff"]
        )

    def test_read_project_file_rejects_large_files(self) -> None:
        path = self.directory / "huge.json"
        path.write_text("x" * (MAX_PROJECT_BYTES + 1), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "larger than"):
            read_project_file(path)

    def test_project_from_portable_appends_without_replacing(self) -> None:
        existing = project_from_portable(self.data, self.portable("Existing"))
        imported = project_from_portable(self.data, self.portable("Imported"))
        self.assertEqual([project.name for project in self.data.projects], ["Existing", "Imported"])
        self.assertIs(self.data.projects[0], existing)
        self.assertIs(self.data.projects[1], imported)

    def test_duplicate_names_get_numbered_copies(self) -> None:
        for _ in range(3):
            project_from_portable(self.data, self.portable())
        self.assertEqual(
            [project.name for project in self.data.projects],
            ["Test Theme", "Test Theme (2)", "Test Theme (3)"],
        )

    def test_unique_project_name_ignores_case(self) -> None:
        project_from_portable(self.data, self.portable("Theme"))
        self.assertEqual(unique_project_name(self.data, "theme"), "theme (2)")


if __name__ == "__main__":
    unittest.main()
