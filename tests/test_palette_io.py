from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vcolor.models import ColorEntry, Project
from vcolor.palette_io import export_palette, import_palette


class PaletteIoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.project = Project(
            name="Brand colors",
            colors=[
                ColorEntry(name="Ocean blue", hex="#0a84ff"),
                ColorEntry(name="Ink", hex="#123123"),
            ],
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_json_export_import(self) -> None:
        path = self.directory / "brand.json"
        export_palette(self.project, path, "json")
        colors = import_palette(path)
        self.assertEqual([color.name for color in colors], ["Ocean blue", "Ink"])
        self.assertEqual(colors[0].hex, "#0a84ff")

    def test_css_export_import(self) -> None:
        path = self.directory / "brand.css"
        export_palette(self.project, path, "css")
        text = path.read_text(encoding="utf-8")
        self.assertIn("--ocean-blue: #0a84ff;", text)
        colors = import_palette(path)
        self.assertEqual(colors[0].name, "Ocean Blue")
        self.assertEqual(colors[0].hex, "#0a84ff")

    def test_gpl_export_import(self) -> None:
        path = self.directory / "brand.gpl"
        export_palette(self.project, path, "gpl")
        colors = import_palette(path)
        self.assertEqual(colors[1].name, "Ink")
        self.assertEqual(colors[1].hex, "#123123")

    def test_imports_plain_hex_list(self) -> None:
        path = self.directory / "colors.css"
        path.write_text("a { color: #fff; background: #0A84FF; }", encoding="utf-8")
        colors = import_palette(path)
        self.assertEqual({color.hex for color in colors}, {"#ffffff", "#0a84ff"})

    def test_imports_json_string_list(self) -> None:
        path = self.directory / "colors.json"
        path.write_text(json.dumps(["#abc", "#123456"]), encoding="utf-8")
        colors = import_palette(path)
        self.assertEqual([color.hex for color in colors], ["#aabbcc", "#123456"])

    def test_empty_file_raises(self) -> None:
        path = self.directory / "empty.css"
        path.write_text("no colors here", encoding="utf-8")
        with self.assertRaises(ValueError):
            import_palette(path)


if __name__ == "__main__":
    unittest.main()
