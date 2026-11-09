from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vcolor.models import ColorEntry, Project
from vcolor.palette_format import (
    FORMAT,
    PALETTE_SCHEMA,
    PortablePalette,
    load_palette,
    save_palette,
)


class PortablePaletteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _palette(self) -> PortablePalette:
        return PortablePalette(
            id="test-theme",
            name="Test Theme",
            description="A test palette.",
            source="https://example.com/test-theme",
            license="MIT",
            tags=["dark", "test"],
            colors=[
                ColorEntry(name="base", hex="#101014"),
                ColorEntry(name="accent", hex="#0a84ff"),
            ],
        )

    def test_round_trip_preserves_metadata(self) -> None:
        path = save_palette(self._palette(), self.directory / "test-theme.json")
        restored = load_palette(path)
        self.assertEqual(restored.id, "test-theme")
        self.assertEqual(restored.name, "Test Theme")
        self.assertEqual(restored.description, "A test palette.")
        self.assertEqual(restored.source, "https://example.com/test-theme")
        self.assertEqual(restored.license, "MIT")
        self.assertEqual(restored.tags, ["dark", "test"])
        self.assertEqual([color.hex for color in restored.colors], ["#101014", "#0a84ff"])

    def test_saved_document_has_canonical_fields(self) -> None:
        path = save_palette(self._palette(), self.directory / "test-theme.json")
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(raw["format"], FORMAT)
        self.assertEqual(raw["version"], 1)
        self.assertEqual(raw["colors"][0], {"name": "base", "hex": "#101014"})

    def test_document_without_format_is_readable(self) -> None:
        path = self.directory / "legacy.json"
        path.write_text(
            json.dumps({"name": "Legacy", "colors": [{"name": "Blue", "hex": "#123"}]}),
            encoding="utf-8",
        )
        palette = load_palette(path)
        self.assertEqual(palette.id, "legacy")
        self.assertEqual(palette.colors[0].hex, "#112233")

    def test_mapping_colors_are_accepted(self) -> None:
        path = self.directory / "mapping.json"
        path.write_text(
            json.dumps({"name": "Mapping", "colors": {"Base": "#ABCDEF"}}),
            encoding="utf-8",
        )
        palette = load_palette(path)
        self.assertEqual(palette.colors[0].name, "Base")
        self.assertEqual(palette.colors[0].hex, "#abcdef")

    def test_string_colors_get_generated_names(self) -> None:
        path = self.directory / "strings.json"
        path.write_text(
            json.dumps({"name": "Strings", "colors": ["#fff", "#000000"]}),
            encoding="utf-8",
        )
        palette = load_palette(path)
        self.assertEqual([color.name for color in palette.colors], ["Color 1", "Color 2"])

    def test_invalid_colors_are_skipped(self) -> None:
        path = self.directory / "mixed.json"
        path.write_text(
            json.dumps(
                {
                    "name": "Mixed",
                    "colors": ["#fff", "not-a-color", {"name": "Bad", "hex": "nope"}],
                }
            ),
            encoding="utf-8",
        )
        palette = load_palette(path)
        self.assertEqual([color.hex for color in palette.colors], ["#ffffff"])

    def test_missing_name_is_rejected(self) -> None:
        path = self.directory / "nameless.json"
        path.write_text(json.dumps({"colors": ["#fff"]}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing a name"):
            load_palette(path)

    def test_no_valid_colors_is_rejected(self) -> None:
        path = self.directory / "empty.json"
        path.write_text(
            json.dumps({"name": "Empty", "colors": ["nope"]}), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "no valid colors"):
            load_palette(path)

    def test_unsupported_vcolor_format_is_rejected(self) -> None:
        path = self.directory / "future.json"
        path.write_text(
            json.dumps(
                {
                    "format": "vcolor.palette.v99",
                    "name": "Future",
                    "colors": ["#fff"],
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "Unsupported palette format"):
            load_palette(path)

    def test_from_project_and_back(self) -> None:
        project = Project(
            name="Brand Colors",
            colors=[ColorEntry(name="Ink", hex="#123123")],
        )
        palette = PortablePalette.from_project(project)
        self.assertEqual(palette.id, "brand-colors")
        restored = palette.to_project()
        self.assertEqual(restored.name, "Brand Colors")
        self.assertEqual(restored.colors[0].name, "Ink")
        self.assertEqual(restored.colors[0].hex, "#123123")

    def test_save_creates_parent_directories(self) -> None:
        path = save_palette(
            self._palette(), self.directory / "nested" / "deeper" / "theme.json"
        )
        self.assertTrue(path.is_file())

    def test_schema_describes_the_format(self) -> None:
        self.assertEqual(PALETTE_SCHEMA["required"], ["name", "colors"])
        self.assertEqual(PALETTE_SCHEMA["properties"]["format"]["const"], FORMAT)
        self.assertIn("color", PALETTE_SCHEMA["$defs"])


if __name__ == "__main__":
    unittest.main()
