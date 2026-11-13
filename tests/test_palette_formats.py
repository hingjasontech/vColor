from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from vcolor.color_utils import hex_to_rgb, rgb_to_cmyk, rgb_to_lab
from vcolor.models import ColorEntry, Project
from vcolor.palette_formats import (
    DEFAULT_EXPORT_FORMAT,
    EXPORT_FORMATS,
    IMPORT_FILTER,
    export_filter_string,
    export_format_for_filter,
    export_format_for_suffix,
    export_palette,
    import_palette,
    import_palette_bytes,
    is_supported_palette_file,
    resolve_export_target,
)


def _ase_name(name: str) -> bytes:
    encoded = name.encode("utf-16-be")
    return struct.pack(">H", len(encoded) // 2 + 1) + encoded + b"\x00\x00"


def _ase_file(entries: list[tuple[str, bytes, tuple[float, ...]]]) -> bytes:
    blocks: list[bytes] = []
    for name, model, values in entries:
        payload = (
            _ase_name(name)
            + model
            + struct.pack(">" + "f" * len(values), *values)
            + struct.pack(">H", 2)
        )
        blocks.append(struct.pack(">HI", 0x0001, len(payload)) + payload)
    return (
        b"ASEF"
        + struct.pack(">HHI", 1, 0, len(blocks))
        + b"".join(blocks)
    )


class PaletteFormatTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.project = Project(
            name="Ocean",
            colors=[
                ColorEntry(name="Ocean Blue", hex="#0a84ff"),
                ColorEntry(name="Ink", hex="#123123"),
            ],
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, name: str, text: str) -> Path:
        path = self.directory / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_every_export_format_round_trips(self) -> None:
        named = {
            fmt.id
            for fmt in EXPORT_FORMATS
            if fmt.id not in {"csv", "coolors"}
        }
        for fmt in EXPORT_FORMATS:
            with self.subTest(fmt=fmt.id):
                path = self.directory / f"ocean-{fmt.id}{fmt.suffix}"
                export_palette(self.project, path, fmt.id)
                colors = import_palette(path)
                self.assertEqual(
                    [color.hex for color in colors], ["#0a84ff", "#123123"]
                )
                if fmt.id in named:
                    self.assertEqual(
                        [color.name for color in colors], ["Ocean Blue", "Ink"]
                    )

    def test_json_export_uses_name_hex_array(self) -> None:
        path = self.directory / "ocean.json"
        export_palette(self.project, path, "json")
        self.assertEqual(
            json.loads(path.read_text(encoding="utf-8")),
            [
                {"name": "Ocean Blue", "hex": "#0a84ff"},
                {"name": "Ink", "hex": "#123123"},
            ],
        )

    def test_json_import_accepts_common_shapes(self) -> None:
        payloads = {
            "array.json": [{"name": "Blue", "hex": "#0a84ff"}],
            "strings.json": ["#0a84ff"],
            "mapping.json": {"Blue": "#0a84ff"},
            "wrapped.json": {"colors": {"Blue": "#0a84ff"}},
            "extended.json": [
                {"name": "Blue", "hex": "#0a84ff", "description": "ignored"}
            ],
            "generic.json": {"entries": [{"value": "rgb(10, 132, 255)"}]},
        }
        for name, payload in payloads.items():
            with self.subTest(name=name):
                path = self.write(name, json.dumps(payload))
                colors = import_palette(path)
                self.assertEqual(colors[0].hex, "#0a84ff")

    def test_legacy_vcolor_json_is_rejected(self) -> None:
        path = self.write(
            "legacy.json",
            json.dumps(
                {
                    "format": "vcolor.palette",
                    "name": "Legacy",
                    "colors": ["#0a84ff"],
                }
            ),
        )
        with self.assertRaisesRegex(ValueError, "no longer supported"):
            import_palette(path)

    def test_css_variables_use_names_and_scan_extra_colors(self) -> None:
        path = self.write(
            "theme.css",
            """
            /* Brand colors */
            :root {
              --ocean-blue: #0a84ff;
              --ink: rgb(18 49 35);
            }
            body { background: #ffffff; }
            """,
        )
        colors = import_palette(path)
        self.assertEqual(
            [(color.name, color.hex) for color in colors],
            [
                ("Ocean Blue", "#0a84ff"),
                ("Ink", "#123123"),
                ("Color 3", "#ffffff"),
            ],
        )

    def test_scss_variables_and_defaults(self) -> None:
        path = self.write(
            "theme.scss",
            """
            // Brand colors
            $ocean-blue: #0a84ff !default;
            $ink: hsl(120, 100%, 10%);
            """,
        )
        colors = import_palette(path)
        self.assertEqual(
            [(color.name, color.hex) for color in colors],
            [("Ocean Blue", "#0a84ff"), ("Ink", "#003300")],
        )

    def test_csv_accepts_bare_coolors_hex_and_named_rows(self) -> None:
        bare = self.write("coolors.csv", "0a84ff,123123,abc")
        self.assertEqual(
            [color.hex for color in import_palette(bare)],
            ["#0a84ff", "#123123", "#aabbcc"],
        )

        named = self.write(
            "named.csv",
            "name,hex\nOcean Blue,0a84ff\nInk,#123123\n",
        )
        self.assertEqual(
            [(color.name, color.hex) for color in import_palette(named)],
            [("Ocean Blue", "#0a84ff"), ("Ink", "#123123")],
        )

    def test_text_import_accepts_hex_and_labels(self) -> None:
        path = self.write(
            "theme.txt",
            """
            # A comment
            #0a84ff\tOcean Blue
            123123
            0a84ff
            """,
        )
        colors = import_palette(path)
        self.assertEqual(
            [(color.name, color.hex) for color in colors],
            [("Ocean Blue", "#0a84ff"), ("Color 2", "#123123")],
        )

    def test_text_import_ignores_prose_that_looks_like_hex(self) -> None:
        path = self.write("notes.txt", "add a color to the palette\n")
        with self.assertRaises(ValueError):
            import_palette(path)

    def test_xml_import_accepts_child_names_and_text_colors(self) -> None:
        path = self.write(
            "theme.xml",
            """
            <palette>
              <color><name>Ocean Blue</name>#0a84ff</color>
              <color r="18" g="49" b="35"><name>Ink</name></color>
            </palette>
            """,
        )
        self.assertEqual(
            [(color.name, color.hex) for color in import_palette(path)],
            [("Ocean Blue", "#0a84ff"), ("Ink", "#123123")],
        )

    def test_xml_import(self) -> None:
        path = self.write(
            "theme.xml",
            """
            <palette>
              <color name="Ocean Blue" hex="#0a84ff" />
              <color name="Ink" r="18" g="49" b="35" />
            </palette>
            """,
        )
        self.assertEqual(
            [(color.name, color.hex) for color in import_palette(path)],
            [("Ocean Blue", "#0a84ff"), ("Ink", "#123123")],
        )

    def test_svg_import_ignores_text_fill(self) -> None:
        path = self.write(
            "swatches.svg",
            """
            <svg xmlns="http://www.w3.org/2000/svg">
              <rect fill="#0a84ff" data-name="Ocean Blue" />
              <text fill="#ffffff">Ocean Blue</text>
            </svg>
            """,
        )
        self.assertEqual(
            [(color.name, color.hex) for color in import_palette(path)],
            [("Ocean Blue", "#0a84ff")],
        )

    def test_ase_import_supports_rgb_cmyk_lab_and_gray(self) -> None:
        blue = hex_to_rgb("#0a84ff")
        ink = rgb_to_cmyk(hex_to_rgb("#123123"))
        lab = rgb_to_lab(hex_to_rgb("#0a84ff"))
        data = _ase_file(
            [
                ("Blue", b"RGB ", (blue.r / 255.0, blue.g / 255.0, blue.b / 255.0)),
                ("Ink", b"CMYK", (ink.c, ink.m, ink.y, ink.k)),
                ("Lab Blue", b"LAB ", (lab.l, lab.a, lab.b)),
                ("Gray", b"Gray", (0.5,)),
            ]
        )
        colors = import_palette_bytes(data, self.directory / "swatches.ase")
        self.assertEqual([color.name for color in colors], ["Blue", "Ink", "Lab Blue", "Gray"])
        self.assertEqual(colors[0].hex, "#0a84ff")
        self.assertEqual(colors[1].hex, "#123123")
        for actual, expected in zip(
            hex_to_rgb(colors[2].hex).as_tuple(),
            hex_to_rgb("#0a84ff").as_tuple(),
            strict=True,
        ):
            self.assertLessEqual(abs(actual - expected), 2)
        self.assertEqual(colors[3].hex, "#808080")

    def test_truncated_ase_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            import_palette_bytes(b"ASEF", self.directory / "broken.ase")

    def test_tailwind_config_import_flattens_shades(self) -> None:
        path = self.write(
            "tailwind.config.js",
            """
            /** @type {import('tailwindcss').Config} */
            module.exports = {
              theme: {
                extend: {
                  colors: {
                    ocean: { 500: "#0a84ff", DEFAULT: "#123123" },
                    ink: "#123123",
                  },
                },
              },
            };
            """,
        )
        colors = import_palette(path)
        self.assertEqual(
            [(color.name, color.hex) for color in colors],
            [
                ("Ocean 500", "#0a84ff"),
                ("Ocean Default", "#123123"),
                ("Ink", "#123123"),
            ],
        )

    def test_gpl_import(self) -> None:
        path = self.write(
            "theme.gpl",
            """
            GIMP Palette
            Name: Ocean
            Columns: 2
            #
              10 132 255\tOcean Blue
              18  49  35\tInk
            """,
        )
        self.assertEqual(
            [(color.name, color.hex) for color in import_palette(path)],
            [("Ocean Blue", "#0a84ff"), ("Ink", "#123123")],
        )

    def test_coolors_link_import(self) -> None:
        path = self.write(
            "palette.txt", "https://coolors.co/0a84ff-123123-abc\n"
        )
        self.assertEqual(
            [color.hex for color in import_palette(path)],
            ["#0a84ff", "#123123", "#aabbcc"],
        )

    def test_empty_and_invalid_files_are_rejected(self) -> None:
        for name, text in {
            "empty.css": "no colors here",
            "empty.txt": "",
            "invalid.json": "{not json",
            "scalar.json": "42",
        }.items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    import_palette(self.write(name, text))

    def test_export_creates_parent_directories(self) -> None:
        path = self.directory / "nested" / "deeper" / "theme.json"
        export_palette(self.project, path, "json")
        self.assertTrue(path.is_file())

    def test_unsupported_export_format_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported export format"):
            export_palette(self.project, self.directory / "theme.pdf", "pdf")

    def test_export_filters_and_suffix_lookup(self) -> None:
        filters = export_filter_string().split(";;")
        self.assertEqual(len(filters), len(EXPORT_FORMATS))
        self.assertIn("JSON palette (*.json)", filters)
        self.assertEqual(DEFAULT_EXPORT_FORMAT.id, "json")
        self.assertEqual(export_format_for_filter("CSS variables (*.css)").id, "css")
        self.assertEqual(export_format_for_suffix(".ase").id, "ase")
        self.assertEqual(export_format_for_suffix(".js").id, "tailwind")
        self.assertEqual(export_format_for_suffix(".txt").id, "txt")
        self.assertIsNone(export_format_for_suffix(".png"))

    def test_resolve_export_target(self) -> None:
        path, fmt = resolve_export_target(
            self.directory / "brand", "CSS variables (*.css)"
        )
        self.assertEqual(path.suffix, ".css")
        self.assertEqual(fmt.id, "css")

        path, fmt = resolve_export_target(
            self.directory / "brand.ase", "JSON palette (*.json)"
        )
        self.assertEqual(path.suffix, ".ase")
        self.assertEqual(fmt.id, "ase")

        path, fmt = resolve_export_target(
            self.directory / "brand.txt", "Coolors link (*.txt)"
        )
        self.assertEqual(fmt.id, "coolors")

        path, fmt = resolve_export_target(
            self.directory / "brand.txt", "Hex list (*.txt)"
        )
        self.assertEqual(fmt.id, "txt")

        path, fmt = resolve_export_target(
            self.directory / "brand.unknown", "JSON palette (*.json)"
        )
        self.assertEqual(path.name, "brand.unknown.json")
        self.assertEqual(fmt.id, "json")

    def test_supported_import_files(self) -> None:
        for suffix in (".json", ".css", ".scss", ".txt", ".csv", ".xml", ".svg", ".ase", ".js"):
            with self.subTest(suffix=suffix):
                self.assertTrue(is_supported_palette_file(Path(f"theme{suffix}")))
        self.assertFalse(is_supported_palette_file(Path("theme.png")))
        self.assertIn("*.ase", IMPORT_FILTER)
        self.assertIn("*.coolors", IMPORT_FILTER)


if __name__ == "__main__":
    unittest.main()
