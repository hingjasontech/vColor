from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vcolor.models import AppData, ColorEntry, Project
from vcolor.palette_formats import export_palette
from vcolor.project_files import (
    MAX_PROJECT_BYTES,
    humanize_filename,
    project_from_palette,
    project_name_from_path,
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

    @staticmethod
    def colors() -> list[ColorEntry]:
        return [
            ColorEntry(name="Background", hex="#101014"),
            ColorEntry(name="Accent", hex="#0a84ff"),
        ]

    @staticmethod
    def project() -> Project:
        return Project(name="Ignored", colors=ProjectFileTests.colors())

    def test_project_names_come_from_file_names(self) -> None:
        self.assertEqual(
            project_name_from_path("catppuccin-mocha.json"), "Catppuccin Mocha"
        )
        self.assertEqual(project_name_from_path("TokyoNight.css"), "Tokyo Night")
        self.assertEqual(project_name_from_path("my_theme.v2.txt"), "My Theme V2")

    def test_humanize_falls_back_for_empty_names(self) -> None:
        self.assertEqual(humanize_filename("---"), "Project")

    def test_read_project_file_preserves_colors(self) -> None:
        path = export_palette(
            self.project(), self.directory / "test-theme.json", "json"
        )
        colors = read_project_file(path)
        self.assertEqual(
            [color.hex for color in colors], ["#101014", "#0a84ff"]
        )
        self.assertEqual(colors[0].name, "Background")

    def test_read_project_file_rejects_large_files(self) -> None:
        path = self.directory / "huge.json"
        path.write_text("x" * (MAX_PROJECT_BYTES + 1), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "larger than"):
            read_project_file(path)

    def test_project_from_palette_appends_without_replacing(self) -> None:
        existing = Project(name="Existing")
        self.data.projects.append(existing)
        imported = project_from_palette(
            self.data, self.directory / "imported-theme.css", self.colors()
        )
        self.assertEqual(
            [project.name for project in self.data.projects],
            ["Existing", "Imported Theme"],
        )
        self.assertIs(self.data.projects[0], existing)
        self.assertIs(self.data.projects[1], imported)
        self.assertEqual([color.hex for color in imported.colors], ["#101014", "#0a84ff"])
        self.assertNotEqual(imported.colors[0].id, self.colors()[0].id)

    def test_duplicate_names_get_numbered_copies(self) -> None:
        for _ in range(3):
            project_from_palette(
                self.data, self.directory / "test-theme.json", self.colors()
            )
        self.assertEqual(
            [project.name for project in self.data.projects],
            ["Test Theme", "Test Theme (2)", "Test Theme (3)"],
        )

    def test_unique_project_name_ignores_case(self) -> None:
        self.data.projects.append(Project(name="Theme"))
        self.assertEqual(unique_project_name(self.data, "theme"), "theme (2)")


if __name__ == "__main__":
    unittest.main()
